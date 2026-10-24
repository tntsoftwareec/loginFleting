from core.base_model import BaseModel
from core.orm import ForeignKey

class ProductModel(BaseModel):
    table_name = "products"
    supplier = ForeignKey("suppliers", "supplier_id")
