from dataclasses import dataclass
from datetime import datetime
from bson import ObjectId


@dataclass
class Deposit:
    _id: ObjectId = ObjectId()
    id: str = ""
    user_id: int = 0
    amount: int = 0
    datetime: datetime 