from core.base_model import BaseModel
from core.orm import HasMany, ForeignKey

class InvoiceModel(BaseModel):
    table_name = "invoices"
    items = HasMany("invoice_items", "invoice_id")
    client = ForeignKey("clients", "client_id")

class InvoiceItemModel(BaseModel):
    table_name = "invoice_items"
    invoice = ForeignKey("invoices", "invoice_id")
