from dataclasses import dataclass
from bson import ObjectId


@dataclass
class Category:
    _id: ObjectId = ObjectId()
    id: str = ""
    user_id: int = 0               # The user that owns this category
    name: str = ""
    price: int = 9999999999
    adding_instruction: str = ""
    num_avai_products: int = 0
    num_sold_products: int = 0
    next_product_id: int = 0