import os
from datetime import datetime, timedelta

from app.controllers.company_controller import CompanyController
from app.models.quotation_model import QuotationModel, QuotationItemModel
from app.models.company_model import CompanyModel
from app.models.client_model import ClientModel
from app.models.product_model import ProductModel
from app.services.pdf_service import PDFService
from app.services.email_service import EmailService
from app.services.sri_catalogs import (
    calcular_totales_linea,
    es_forma_pago_valida,
    normalizar_forma_pago,
)
from core.database import transaction
from core.logger import get_logger

logger = get_logger("QuotationController")

class QuotationController:
    @classmethod
    def get_all(cls):
        """Retorna todas las cotizaciones."""
        return QuotationModel.all()

    @classmethod
    def get_by_id(cls, quotation_id: int):
        """Retorna una cotización con sus items."""
        return QuotationModel.with_("items").find(quotation_id)

    @classmethod
    def _with_product_images(cls, items: list) -> list:
        """Añade la imagen actual del producto a cada ítem de cotización.

        ``quotation_items`` guarda ``item_id``, pero no la ruta de la imagen.
        Para las cotizaciones nuevas se usa la ruta del carrito y, al
        regenerar un PDF antiguo, se consulta el producto actual.
        """
        enriched = []
        for raw in items or []:
            item = dict(raw)
            item_id = item.get("item_id") or item.get("id")
            code = str(item.get("codigo") or "").strip()
            if item.get("tipo") == "producto" and (item_id or code):
                current_path = str(item.get("imagen_path") or "").strip()
                if not current_path or not os.path.isfile(current_path):
                    product = None
                    if item_id:
                        product = ProductModel.find(item_id)
                    if not product and code:
                        matches = ProductModel.where(codigo=code)
                        if not matches and code.upper() != code:
                            matches = ProductModel.where(codigo=code.upper())
                        product = matches[0] if matches else None
                    if product:
                        item["imagen_path"] = product.get("imagen_path") or ""
            enriched.append(item)
        return enriched

    @classmethod
    def create_quotation(cls, client_id: int, cart_items: list, notas: str = "", dias_validez: int = 15,
                         fecha: str = None):
        """Crea una nueva cotización:
        - Calcula subtotales, IVA 15%, descuentos y total.
        - Genera PDF de cotización.
        - Registra en base de datos.

        Returns:
            (success: bool, data_or_error: dict|str)
        """
        if not cart_items:
            return False, "La lista de ítems está vacía. Agregue al menos un producto o servicio."

        company = CompanyModel.get_info()
        client = ClientModel.find(client_id) if client_id else None

        if not client:
            return False, "Debe seleccionar un cliente válido para generar la cotización."

        # Format Secuencial COT-001-001-000000001
        sec_num = int(company.get("secuencial_cotizacion", 1) or 1)
        estab = str(company.get("establecimiento", "001")).zfill(3)
        pto_emi = str(company.get("punto_emision", "001")).zfill(3)
        secuencial_str = f"COT-{estab}-{pto_emi}-{str(sec_num).zfill(9)}"

        base_date = datetime.strptime(fecha, "%Y-%m-%d") if fecha else datetime.now()
        fecha_emision = base_date.strftime("%Y-%m-%d")
        fecha_validez = (base_date + timedelta(days=dias_validez)).strftime("%Y-%m-%d")

        subtotal_15 = 0.0
        subtotal_0 = 0.0
        subtotal_sin_impuestos = 0.0
        total_descuento = 0.0
        iva_total = 0.0
        ice_total = 0.0

        processed_items = []

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
                "total": line["total"],
                "imagen_path": item.get("imagen_path", "") if tipo == "producto" else "",
            })

        # Incluye la imagen del producto en el PDF de la cotización.
        processed_items = cls._with_product_images(processed_items)

        importe_total = subtotal_sin_impuestos + iva_total + ice_total

        quotation_data = {
            "secuencial": secuencial_str,
            "client_nombre": client.get("razon_social", "CLIENTE"),
            "client_identificacion": client.get("identificacion", ""),
            "client_email": client.get("email", ""),
            "client_direccion": client.get("direccion", "Ciudad"),
            "fecha_emision": fecha_emision,
            "fecha_validez": fecha_validez,
            "subtotal_15": subtotal_15,
            "subtotal_0": subtotal_0,
            "subtotal_sin_impuestos": subtotal_sin_impuestos,
            "total_descuento": total_descuento,
            "iva_total": iva_total,
            "ice_total": ice_total,
            "importe_total": importe_total,
            "notas": notas,
        }

        # 1. Generate PDF
        pdf_path = PDFService.generate_cotizacion_pdf(company, quotation_data, processed_items)

        # 2-4. Guardar cotización, ítems y secuencial de forma atómica.
        with transaction():
            new_quotation = QuotationModel.create(
                secuencial=secuencial_str,
                client_id=client.get("id"),
                client_nombre=client.get("razon_social", "CLIENTE"),
                client_identificacion=client.get("identificacion", ""),
                client_email=client.get("email", ""),
                client_direccion=client.get("direccion", "Ciudad"),
                fecha_emision=fecha_emision,
                fecha_validez=fecha_validez,
                subtotal_15=subtotal_15,
                subtotal_0=subtotal_0,
                subtotal_sin_impuestos=subtotal_sin_impuestos,
                total_descuento=total_descuento,
                iva_total=iva_total,
                ice_total=ice_total,
                importe_total=importe_total,
                estado="EMITIDA",
                pdf_path=pdf_path,
                notas=notas,
            )

            quot_id = new_quotation["id"]

            # 3. Save Items
            for pit in processed_items:
                QuotationItemModel.create(
                    quotation_id=quot_id,
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

            # 4. Increment secuencial
            CompanyModel.update_by_id(company["id"], secuencial_cotizacion=sec_num + 1)

        result_dict = dict(new_quotation)
        return True, result_dict

    @classmethod
    def ensure_quotation_pdf(cls, quotation_id: int, force: bool = False) -> str:
        """Devuelve la ruta del PDF de la cotización, regenerándolo si falta.

        Los PDF viven en el directorio persistente de la app, pero pueden
        borrarse manualmente o perderse al cambiar de equipo. En ese caso se
        vuelve a generar con los datos actuales de la cotización.

        ``force=True`` regenera incluso si el archivo existe; se usa al abrir
        o enviar la cotización para incorporar cambios recientes en las
        imágenes de los productos. Si falla, conserva el PDF anterior.
        """
        quot = cls.get_by_id(quotation_id)
        if not quot:
            return ""

        pdf_path = str(quot.get("pdf_path") or "").strip()
        if pdf_path and os.path.isfile(pdf_path) and not force:
            return pdf_path

        company = CompanyModel.get_info()
        if not company:
            return pdf_path if pdf_path and os.path.isfile(pdf_path) else ""

        try:
            pdf_path = PDFService.generate_cotizacion_pdf(
                company,
                cls._quotation_pdf_data(quot),
                cls._with_product_images(quot.get("items") or []),
            )
            QuotationModel.update_by_id(quotation_id, pdf_path=pdf_path)
            return pdf_path
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "No se pudo regenerar el PDF de la cotización %s: %s",
                quotation_id,
                exc,
            )
            if pdf_path and os.path.isfile(pdf_path):
                return pdf_path
            return ""

    @staticmethod
    def _quotation_pdf_data(quot: dict) -> dict:
        """Datos de la cotización usados para regenerar el PDF."""
        return {
            "secuencial": quot.get("secuencial"),
            "client_nombre": quot.get("client_nombre"),
            "client_identificacion": quot.get("client_identificacion"),
            "client_email": quot.get("client_email"),
            "client_direccion": quot.get("client_direccion", "Ciudad"),
            "fecha_emision": quot.get("fecha_emision"),
            "fecha_validez": quot.get("fecha_validez"),
            "subtotal_15": quot.get("subtotal_15", 0),
            "subtotal_0": quot.get("subtotal_0", 0),
            "subtotal_sin_impuestos": quot.get("subtotal_sin_impuestos", 0),
            "total_descuento": quot.get("total_descuento", 0),
            "iva_total": quot.get("iva_total", 0),
            "ice_total": quot.get("ice_total", 0),
            "importe_total": quot.get("importe_total", 0),
            "notas": quot.get("notas", ""),
        }

    @classmethod
    def send_quotation_email(cls, quotation_id: int):
        """Envía la cotización en PDF por correo al cliente."""
        quot = cls.get_by_id(quotation_id)
        if not quot:
            return False, "Cotización no encontrada."

        pdf_path = cls.ensure_quotation_pdf(quotation_id, force=True)
        if not pdf_path:
            return False, (
                "No se pudo generar el PDF de la cotización. "
                "Verifica que la cotización tenga ítems y vuelve a intentar."
            )

        # CompanyController entrega smtp_pass ya descifrado. Usar el modelo
        # directamente enviaría el token cifrado como contraseña SMTP.
        company = CompanyController.get_info() or {}
        quotation_data = {
            "secuencial": quot.get("secuencial"),
            "client_nombre": quot.get("client_nombre"),
            "client_email": quot.get("client_email"),
            "fecha_emision": quot.get("fecha_emision"),
            "fecha_validez": quot.get("fecha_validez"),
            "importe_total": quot.get("importe_total"),
            "notas": quot.get("notas", ""),
        }

        success, msg = EmailService.send_quotation_email(company, quotation_data, pdf_path)
        if success and (quot.get("estado") or "").upper() != "FACTURADA":
            QuotationModel.update_by_id(quotation_id, estado="ENVIADA")
        return success, msg

    @classmethod
    def invoice_quotation(cls, quotation_id: int, forma_pago: str = "EFECTIVO",
                          send_email: bool = False):
        """Genera una factura a partir de una cotización existente.

        La cotización queda marcada como ``FACTURADA`` y se guarda el vínculo
        con la factura para impedir una segunda facturación accidental.
        """
        quot = cls.get_by_id(quotation_id)
        if not quot:
            return False, "Cotización no encontrada."

        invoice_id = quot.get("invoice_id")
        if invoice_id or (quot.get("estado") or "").upper() == "FACTURADA":
            if invoice_id:
                from app.models.invoice_model import InvoiceModel

                invoice = InvoiceModel.find(int(invoice_id))
                if invoice:
                    return False, (
                        "Esta cotización ya fue facturada con la factura "
                        f"{invoice.get('secuencial')}."
                    )
            return False, "Esta cotización ya fue facturada."

        items = quot.get("items") or []
        if not items:
            return False, "La cotización no tiene ítems para facturar."

        cart_items = []
        for item in items:
            cantidad = float(item.get("cantidad") or 0)
            descripcion = item.get("descripcion") or "Item"
            if cantidad <= 0:
                return False, f"La cantidad de '{descripcion}' debe ser mayor a cero."

            cart_items.append({
                "id": item.get("item_id"),
                "tipo": item.get("tipo") or "producto",
                "codigo": item.get("codigo") or "ITEM",
                "nombre": descripcion,
                "precio": float(item.get("precio_unitario") or 0),
                "cantidad": cantidad,
                "descuento": float(item.get("descuento") or 0),
                "iva_porcentaje": float(item.get("iva_porcentaje") or 0),
                "ice_codigo": str(item.get("ice_codigo") or ""),
                "ice_porcentaje": float(item.get("ice_porcentaje") or 0),
            })

        forma_pago = normalizar_forma_pago(forma_pago)
        if not es_forma_pago_valida(forma_pago):
            forma_pago = "EFECTIVO"

        # Importación local para mantener desacoplados ambos controladores.
        from app.controllers.invoice_controller import InvoiceController

        success, result = InvoiceController.create_invoice(
            client_id=quot.get("client_id"),
            cart_items=cart_items,
            forma_pago=forma_pago,
            send_email=bool(send_email),
        )
        if not success:
            return False, result

        try:
            QuotationModel.update_by_id(
                quotation_id,
                estado="FACTURADA",
                invoice_id=result.get("id"),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "La factura %s se creó, pero no se pudo marcar la cotización %s: %s",
                result.get("secuencial"),
                quotation_id,
                exc,
            )
            result = dict(result)
            result["quotation_warning"] = (
                "La factura se generó, pero no se pudo actualizar el estado de "
                "la cotización."
            )

        return True, result

    @classmethod
    def mark_whatsapp_sent(cls, quotation_id: int):
        """Marca la cotización como enviada por WhatsApp (solo seguimiento)."""
        try:
            QuotationModel.update_by_id(quotation_id, enviada_whatsapp=1)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "No se pudo marcar la cotización %s como enviada por WhatsApp: %s",
                quotation_id,
                exc,
            )
            return False

    @classmethod
    def delete(cls, quotation_id: int):
        """Elimina una cotización y sus ítems."""
        quot = QuotationModel.find(quotation_id)
        if not quot:
            return False, "Cotización no encontrada."
        if quot.get("invoice_id") or (quot.get("estado") or "").upper() == "FACTURADA":
            return False, (
                "No se puede eliminar una cotización facturada. "
                "Elimina primero la factura asociada si es necesario."
            )
        QuotationModel.delete_by_id(quotation_id)
        return True, "Cotización eliminada exitosamente."
