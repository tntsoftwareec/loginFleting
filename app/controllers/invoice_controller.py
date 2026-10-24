import os
from datetime import datetime
from app.controllers.company_controller import CompanyController
from app.controllers.inventory_controller import InventoryController
from app.models.invoice_model import InvoiceModel, InvoiceItemModel
from app.models.company_model import CompanyModel
from app.models.client_model import ClientModel
from app.models.product_model import ProductModel
from app.services.xml_service import XMLService
from app.services.pdf_service import PDFService
from app.services.email_service import EmailService
from app.services.sri_service import SRIService
from core.database import transaction

class InvoiceController:
    @classmethod
    def get_all(cls):
        """Retorna todas las facturas emitidas con información del cliente."""
        return InvoiceModel.all()

    @classmethod
    def get_by_id(cls, invoice_id: int):
        """Retorna una factura con sus detalles."""
        inv = InvoiceModel.with_("items").find(invoice_id)
        return inv

    @classmethod
    def create_invoice(cls, client_id: int, cart_items: list, forma_pago: str = "EFECTIVO",
                       fecha: str = None, send_email: bool = True):
        """Procesa una nueva venta en el Punto de Venta (POS):
        - Valida stock y datos.
        - Genera Secuencial y Clave de Acceso SRI.
        - Calcula Subtotales, IVA 15%, Descuentos y Total.
        - Descuenta stock de productos.
        - Crea archivo XML del SRI.
        - Genera RIDE PDF.
        - Envía por correo electrónico en PDF/XML al SRI y cliente.
        - Registra la factura y detalles en la base de datos.
        
        Returns:
            (success: bool, data_or_error: dict|str)
        """
        if not cart_items:
            return False, "El carrito de compras está vacío. Agregue al menos un producto o servicio."

        # Datos con smtp_pass descifrado para el envío por correo.
        company = CompanyController.get_info()
        client = ClientModel.find(client_id) if client_id else None

        if not client:
            # Fallback to Consumidor Final
            cf = ClientModel.where(identificacion="9999999999999")
            if cf:
                client = cf[0]
            else:
                client = {
                    "id": None,
                    "tipo_documento": "CONSUMIDOR_FINAL",
                    "identificacion": "9999999999999",
                    "razon_social": "CONSUMIDOR FINAL",
                    "email": "consumidor@mail.com",
                    "direccion": "Ciudad"
                }

        # Format Secuencial
        sec_num = int(company.get("secuencial_factura", 1))
        estab = str(company.get("establecimiento", "001")).zfill(3)
        pto_emi = str(company.get("punto_emision", "001")).zfill(3)
        secuencial_str = f"{estab}-{pto_emi}-{str(sec_num).zfill(9)}"

        fecha_emision = fecha or datetime.now().strftime("%Y-%m-%d")

        subtotal_15 = 0.0
        subtotal_0 = 0.0
        subtotal_sin_impuestos = 0.0
        total_descuento = 0.0
        iva_total = 0.0
        importe_total = 0.0

        processed_items = []

        # Validate stock and compute item totals
        for item in cart_items:
            tipo = item.get("tipo", "producto")
            item_id = item.get("id")
            codigo = item.get("codigo", "P-001")
            descripcion = item.get("nombre", "Item")
            cantidad = float(item.get("cantidad", 1))
            precio_unitario = float(item.get("precio", 0.0))
            descuento = float(item.get("descuento", 0.0))
            iva_p = float(item.get("iva_porcentaje", 15.0))

            if cantidad <= 0:
                return False, f"La cantidad para '{descripcion}' debe ser mayor a cero."

            # If product, verify and deduct stock
            if tipo == "producto" and item_id:
                prod = ProductModel.find(item_id)
                if prod:
                    current_stock = int(prod.get("stock", 0))
                    if current_stock < int(cantidad):
                        return False, f"Stock insuficiente para '{descripcion}'. Disponible: {current_stock}, Solicitado: {cantidad}"

            subtotal_item = (cantidad * precio_unitario) - descuento
            if subtotal_item < 0:
                subtotal_item = 0.0

            valor_iva = (subtotal_item * (iva_p / 100.0)) if iva_p > 0 else 0.0
            total_item = subtotal_item + valor_iva

            subtotal_sin_impuestos += subtotal_item
            total_descuento += descuento
            iva_total += valor_iva

            if iva_p > 0:
                subtotal_15 += subtotal_item
            else:
                subtotal_0 += subtotal_item

            processed_items.append({
                "tipo": tipo,
                "item_id": item_id,
                "codigo": codigo,
                "descripcion": descripcion,
                "cantidad": cantidad,
                "precio_unitario": precio_unitario,
                "descuento": descuento,
                "subtotal": subtotal_item,
                "iva_porcentaje": iva_p,
                "valor_iva": valor_iva,
                "total": total_item
            })

        importe_total = subtotal_sin_impuestos + iva_total

        invoice_data = {
            "secuencial": secuencial_str,
            "client_tipo_doc": client.get("tipo_documento", "CEDULA"),
            "client_nombre": client.get("razon_social", "CONSUMIDOR FINAL"),
            "client_identificacion": client.get("identificacion", "9999999999999"),
            "client_email": client.get("email", "consumidor@mail.com"),
            "client_direccion": client.get("direccion", "Ciudad"),
            "fecha_emision": fecha_emision,
            "subtotal_15": subtotal_15,
            "subtotal_0": subtotal_0,
            "subtotal_sin_impuestos": subtotal_sin_impuestos,
            "total_descuento": total_descuento,
            "iva_total": iva_total,
            "importe_total": importe_total,
            "forma_pago": forma_pago
        }

        # 1. Generate XML
        xml_path, xml_content, clave_acceso = XMLService.create_factura_xml(company, invoice_data, processed_items)
        invoice_data["clave_acceso"] = clave_acceso

        # 2. Generate PDF RIDE
        pdf_path = PDFService.generate_factura_pdf(company, invoice_data, processed_items, clave_acceso)

        # 3. Send Email to SRI and Client
        if send_email:
            email_sent, email_msg = EmailService.send_invoice_email(company, invoice_data, xml_path, pdf_path)
            email_estado = "ENVIADA" if email_sent else "PENDIENTE"
        else:
            email_estado = "PENDIENTE"
            email_msg = "Pendiente de envío"

        # La factura nace GENERADA; el estado electrónico cambia cuando se
        # envía al SRI desde el historial de facturas.
        estado_final = "GENERADA"

        # 4-6. Guardar factura, ítems, stock y secuencial de forma atómica.
        with transaction():
            new_invoice = InvoiceModel.create(
                secuencial=secuencial_str,
                clave_acceso=clave_acceso,
                client_id=client.get("id"),
                client_nombre=client.get("razon_social", "CONSUMIDOR FINAL"),
                client_identificacion=client.get("identificacion", "9999999999999"),
                client_email=client.get("email", "consumidor@mail.com"),
                client_direccion=client.get("direccion", "Ciudad"),
                fecha_emision=fecha_emision,
                subtotal_15=subtotal_15,
                subtotal_0=subtotal_0,
                subtotal_sin_impuestos=subtotal_sin_impuestos,
                total_descuento=total_descuento,
                iva_total=iva_total,
                importe_total=importe_total,
                forma_pago=forma_pago,
                estado=estado_final,
                email_estado=email_estado,
                xml_path=xml_path,
                pdf_path=pdf_path,
                sri_mensaje=""
            )

            inv_id = new_invoice["id"]

            # 5. Save Items & deduct product stock
            for pit in processed_items:
                InvoiceItemModel.create(
                    invoice_id=inv_id,
                    tipo=pit["tipo"],
                    item_id=pit["item_id"],
                    codigo=pit["codigo"],
                    descripcion=pit["descripcion"],
                    cantidad=pit["cantidad"],
                    precio_unitario=pit["precio_unitario"],
                    descuento=pit["descuento"],
                    subtotal=pit["subtotal"],
                    iva_porcentaje=pit["iva_porcentaje"],
                    valor_iva=pit["valor_iva"],
                    total=pit["total"]
                )

                # Descuenta stock y registra el movimiento de inventario.
                if pit["tipo"] == "producto" and pit["item_id"]:
                    success, movement = InventoryController.register_movement(
                        product_id=pit["item_id"],
                        tipo="VENTA",
                        cantidad=int(pit["cantidad"]),
                        motivo=f"Venta según factura {secuencial_str}",
                        referencia=secuencial_str,
                    )
                    if not success:
                        raise ValueError(str(movement))

            # 6. Increment company secuencial
            CompanyModel.update_by_id(company["id"], secuencial_factura=sec_num + 1)

        result_dict = dict(new_invoice)
        result_dict["email_status"] = email_msg
        return True, result_dict

    @classmethod
    def _ensure_invoice_xml(cls, inv: dict, company: dict) -> tuple[bool, str]:
        """Devuelve el XML de la factura; lo regenera si el archivo no existe."""
        xml_path = str(inv.get("xml_path") or "").strip()
        if xml_path and os.path.isfile(xml_path):
            return True, xml_path

        items = inv.get("items") or []
        if not items:
            return False, "La factura no tiene ítems para regenerar el XML."

        identificacion = str(inv.get("client_identificacion") or "")
        invoice_data = {
            "secuencial": inv.get("secuencial"),
            "clave_acceso": inv.get("clave_acceso"),
            "client_tipo_doc": "RUC" if len(identificacion) == 13 else "CEDULA",
            "client_nombre": inv.get("client_nombre", "CONSUMIDOR FINAL"),
            "client_identificacion": inv.get("client_identificacion", "9999999999999"),
            "client_email": inv.get("client_email", ""),
            "client_direccion": inv.get("client_direccion", "Ciudad"),
            "fecha_emision": inv.get("fecha_emision"),
            "subtotal_15": float(inv.get("subtotal_15") or 0),
            "subtotal_0": float(inv.get("subtotal_0") or 0),
            "subtotal_sin_impuestos": float(inv.get("subtotal_sin_impuestos") or 0),
            "total_descuento": float(inv.get("total_descuento") or 0),
            "iva_total": float(inv.get("iva_total") or 0),
            "importe_total": float(inv.get("importe_total") or 0),
            "forma_pago": inv.get("forma_pago", "EFECTIVO"),
        }
        processed_items = []
        for item in items:
            processed_items.append({
                "codigo": item.get("codigo", ""),
                "descripcion": item.get("descripcion", ""),
                "cantidad": float(item.get("cantidad") or 1),
                "precio_unitario": float(item.get("precio_unitario") or 0),
                "descuento": float(item.get("descuento") or 0),
                "subtotal": float(item.get("subtotal") or 0),
                "iva_porcentaje": float(item.get("iva_porcentaje") or 0),
                "valor_iva": float(item.get("valor_iva") or 0),
                "total": float(item.get("total") or 0),
            })

        try:
            xml_path, _content, clave = XMLService.create_factura_xml(
                company, invoice_data, processed_items
            )
        except Exception as exc:  # noqa: BLE001
            return False, f"No se pudo regenerar el XML de la factura: {exc}"

        InvoiceModel.update_by_id(
            inv["id"], xml_path=xml_path, clave_acceso=clave
        )
        return True, xml_path

    @classmethod
    def send_to_sri(cls, invoice_id: int):
        """Firma y envía la factura al SRI; guarda estado y respuesta.

        Returns:
            ``(ok, resultado)``. ``ok`` es ``True`` cuando el SRI respondió
            (aunque el comprobante haya sido devuelto o rechazado).
        """
        inv = cls.get_by_id(invoice_id)
        if not inv:
            return False, "Factura no encontrada."

        company = CompanyController.get_info()
        if not company:
            return False, "No se encontró la configuración de la empresa."

        ok, xml_or_error = cls._ensure_invoice_xml(inv, company)
        if not ok:
            return False, xml_or_error

        try:
            ok, result = SRIService.send_invoice(xml_or_error, company)
        except Exception as exc:  # noqa: BLE001
            ok, result = False, f"Error inesperado al enviar al SRI: {exc}"
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not ok:
            InvoiceModel.update_by_id(
                invoice_id,
                estado="ERROR",
                sri_mensaje=str(result),
                sri_respuesta=str(result),
                sri_fecha_envio=ahora,
            )
            return False, str(result)

        InvoiceModel.update_by_id(
            invoice_id,
            estado=result.get("estado") or "SIN RESPUESTA",
            sri_mensaje=result.get("mensaje") or "",
            sri_respuesta=result.get("respuesta") or "",
            sri_autorizacion=result.get("numero_autorizacion") or "",
            sri_fecha_autorizacion=result.get("fecha_autorizacion") or "",
            sri_fecha_envio=ahora,
            xml_path=result.get("xml_firmado_path") or xml_or_error,
        )
        return True, result

    @classmethod
    def resend_email(cls, invoice_id: int):
        """Re-envía el PDF y XML de la factura por correo."""
        inv = cls.get_by_id(invoice_id)
        if not inv:
            return False, "Factura no encontrada."

        company = CompanyController.get_info()
        invoice_data = {
            "secuencial": inv.get("secuencial"),
            "clave_acceso": inv.get("clave_acceso"),
            "client_nombre": inv.get("client_nombre"),
            "client_email": inv.get("client_email"),
            "fecha_emision": inv.get("fecha_emision"),
            "importe_total": inv.get("importe_total")
        }

        success, msg = EmailService.send_invoice_email(company, invoice_data, inv.get("xml_path"), inv.get("pdf_path"))
        if success:
            InvoiceModel.update_by_id(invoice_id, email_estado="ENVIADA")
        return success, msg
