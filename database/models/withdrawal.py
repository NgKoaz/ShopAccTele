from dataclasses import dataclass
from datetime import datetime
from bson import ObjectId

@dataclass
class Deposit:
    _id: ObjectId = ObjectId()
    user_id: int = 0
    category_id: int = 0
    category_name: str = ""
    num_products: int = 0
    price: int = 0
    total: int = 0
    datetime: datetime