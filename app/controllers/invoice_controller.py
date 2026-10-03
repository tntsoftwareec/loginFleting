from datetime import datetime
from app.models.invoice_model import InvoiceModel, InvoiceItemModel
from app.models.company_model import CompanyModel
from app.models.client_model import ClientModel
from app.models.product_model import ProductModel
from app.services.xml_service import XMLService
from app.services.pdf_service import PDFService
from app.services.email_service import EmailService

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
    def create_invoice(cls, client_id: int, cart_items: list, forma_pago: str = "EFECTIVO"):
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

        company = CompanyModel.get_info()
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

        fecha_emision = datetime.now().strftime("%Y-%m-%d")

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
        email_sent, email_msg = EmailService.send_invoice_email(company, invoice_data, xml_path, pdf_path)
        estado_final = "ENVIADA" if email_sent else "GENERADA"

        # 4. Save Invoice to Database
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
            xml_path=xml_path,
            pdf_path=pdf_path,
            sri_mensaje=email_msg
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

            # Deduct stock if product
            if pit["tipo"] == "producto" and pit["item_id"]:
                prod = ProductModel.find(pit["item_id"])
                if prod:
                    new_st = max(0, int(prod.get("stock", 0)) - int(pit["cantidad"]))
                    ProductModel.update_by_id(pit["item_id"], stock=new_st)

        # 6. Increment company secuencial
        CompanyModel.update_by_id(company["id"], secuencial_factura=sec_num + 1)

        result_dict = dict(new_invoice)
        result_dict["email_status"] = email_msg
        return True, result_dict

    @classmethod
    def resend_email(cls, invoice_id: int):
        """Re-envía el PDF y XML de la factura por correo."""
        inv = cls.get_by_id(invoice_id)
        if not inv:
            return False, "Factura no encontrada."

        company = CompanyModel.get_info()
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
            InvoiceModel.update_by_id(invoice_id, estado="ENVIADA", sri_mensaje=msg)
        return success, msg
