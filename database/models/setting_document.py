from dataclasses import dataclass


@dataclass
class SettingDocument:
    password: str = "123"
    storage_group_id: str = ""