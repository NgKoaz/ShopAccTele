from dataclasses import dataclass
from bson import ObjectId


@dataclass
class Setting:
    _id: ObjectId = ObjectId()
    password: str = "123"
    storage_chat_id: int = 0
    next_category_id: int = 0