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
from app.services.sri_catalogs import (
    calcular_totales_linea,
    es_forma_pago_valida,
    normalizar_forma_pago,
)
from core.database import transaction
from core.logger import get_logger

logger = get_logger("InvoiceController")

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
                       fecha: str = None, send_email: bool = True, propina: float = 0.0):
        """Procesa una nueva venta en el Punto de Venta (POS):
        - Valida stock y datos.
        - Genera Secuencial y Clave de Acceso SRI.
        - Calcula Subtotales, IVA, ICE, Descuentos, Propina y Total.
        - Descuenta stock de productos.
        - Crea archivo XML del SRI.
        - Genera RIDE PDF.
        - Programa el envío por correo para cuando el SRI autorice.
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

        forma_pago = normalizar_forma_pago(forma_pago)
        if not es_forma_pago_valida(forma_pago):
            forma_pago = "EFECTIVO"

        try:
            propina_val = round(float(propina or 0), 2)
        except (TypeError, ValueError):
            return False, "La propina debe ser un valor numérico."
        if propina_val < 0:
            return False, "La propina no puede ser negativa."

        subtotal_15 = 0.0
        subtotal_0 = 0.0
        subtotal_sin_impuestos = 0.0
        total_descuento = 0.0
        iva_total = 0.0
        ice_total = 0.0
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

            try:
                line = calcular_totales_linea(
                    cantidad,
                    precio_unitario,
                    descuento,
                    iva_p,
                    item.get("ice_codigo", ""),
                    item.get("ice_porcentaje", 0.0),
                )
            except ValueError as exc:
                return False, f"ICE de '{descripcion}': {exc}"

            # If product, verify and deduct stock
            if tipo == "producto" and item_id:
                prod = ProductModel.find(item_id)
                if prod:
                    current_stock = int(prod.get("stock", 0))
                    if current_stock < int(cantidad):
                        return False, f"Stock insuficiente para '{descripcion}'. Disponible: {current_stock}, Solicitado: {cantidad}"

            subtotal_item = line["subtotal"]
            valor_iva = line["valor_iva"]
            valor_ice = line["valor_ice"]

            subtotal_sin_impuestos += subtotal_item
            total_descuento += descuento
            iva_total += valor_iva
            ice_total += valor_ice

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
                "ice_codigo": line["ice_codigo"],
                "ice_porcentaje": line["ice_porcentaje"],
                "valor_ice": valor_ice,
                "total": line["total"]
            })

        importe_total = subtotal_sin_impuestos + iva_total + ice_total + propina_val

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
            "ice_total": ice_total,
            "propina": propina_val,
            "importe_total": importe_total,
            "forma_pago": forma_pago
        }

        # 1. Generate XML
        xml_path, xml_content, clave_acceso = XMLService.create_factura_xml(company, invoice_data, processed_items)
        invoice_data["clave_acceso"] = clave_acceso

        # 2. Generate PDF RIDE
        pdf_path = PDFService.generate_factura_pdf(company, invoice_data, processed_items, clave_acceso)

        # 3. El correo se envía cuando el SRI autoriza el comprobante. Así el
        # cliente recibe el RIDE definitivo (con número y fecha de autorización)
        # y no un documento marcado como pendiente.
        if send_email:
            email_estado = "PENDIENTE"
            email_msg = "Se enviará automáticamente cuando el SRI autorice la factura."
        else:
            email_estado = "NO_ENVIAR"
            email_msg = "Envío por correo desactivado."

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
                ice_total=ice_total,
                propina=propina_val,
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
                    ice_codigo=pit["ice_codigo"],
                    ice_porcentaje=pit["ice_porcentaje"],
                    valor_ice=pit["valor_ice"],
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
    def _invoice_data_from_record(cls, inv: dict) -> dict:
        """Reconstruye el diccionario que usan XMLService y PDFService."""
        identificacion = str(inv.get("client_identificacion") or "")
        return {
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
            "ice_total": float(inv.get("ice_total") or 0),
            "propina": float(inv.get("propina") or 0),
            "importe_total": float(inv.get("importe_total") or 0),
            "forma_pago": inv.get("forma_pago", "EFECTIVO"),
            "numero_autorizacion": inv.get("sri_autorizacion", ""),
            "fecha_autorizacion": inv.get("sri_fecha_autorizacion", ""),
        }

    @classmethod
    def _items_from_record(cls, inv: dict) -> list:
        return [
            {
                "codigo": item.get("codigo", ""),
                "descripcion": item.get("descripcion", ""),
                "cantidad": float(item.get("cantidad") or 1),
                "precio_unitario": float(item.get("precio_unitario") or 0),
                "descuento": float(item.get("descuento") or 0),
                "subtotal": float(item.get("subtotal") or 0),
                "iva_porcentaje": float(item.get("iva_porcentaje") or 0),
                "valor_iva": float(item.get("valor_iva") or 0),
                "ice_codigo": str(item.get("ice_codigo") or ""),
                "ice_porcentaje": float(item.get("ice_porcentaje") or 0),
                "valor_ice": float(item.get("valor_ice") or 0),
                "total": float(item.get("total") or 0),
            }
            for item in (inv.get("items") or [])
        ]

    @classmethod
    def _ensure_invoice_xml(cls, inv: dict, company: dict) -> tuple[bool, str]:
        """Devuelve el XML de la factura; lo regenera si el archivo no existe."""
        xml_path = str(inv.get("xml_path") or "").strip()
        if xml_path and os.path.isfile(xml_path):
            return True, xml_path

        items = inv.get("items") or []
        if not items:
            return False, "La factura no tiene ítems para regenerar el XML."

        invoice_data = cls._invoice_data_from_record(inv)
        processed_items = cls._items_from_record(inv)

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
    def _regenerate_invoice_pdf(
        cls,
        inv: dict,
        company: dict,
        autorizacion: dict | None = None,
    ) -> str:
        """Regenera el RIDE con los datos de autorización del SRI.

        Un RIDE solo debe mostrar número y fecha de autorización cuando el
        comprobante ya fue autorizado; por eso se regenera al recibir la
        respuesta del SRI. Un fallo aquí no debe romper el flujo de envío.
        """
        items = cls._items_from_record(inv)
        if not items:
            return ""

        invoice_data = cls._invoice_data_from_record(inv)
        clave_acceso = str(inv.get("clave_acceso") or "")
        if not clave_acceso:
            return ""

        try:
            pdf_path = PDFService.generate_factura_pdf(
                company,
                invoice_data,
                items,
                clave_acceso,
                autorizacion=autorizacion,
            )
        except Exception:  # noqa: BLE001
            logger.exception(
                "No se pudo regenerar el RIDE de la factura %s",
                inv.get("secuencial"),
            )
            return ""

        InvoiceModel.update_by_id(inv["id"], pdf_path=pdf_path)
        return pdf_path

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

        # El RIDE definitivo debe incluir número y fecha de autorización.
        if (result.get("estado") or "").upper() == "AUTORIZADO":
            if result.get("clave_acceso"):
                inv = dict(inv, clave_acceso=result["clave_acceso"])
            pdf_path = cls._regenerate_invoice_pdf(inv, company, result)
            if pdf_path:
                result["pdf_path"] = pdf_path

            # Enviar el correo con el RIDE y el XML autorizados. Si el usuario
            # desactivó el envío, se respeta esa decisión.
            updated_inv = cls.get_by_id(invoice_id)
            if updated_inv:
                email_estado = str(updated_inv.get("email_estado") or "").upper()
                if email_estado not in ("NO_ENVIAR", "ENVIADA"):
                    email_data = cls._invoice_data_from_record(updated_inv)
                    email_xml = (
                        result.get("xml_autorizado_path")
                        or result.get("xml_firmado_path")
                        or xml_or_error
                    )
                    email_pdf = pdf_path or updated_inv.get("pdf_path") or ""
                    email_sent, email_msg = EmailService.send_invoice_email(
                        company, email_data, email_xml, email_pdf
                    )
                    InvoiceModel.update_by_id(
                        invoice_id,
                        email_estado="ENVIADA" if email_sent else "ERROR",
                    )
                    result["email_status"] = email_msg
                elif email_estado == "ENVIADA":
                    result["email_status"] = "La factura ya había sido enviada por correo."
                else:
                    result["email_status"] = "Envío por correo desactivado."

        return True, result

    @classmethod
    def resend_email(cls, invoice_id: int):
        """Re-envía el PDF y XML de la factura por correo.

        Si la factura ya fue autorizada, usa el XML autorizado y regenera el
        RIDE para que el cliente reciba el número y la fecha de autorización.
        """
        inv = cls.get_by_id(invoice_id)
        if not inv:
            return False, "Factura no encontrada."

        company = CompanyController.get_info()
        if not company:
            return False, "No se encontró la configuración de la empresa."

        invoice_data = cls._invoice_data_from_record(inv)
        clave_acceso = str(inv.get("clave_acceso") or "")
        xml_path = str(inv.get("xml_path") or "")

        # El XML autorizado es el que debe recibir el cliente.
        if xml_path and clave_acceso:
            autorizado_path = os.path.join(
                os.path.dirname(xml_path),
                f"FAC_{clave_acceso}_autorizado.xml",
            )
            if os.path.isfile(autorizado_path):
                xml_path = autorizado_path

        pdf_path = str(inv.get("pdf_path") or "")
        autorizacion = None
        if inv.get("sri_autorizacion") or inv.get("sri_fecha_autorizacion"):
            autorizacion = {
                "estado": "AUTORIZADO",
                "numero": inv.get("sri_autorizacion") or "",
                "fecha": inv.get("sri_fecha_autorizacion") or "",
            }

        regenerated = cls._regenerate_invoice_pdf(inv, company, autorizacion)
        if regenerated:
            pdf_path = regenerated

        success, msg = EmailService.send_invoice_email(
            company, invoice_data, xml_path, pdf_path
        )
        if success:
            InvoiceModel.update_by_id(invoice_id, email_estado="ENVIADA")
        return success, msg
