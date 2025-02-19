from dataclasses import dataclass
from bson import ObjectId
from datetime import datetime


@dataclass
class Product:
    _id: ObjectId = ObjectId()
    id: int                       
    user_id: int = -1                  # Empty if nobody owns this product
    category_id: int = -1
    original_message_id: int = -1
    original_chat_id: int = -1
    backup_message_id: int = -1        # Message ID attaching with file
    backup_chat_id: int = -1           # Group ID where the message is
    bought_at: datetime = None
    