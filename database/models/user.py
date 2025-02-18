from dataclasses import dataclass
from bson import ObjectId


@dataclass
class User:
    _id: ObjectId = ObjectId()
    id: int = 0
    balance: int = 0
    admin_password: str = ""
    