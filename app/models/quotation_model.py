from core.base_model import BaseModel
from core.orm import HasMany, ForeignKey

class QuotationModel(BaseModel):
    table_name = "quotations"
    items = HasMany("quotation_items", "quotation_id")
    client = ForeignKey("clients", "client_id")

class QuotationItemModel(BaseModel):
    table_name = "quotation_items"
    quotation = ForeignKey("quotations", "quotation_id")
