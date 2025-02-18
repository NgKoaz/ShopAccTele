
from services.database import Database
from database.models.product import Product
from database.models.user import User
from dataclasses import asdict
from google.cloud.firestore_v1.transaction import Transaction



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

    """ Using transaction """
    def add_balance(self, user_id: str, amount: int) -> None:
        user_ref = self.db.document(self.USER_COLLECTION, user_id)
        def transaction_operation(transaction: Transaction):
            user_doc = transaction.get(user_ref)
            if user_doc.exists:
                user = User(**user_doc.to_dict())
                user.balance += amount
                user_ref.update({'balance': user.balance})
            else:
                new_user = User(balance = amount, admin_password="")
                user_ref.set(asdict(new_user))
        self.db.transaction(transaction_operation=transaction_operation)


