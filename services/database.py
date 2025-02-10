import firebase_admin
from firebase_admin import credentials, firestore, db
from dataclasses import asdict

from database.models.user import User
from database.models.category import Category
from database.models.setting_document import SettingDocument
from database.models.product import Product

"""Firestore and Real-time Storage"""
class Database:
    USER_COLLECTION = "users"
    AVAL_ACCOUNT_COLLECTION = "avai_accounts"
    SOLD_ACCOUNT_COLLECTION = "sold_accounts"

    AVAL_PRODUCT_COLLECTION = "avai_products"
    BANK_COLLECTION = "banks"
    CONFIG_COLLECTION = "config"

    SETTING_DOCUMENT = "data/settings"
    CATEGORY_COLLECTION = "categories"

    AVAILABLE = "avai"
    SOLD = "sold"

    def __init__(self):
        cred = credentials.Certificate("firebase.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://shop-acc-14496-default-rtdb.asia-southeast1.firebasedatabase.app/'
        })
        self.firestore = firestore.client()
        self.realtime_db = db

    def get_user(self, user_id) -> User:
        doc_ref = self.firestore.collection(self.USER_COLLECTION).document(str(user_id))
        doc = doc_ref.get()
        if doc.exists:
            return User(**doc.to_dict())
                        
        print(f"Document {user_id} does not exist.")
        user = User()
        doc_ref.set(asdict(user))
        return user

    def get_bank_name(self, bin) -> str:
        bin = str(bin)
        doc_ref = self.firestore.collection(self.BANK_COLLECTION).document(bin)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            return data["code"] + " - " + data["name"]
            
        print(f"Document {bin} does not exist.")
        return bin

    def count_new_accounts(self):
        query = self.firestore.collection(self.AVAL_ACCOUNT_COLLECTION).select([]).count()
        result = query.get()
        return result[0][0].value
    
    def get_categories(self) -> dict[Category]:
        query = self.firestore.collection(self.CATEGORY_COLLECTION)
        docs = query.get()
        categories = [Category(**doc.to_dict()) for doc in docs]
        return categories

    def count_old_accounts(self):
        query = self.firestore.collection(self.SOLD_ACCOUNT_COLLECTION).select([]).count()
        result = query.get()
        return result[0][0].value
    
    def save_user(self, user_id: str, user: User) -> None:
        doc_ref = self.firestore.collection(self.USER_COLLECTION).document(str(user_id))
        doc_ref.set(asdict(user))

    def transfer_to_old_acccount(self, phone: str, account: Product):
        self.firestore.collection(self.AVAL_ACCOUNT_COLLECTION).document(phone).delete()
        self.firestore.collection(self.SOLD_ACCOUNT_COLLECTION).document(phone).set(asdict(account))

    def get_new_order_id(self, default=123) -> int:
        ref = self.realtime_db.reference("/new_order_id")
        new_order_id = ref.get()
        if new_order_id is None:
            new_order_id = default
        ref.set(new_order_id + 1)
        return new_order_id

    def get_new_accounts(self, limit) -> dict[Product]:
        col_ref = self.firestore.collection(self.AVAL_ACCOUNT_COLLECTION)
        docs = col_ref.limit(limit).get()
        accounts = [doc.to_dict() for doc in docs]
        return accounts
        
    def get_setting(self) -> SettingDocument:
        doc_ref = self.firestore.document(self.SETTING_DOCUMENT)
        doc = doc_ref.get()
        if doc.exists:
            return SettingDocument(**doc.to_dict())
        
        setting = SettingDocument()
        doc_ref.set(asdict(setting))
        return setting

    def save_setting(self, setting: SettingDocument):
        doc_ref = self.firestore.document(self.SETTING_DOCUMENT)
        doc_ref.set(asdict(setting))

    def get_products(self) -> dict[Product]:
        col_ref = self.firestore.collection(self.CATEGORY_COLLECTION)
        docs = col_ref.get()
        products = [Product(**doc.to_dict()) for doc in docs]
        return products

    def save_product(self, category_id: str, product_id: str, product: Product):
        doc_ref = self.firestore.document(self.CATEGORY_COLLECTION + "/" + category_id + "/" + self.AVAILABLE + "/" + product_id)
        doc_ref.set(asdict(product))

    def transfer_avai_to_sold_product(self, category_id: str, product_id: str, product: Product):
        pass
        # self.firestore.collection(self.AVAL_ACCOUNT_COLLECTION).document(phone).delete()
        # self.firestore.collection(self.SOLD_ACCOUNT_COLLECTION).document(phone).set(asdict(account))



