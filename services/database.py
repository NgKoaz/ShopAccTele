import firebase_admin
from firebase_admin import credentials, firestore
from dataclasses import asdict

from models.user import User


class Database:
    USER_COLLECTION = "users"
    NEW_ACCOUNT_COLLECTION = "new_accounts"
    OLD_ACCOUNT_COLLECTION = "old_accounts"
    BANK_COLLECTION = "banks"

    instance = None

    def __init__(self):
        cred = credentials.Certificate("firebase.json")
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    @staticmethod
    def gI():
        Database.instance = Database.instance if Database.instance else Database()
        return Database.instance

    def get_user(self, user_id) -> User:
        doc_ref = self.db.collection(self.USER_COLLECTION).document(str(user_id))
        doc = doc_ref.get()
        if doc.exists:
            return User(**doc.to_dict())
                        
        print(f"Document {user_id} does not exist.")
        user = User()
        doc_ref.set(asdict(user))
        return user
        
    def get_bank_name(self, bin) -> str:
        bin = str(bin)
        doc_ref = self.db.collection(self.BANK_COLLECTION).document(bin)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            return data["code"] + " - " + data["name"]
            
        print(f"Document {bin} does not exist.")
        return bin

    def count_new_accounts(self):
        query = self.db.collection(self.NEW_ACCOUNT_COLLECTION).select([]).count()
        result = query.get()
        return result[0][0].value
  
    def count_old_accounts(self):
        query = self.db.collection(self.OLD_ACCOUNT_COLLECTION).select([]).count()
        result = query.get()
        return result[0][0].value
    
    def save_user(self, user_id: str, user: User) -> None:
        doc_ref = self.db.collection(self.USER_COLLECTION).document(str(user_id))
        doc_ref.set(asdict(user))
                        

