from dataclasses import dataclass

@dataclass
class User:
    balance: int = 0
    latest_payment_id: int = -1


