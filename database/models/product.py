from dataclasses import dataclass


@dataclass
class Product:
    id: str = ""                        # Auto generate
    user_id: str = ""                   # Empty if nobody owns this product
    backup_message_id: str = ""         # Message ID attaching with file
    backup_storage_group_id: str = ""   # Group ID where the message is
