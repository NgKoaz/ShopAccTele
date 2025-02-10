from dataclasses import dataclass


@dataclass
class Product:
    category_id: str = ""
    user_id: str = ""   # Empty if nobody owns this product
    file_id: str = ""
    
    backup_message_id: str = ""
    backup_storage_group_id: str = ""

