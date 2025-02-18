from dataclasses import dataclass

@dataclass
class User:
    balance: int = 0
    admin_password: str = ""
