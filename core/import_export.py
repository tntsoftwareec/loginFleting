"""Importación desde Excel y exportación a Excel/PDF de los datos del sistema.

Cubre las cuatro entidades principales:

* clientes
* productos
* facturas (una fila por ítem, agrupadas por la columna ``grupo``)
* cotizaciones (misma estructura que facturas)

Los archivos exportados usan exactamente el mismo formato que el importador,
por lo que sirven también como plantilla de ida y vuelta.
"""
import os
from datetime import date, datetime

from app.controllers.client_controller import ClientController
from app.controllers.product_controller import ProductController
from app.controllers.inventory_controller import InventoryController
from app.controllers.invoice_controller import InvoiceController
from app.controllers.quotation_controller import QuotationController
from core.database import transaction
from app.models.client_model import ClientModel
from app.models.product_model import ProductModel
from app.models.invoice_model import InvoiceModel
from app.models.quotation_model import QuotationModel
from core.documents import excel_io, list_pdf, storage
from core.logger import get_logger

logger = get_logger("ImportExport")

# ---------------------------------------------------------------------------
# Definición de columnas
# ---------------------------------------------------------------------------

CUSTOMERS = {
    "label": "Clientes",
    "sheet": "Clientes",
    "file": "clientes",
    "title": "Listado de clientes",
    "headers": ["tipo_documento", "identificacion", "razon_social", "email",
                "telefono", "direccion", "activo"],
    "instructions": [
        ("tipo_documento", "CEDULA, RUC, PASAPORTE o CONSUMIDOR_FINAL. Por defecto CEDULA.", "CEDULA"),
        ("identificacion", "Número de cédula o RUC. Si ya existe, el cliente se actualiza.", "1713175071"),
        ("razon_social", "Nombre completo o razón social (obligatorio).", "María Fernanda Torres"),
        ("email", "Correo electrónico para enviar cotizaciones y facturas.", "cliente@example.com"),
        ("telefono", "Teléfono o WhatsApp en formato +593 9XXXXXXXX.", "+593 991234567"),
        ("direccion", "Dirección del cliente.", "Av. Amazonas N34-451, Quito"),
        ("activo", "SI o NO. Por defecto SI.", "SI"),
    ],
    "pdf": [("identificacion", "Identificación"), ("razon_social", "Razón social"),
            ("tipo_documento", "Tipo"), ("email", "Email"), ("telefono", "Teléfono"),
            ("direccion", "Dirección"), ("estado", "Estado")],
}

PRODUCTS = {
    "label": "Productos",
    "sheet": "Productos",
    "file": "productos",
    "title": "Listado de productos y servicios",
    "headers": ["codigo", "nombre", "descripcion", "categoria", "precio",
                "costo", "stock", "iva", "activo"],
    "instructions": [
        ("codigo", "Código único del producto. Si ya existe, el producto se actualiza.", "P0001"),
        ("nombre", "Nombre del producto o servicio (obligatorio).", "Laptop Lenovo ThinkPad"),
        ("descripcion", "Descripción opcional.", "14 pulgadas, 16 GB RAM"),
        ("categoria", "Categoría libre.", "Tecnología"),
        ("precio", "Precio de venta sin IVA. Use punto como separador decimal.", "780.00"),
        ("costo", "Costo del producto (opcional).", "600.00"),
        ("stock", "Cantidad disponible (opcional).", "10"),
        ("iva", "Porcentaje de IVA: 15, 12, 5 o 0.", "15"),
        ("activo", "SI o NO. Por defecto SI.", "SI"),
    ],
    "pdf": [("codigo", "Código"), ("nombre", "Nombre"), ("categoria", "Categoría"),
            ("precio", "Precio"), ("iva", "IVA %"), ("stock", "Stock"), ("estado", "Estado")],
}

INVOICES = {
    "label": "Facturas",
    "sheet": "Facturas",
    "file": "facturas",
    "title": "Listado de facturas emitidas",
    "headers": ["grupo", "fecha", "cliente_identificacion", "cliente_nombre", "forma_pago",
                "codigo", "descripcion", "cantidad", "precio_unitario", "descuento", "iva"],
    "instructions": [
        ("grupo", "Identificador del comprobante. Todas las filas con el mismo grupo forman una factura.", "F-001"),
        ("fecha", "Fecha de emisión dd/mm/aaaa. Si se omite se usa la fecha actual.", "18/10/2026"),
        ("cliente_identificacion", "Cédula/RUC del cliente. Si no existe se crea automáticamente.", "1713175071"),
        ("cliente_nombre", "Nombre del cliente (para crearlo si no existe).", "María Torres"),
        ("forma_pago", "EFECTIVO, TARJETA o TRANSFERENCIA (también 01, 16, 19, 20).", "EFECTIVO"),
        ("codigo", "Código del producto o servicio.", "P0001"),
        ("descripcion", "Descripción del ítem (obligatorio).", "Laptop Lenovo"),
        ("cantidad", "Cantidad vendida.", "2"),
        ("precio_unitario", "Precio unitario sin IVA.", "780.00"),
        ("descuento", "Descuento en dólares para la línea.", "0"),
        ("iva", "Porcentaje de IVA de la línea (15 por defecto).", "15"),
        ("IMPORTANTE", "Cada importación emite facturas nuevas; no reimporte el mismo archivo.", ""),
    ],
    "pdf": [("numero", "Número"), ("fecha", "Fecha"), ("cliente", "Cliente"),
            ("total", "Total"), ("estado", "Estado SRI"), ("clave", "Clave de acceso")],
}

QUOTES = {
    "label": "Cotizaciones",
    "sheet": "Cotizaciones",
    "file": "cotizaciones",
    "title": "Listado de cotizaciones",
    "headers": ["grupo", "fecha", "cliente_identificacion", "cliente_nombre", "dias_validez",
                "codigo", "descripcion", "cantidad", "precio_unitario", "descuento", "iva",
                "observaciones"],
    "instructions": [
        ("grupo", "Identificador de la cotización. Filas con el mismo grupo forman una cotización.", "C-001"),
        ("fecha", "Fecha de emisión dd/mm/aaaa. Si se omite se usa la fecha actual.", "18/10/2026"),
        ("cliente_identificacion", "Cédula/RUC del cliente. Si no existe se crea automáticamente.", "1713175071"),
        ("cliente_nombre", "Nombre del cliente (para crearlo si no existe).", "María Torres"),
        ("dias_validez", "Días de validez de la cotización (15 por defecto).", "15"),
        ("codigo", "Código del producto o servicio.", "P0001"),
        ("descripcion", "Descripción del ítem (obligatorio).", "Laptop Lenovo"),
        ("cantidad", "Cantidad cotizada.", "2"),
        ("precio_unitario", "Precio unitario sin IVA.", "780.00"),
        ("descuento", "Descuento en dólares para la línea.", "0"),
        ("iva", "Porcentaje de IVA de la línea (15 por defecto).", "15"),
        ("observaciones", "Observaciones de la cotización.", "Precios válidos por 15 días"),
        ("IMPORTANTE", "Cada importación crea cotizaciones nuevas; no reimporte el mismo archivo.", ""),
    ],
    "pdf": [("numero", "Número"), ("fecha", "Fecha"), ("cliente", "Cliente"),
            ("total", "Total"), ("validez", "Válida hasta"), ("estado", "Estado")],
}

KINDS = {
    "customers": CUSTOMERS,
    "products": PRODUCTS,
    "invoices": INVOICES,
    "quotes": QUOTES,
}

PAYMENT_MAP = {
    "01": "EFECTIVO", "1": "EFECTIVO", "EFECTIVO": "EFECTIVO", "CONTADO": "EFECTIVO",
    "16": "TARJETA", "TARJETA": "TARJETA", "DEBITO": "TARJETA", "CREDITO": "TARJETA",
    "19": "TRANSFERENCIA", "20": "TRANSFERENCIA", "TRANSFERENCIA": "TRANSFERENCIA",
    "TRANSFER": "TRANSFERENCIA",
}


# ---------------------------------------------------------------------------
# Conversión de valores
# ---------------------------------------------------------------------------

def _text(value) -> str:
    return "" if value is None else str(value).strip()


def _to_float(value, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace("$", "").replace(" ", "")
    if not text:
        return default
    if "." in text and "," in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return default


def _to_bool(value, default: bool = True) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    text = _text(value).lower()
    return text in ("si", "sí", "s", "1", "true", "yes", "x", "activo", "a")


def _parse_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = _text(value)
    if not text:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%y", "%d-%m-%y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _guess_doc_type(identification: str) -> str:
    digits = "".join(ch for ch in str(identification or "") if ch.isdigit())
    if len(digits) == 13:
        return "RUC"
    if len(digits) == 10:
        return "CEDULA"
    return "PASAPORTE"


def _normalize_iva(value) -> float:
    if value is None or value == "":
        return 15.0
    rate = _to_float(value, 15.0)
    if 0 < rate <= 1:
        rate *= 100
    return rate


def _normalize_payment(value) -> str:
    text = _text(value).upper()
    return PAYMENT_MAP.get(text, "EFECTIVO")


def _group_rows(rows):
    groups = {}
    for index, row in enumerate(rows, start=2):
        key = _text(row.get("grupo")) or f"fila_{index}"
        groups.setdefault(key, []).append(row)
    return groups


def _is_active(row) -> str:
    return "active" if _to_bool(row.get("activo"), True) else "inactive"


# ---------------------------------------------------------------------------
# Exportación
# ---------------------------------------------------------------------------

def _customer_rows():
    rows = []
    for c in ClientController.get_all():
        rows.append({
            "tipo_documento": c.get("tipo_documento") or "CEDULA",
            "identificacion": c.get("identificacion") or "",
            "razon_social": c.get("razon_social") or "",
            "email": c.get("email") or "",
            "telefono": c.get("telefono") or "",
            "direccion": c.get("direccion") or "",
            "activo": "SI" if (c.get("status") or "active") == "active" else "NO",
        })
    return rows


def _product_rows():
    rows = []
    for p in ProductController.get_all():
        rows.append({
            "codigo": p.get("codigo") or "",
            "nombre": p.get("nombre") or "",
            "descripcion": p.get("descripcion") or "",
            "categoria": p.get("categoria") or "General",
            "precio": float(p.get("precio") or 0),
            "costo": float(p.get("costo") or 0),
            "stock": float(p.get("stock") or 0),
            "iva": float(p.get("iva_porcentaje") or 0),
            "activo": "SI" if (p.get("status") or "active") == "active" else "NO",
        })
    return rows


def _invoice_rows():
    rows = []
    for inv in InvoiceController.get_all():
        full = InvoiceModel.with_("items").find(inv["id"]) or {}
        items = full.get("items") or []
        base = {
            "grupo": inv.get("secuencial") or "",
            "fecha": inv.get("fecha_emision") or "",
            "cliente_identificacion": inv.get("client_identificacion") or "",
            "cliente_nombre": inv.get("client_nombre") or "",
            "forma_pago": inv.get("forma_pago") or "EFECTIVO",
        }
        if not items:
            rows.append(dict(base, codigo="", descripcion="", cantidad=0,
                             precio_unitario=0, descuento=0, iva=0))
            continue
        for item in items:
            rows.append(dict(
                base,
                codigo=item.get("codigo") or "",
                descripcion=item.get("descripcion") or "",
                cantidad=float(item.get("cantidad") or 0),
                precio_unitario=float(item.get("precio_unitario") or 0),
                descuento=float(item.get("descuento") or 0),
                iva=float(item.get("iva_porcentaje") or 0),
            ))
    return rows


def _quote_rows():
    rows = []
    for quote in QuotationController.get_all():
        full = QuotationModel.with_("items").find(quote["id"]) or {}
        items = full.get("items") or []
        fecha_validez = quote.get("fecha_validez") or ""
        dias = 15
        if quote.get("fecha_emision") and fecha_validez:
            try:
                delta = datetime.strptime(fecha_validez, "%Y-%m-%d") - \
                    datetime.strptime(quote["fecha_emision"], "%Y-%m-%d")
                dias = max(1, delta.days)
            except ValueError:
                pass
        base = {
            "grupo": quote.get("secuencial") or "",
            "fecha": quote.get("fecha_emision") or "",
            "cliente_identificacion": quote.get("client_identificacion") or "",
            "cliente_nombre": quote.get("client_nombre") or "",
            "dias_validez": dias,
            "observaciones": quote.get("notas") or "",
        }
        if not items:
            rows.append(dict(base, codigo="", descripcion="", cantidad=0,
                             precio_unitario=0, descuento=0, iva=0))
            continue
        for item in items:
            rows.append(dict(
                base,
                codigo=item.get("codigo") or "",
                descripcion=item.get("descripcion") or "",
                cantidad=float(item.get("cantidad") or 0),
                precio_unitario=float(item.get("precio_unitario") or 0),
                descuento=float(item.get("descuento") or 0),
                iva=float(item.get("iva_porcentaje") or 0),
            ))
    return rows


EXPORTERS = {
    "customers": _customer_rows,
    "products": _product_rows,
    "invoices": _invoice_rows,
    "quotes": _quote_rows,
}


def _pdf_rows(kind: str):
    meta = KINDS[kind]
    headers = [label for _key, label in meta["pdf"]]
    rows = []
    if kind == "customers":
        for r in _customer_rows():
            rows.append({
                "identificacion": r["identificacion"], "razon_social": r["razon_social"],
                "tipo_documento": r["tipo_documento"], "email": r["email"],
                "telefono": r["telefono"], "direccion": r["direccion"], "estado": r["activo"],
            })
    elif kind == "products":
        for r in _product_rows():
            rows.append({
                "codigo": r["codigo"], "nombre": r["nombre"], "categoria": r["categoria"],
                "precio": f"$ {r['precio']:,.2f}", "iva": f"{r['iva']:g}",
                "stock": f"{r['stock']:g}", "estado": r["activo"],
            })
    elif kind == "invoices":
        for inv in InvoiceController.get_all():
            rows.append({
                "numero": inv.get("secuencial") or "",
                "fecha": inv.get("fecha_emision") or "",
                "cliente": inv.get("client_nombre") or "",
                "total": f"$ {float(inv.get('importe_total') or 0):,.2f}",
                "estado": inv.get("estado") or "",
                "clave": inv.get("clave_acceso") or "",
            })
    else:
        for quote in QuotationController.get_all():
            rows.append({
                "numero": quote.get("secuencial") or "",
                "fecha": quote.get("fecha_emision") or "",
                "cliente": quote.get("client_nombre") or "",
                "total": f"$ {float(quote.get('importe_total') or 0):,.2f}",
                "validez": quote.get("fecha_validez") or "",
                "estado": quote.get("estado") or "",
            })
    keys = [key for key, _label in meta["pdf"]]
    return headers, [[row.get(key, "") for key in keys] for row in rows]


def build_export(kind: str, fmt: str = "xlsx"):
    """Devuelve (nombre_de_archivo, bytes) para guardar o enviar al cliente."""
    meta = KINDS[kind]
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    if fmt == "pdf":
        headers, rows = _pdf_rows(kind)
        data = list_pdf.list_pdf_bytes(meta["title"], headers, rows,
                                       subtitle=f"Total de registros: {len(rows)}")
        return f"{meta['file']}_{stamp}.pdf", data

    rows = EXPORTERS[kind]()
    data = excel_io.table_bytes(meta["sheet"], meta["headers"], rows,
                                instructions=meta["instructions"])
    return f"{meta['file']}_{stamp}.xlsx", data


def save_export(kind: str, fmt: str = "xlsx") -> str:
    filename, data = build_export(kind, fmt)
    path = storage.exportes_path(filename)
    with open(path, "wb") as fh:
        fh.write(data)
    logger.info("Exportado %s -> %s", kind, path)
    return path


def build_template(kind: str):
    """Plantilla Excel vacía (con hoja de instrucciones)."""
    meta = KINDS[kind]
    data = excel_io.table_bytes(meta["sheet"], meta["headers"], [],
                                instructions=meta["instructions"])
    return f"plantilla_{meta['file']}.xlsx", data


# ---------------------------------------------------------------------------
# Importación
# ---------------------------------------------------------------------------

def _summary(kind: str) -> dict:
    return {"kind": kind, "label": KINDS[kind]["label"], "created": 0, "updated": 0,
            "skipped": 0, "errors": [], "total": 0.0}


def import_customers(path) -> dict:
    result = _summary("customers")
    _headers, rows = excel_io.read_table(path)
    seen = set()
    for index, row in enumerate(rows, start=2):
        name = _text(row.get("razon_social")) or _text(row.get("nombre"))
        identification = _text(row.get("identificacion"))
        if not name:
            result["errors"].append(f"Fila {index}: falta la razón social.")
            result["skipped"] += 1
            continue
        if not identification:
            result["errors"].append(f"Fila {index}: falta la identificación.")
            result["skipped"] += 1
            continue
        if identification in seen:
            result["skipped"] += 1
            continue
        seen.add(identification)
        data = dict(
            tipo_documento=(_text(row.get("tipo_documento")) or _guess_doc_type(identification)).upper(),
            identificacion=identification,
            razon_social=name,
            email=_text(row.get("email")),
            telefono=_text(row.get("telefono")),
            direccion=_text(row.get("direccion")),
            status=_is_active(row),
        )
        try:
            existing = ClientModel.where(identificacion=identification)
            if existing:
                ClientModel.update_by_id(existing[0]["id"], **data)
                result["updated"] += 1
            else:
                ClientModel.create(**data)
                result["created"] += 1
        except Exception as exc:  # noqa: BLE001
            result["errors"].append(f"Fila {index}: {exc}")
            result["skipped"] += 1
    return result


def _unique_product_code(base: str) -> str:
    base = (base or "PEN").strip().upper()[:12] or "PEN"
    candidate = base
    suffix = 1
    while ProductModel.where(codigo=candidate):
        suffix += 1
        candidate = f"{base}-{suffix}"
    return candidate


def import_products(path) -> dict:
    result = _summary("products")
    _headers, rows = excel_io.read_table(path)
    for index, row in enumerate(rows, start=2):
        name = _text(row.get("nombre"))
        code = _text(row.get("codigo"))
        if not name:
            result["errors"].append(f"Fila {index}: falta el nombre.")
            result["skipped"] += 1
            continue
        stock_value = int(_to_float(row.get("stock")))
        data = dict(
            codigo=code,
            nombre=name,
            descripcion=_text(row.get("descripcion")),
            categoria=_text(row.get("categoria")) or "General",
            precio=_to_float(row.get("precio")),
            costo=_to_float(row.get("costo")),
            stock=stock_value,
            iva_porcentaje=_normalize_iva(row.get("iva")),
            status=_is_active(row),
        )
        try:
            existing = ProductModel.where(codigo=code) if code else ProductModel.where(nombre=name)
            if existing:
                product = existing[0]
                old_stock = int(product.get("stock") or 0)
                data.pop("codigo", None)
                with transaction():
                    ProductModel.update_by_id(product["id"], **data)
                    InventoryController.log_stock_change(
                        product["id"],
                        stock_anterior=old_stock,
                        stock_nuevo=stock_value,
                        motivo="Importación de productos desde Excel",
                        referencia="Excel",
                    )
                result["updated"] += 1
            else:
                if not code:
                    data["codigo"] = _unique_product_code(name[:12].replace(" ", ""))
                with transaction():
                    new_product = ProductModel.create(**data)
                    if stock_value > 0:
                        InventoryController.log_stock_change(
                            new_product["id"],
                            stock_anterior=0,
                            stock_nuevo=stock_value,
                            motivo="Importación de productos desde Excel",
                            referencia="Excel",
                            tipo="INICIAL",
                        )
                result["created"] += 1
        except Exception as exc:  # noqa: BLE001
            result["errors"].append(f"Fila {index}: {exc}")
            result["skipped"] += 1
    return result


def _resolve_client(row):
    identification = _text(row.get("cliente_identificacion"))
    if not identification or identification == "9999999999999":
        return None
    existing = ClientModel.where(identificacion=identification)
    if existing:
        return existing[0]
    name = _text(row.get("cliente_nombre")) or f"Cliente {identification}"
    return ClientModel.create(
        tipo_documento=_guess_doc_type(identification),
        identificacion=identification,
        razon_social=name,
        email="",
        telefono="",
        direccion="",
        status="active",
    )


def _items_from_rows(rows):
    """Construye los ítems del carrito que esperan los controladores."""
    items = []
    for row in rows:
        description = _text(row.get("descripcion"))
        if not description:
            continue
        code = _text(row.get("codigo")) or "S/C"
        matches_product = bool(code and code != "S/C" and ProductModel.where(codigo=code))
        items.append({
            "tipo": "producto" if matches_product else "servicio",
            # item_id=None: la importación no descuenta stock ni exige stock disponible.
            "id": None,
            "codigo": code,
            "nombre": description,
            "cantidad": _to_float(row.get("cantidad"), 1.0) or 1.0,
            "precio": _to_float(row.get("precio_unitario")),
            "descuento": _to_float(row.get("descuento")),
            "iva_porcentaje": _normalize_iva(row.get("iva")),
        })
    return items


def import_invoices(path) -> dict:
    result = _summary("invoices")
    _headers, rows = excel_io.read_table(path)
    for group, group_rows in _group_rows(rows).items():
        first = group_rows[0]
        items = _items_from_rows(group_rows)
        if not items:
            result["errors"].append(f"Grupo {group}: sin ítems válidos.")
            result["skipped"] += 1
            continue
        try:
            client = _resolve_client(first)
            parsed = _parse_date(first.get("fecha"))
            success, response = InvoiceController.create_invoice(
                client.get("id") if client else None,
                items,
                forma_pago=_normalize_payment(first.get("forma_pago")),
                fecha=parsed.isoformat() if parsed else None,
                send_email=False,
            )
            if not success:
                result["errors"].append(f"Grupo {group}: {response}")
                result["skipped"] += 1
                continue
            result["created"] += 1
            result["total"] += float(response.get("importe_total") or 0)
        except Exception as exc:  # noqa: BLE001
            result["errors"].append(f"Grupo {group}: {exc}")
            result["skipped"] += 1
    return result


def import_quotes(path) -> dict:
    result = _summary("quotes")
    _headers, rows = excel_io.read_table(path)
    for group, group_rows in _group_rows(rows).items():
        first = group_rows[0]
        items = _items_from_rows(group_rows)
        if not items:
            result["errors"].append(f"Grupo {group}: sin ítems válidos.")
            result["skipped"] += 1
            continue
        try:
            client = _resolve_client(first)
            if not client:
                result["errors"].append(f"Grupo {group}: se requiere la identificación del cliente.")
                result["skipped"] += 1
                continue
            parsed = _parse_date(first.get("fecha"))
            success, response = QuotationController.create_quotation(
                client["id"],
                items,
                notas=_text(first.get("observaciones")),
                dias_validez=int(_to_float(first.get("dias_validez"), 15) or 15),
                fecha=parsed.isoformat() if parsed else None,
            )
            if not success:
                result["errors"].append(f"Grupo {group}: {response}")
                result["skipped"] += 1
                continue
            result["created"] += 1
            result["total"] += float(response.get("importe_total") or 0)
        except Exception as exc:  # noqa: BLE001
            result["errors"].append(f"Grupo {group}: {exc}")
            result["skipped"] += 1
    return result


IMPORTERS = {
    "customers": import_customers,
    "products": import_products,
    "invoices": import_invoices,
    "quotes": import_quotes,
}


def import_file(kind: str, path) -> dict:
    meta = KINDS[kind]
    if not path:
        return {**_summary(kind), "errors": ["No se seleccionó ningún archivo."]}
    if not os.path.isfile(path):
        return {**_summary(kind), "errors": ["El archivo seleccionado no existe."]}
    if not str(path).lower().endswith((".xlsx", ".xlsm")):
        return {**_summary(kind), "errors": ["El archivo debe ser Excel (.xlsx)."]}
    try:
        result = IMPORTERS[kind](path)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error importando %s", kind)
        return {**_summary(kind), "errors": [f"No se pudo leer el archivo: {exc}"]}
    logger.info("Importación %s: %s", meta["label"], result)
    return result


def summary_message(result: dict) -> str:
    parts = [f"{result.get('label', 'Registros')}:"]
    if result.get("created"):
        parts.append(f"{result['created']} creado(s)")
    if result.get("updated"):
        parts.append(f"{result['updated']} actualizado(s)")
    if result.get("skipped"):
        parts.append(f"{result['skipped']} omitido(s)")
    if result.get("total"):
        parts.append(f"total ${float(result['total']):,.2f}")
    if not any(result.get(k) for k in ("created", "updated", "skipped")):
        parts.append("sin cambios")
    if result.get("errors"):
        parts.append(f"{len(result['errors'])} error(es)")
    return " ".join(parts)
