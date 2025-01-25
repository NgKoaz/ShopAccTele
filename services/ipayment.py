from dataclasses import dataclass
from abc import ABC, abstractmethod



@dataclass
class BasicPaymentInfo:
    bin: str
    account_number: str
    account_name: str
    amount: int
    qr_code: str
    currency: str
    description: str
    expired_at: str


class IPayment(ABC):
    @abstractmethod
    def pay(self, path: str, file_name: str):
        """Load in the data set"""
        raise NotImplementedError

    @abstractmethod
    def extract_text(self, full_file_path: str):
        """Extract text from the data set"""
        raise NotImplementedError