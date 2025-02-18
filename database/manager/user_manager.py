
from services.database import Database
from firebase_admin import firestore
from database.models.user import User
from dataclasses import asdict
from google.cloud.firestore_v1.transaction import Transaction
from exceptions.user_exceptions import NegativeBalanceError
from typing import Callable


class UserManager:
    USER_COLLECTION = "users"
    AVAILABLE = "avai"
    SOLD = "sold"

    def __init__(self, db: Database):
        self.db = db
        self.firestore = db.get_firestore()

    def get_user(self, user_id: str) -> User:
        doc_ref = self.firestore.collection(self.USER_COLLECTION).document(str(user_id))
        doc = doc_ref.get()
        if doc.exists:
            return User(**doc.to_dict())
        
        # User does not exist, create default one      
        user = User()
        doc_ref.set(asdict(user))
        return user
    
    def find_user_by_id(self, user_id: str) -> User | None:
        doc_ref = self.firestore.collection(self.USER_COLLECTION).document(str(user_id))
        doc = doc_ref.get()
        return User(**doc.to_dict()) if doc.exists else None

    def save_user(self, user_id: str, user: User) -> None:
        doc_ref = self.firestore.collection(self.USER_COLLECTION).document(str(user_id))
        doc_ref.set(asdict(user))

    async def add_balance(self, user_id: str, amount: int) -> None:
        """
            Raise: NegativeBalanceError
        """
        user_ref = self.db.document(self.USER_COLLECTION, user_id)

        async def transaction_operation(transaction: Transaction):
            user_doc = await user_ref.get(transaction=transaction)
            user = User(**user_doc.to_dict()) if user_doc.exists else  User(balance = amount, admin_password="")
            user.balance += amount

            if user.balance < 0:
                raise NegativeBalanceError("Negative balance!")
            
            transaction.set(user_ref, asdict(user))

        await self.db.transaction(transaction_operation)


    def add_balance_transaction(self, user_id: str, amount: int) -> Callable[[Transaction], None]:
        """
            Raise: NegativeBalanceError
        """
        user_ref = self.db.document(self.USER_COLLECTION, user_id)

        async def transaction_operation(transaction: Transaction) -> None:
            user_doc = await user_ref.get(transaction=transaction)
            user = User(**user_doc.to_dict()) if user_doc.exists else User(balance = amount, admin_password="")
            user.balance += amount

            if user.balance < 0:
                raise NegativeBalanceError("Negative balance!")
            
            transaction.set(user_ref, asdict(user))

        return transaction_operation



