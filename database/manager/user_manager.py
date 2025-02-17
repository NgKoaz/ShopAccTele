
from services.database import Database
from database.models.product import Product
from database.models.user import User
from dataclasses import asdict


class UserManager:
    USER_COLLECTION = "users"
    AVAILABLE = "avai"
    SOLD = "sold"

    def __init__(self, db: Database):
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

