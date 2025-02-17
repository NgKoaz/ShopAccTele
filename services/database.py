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

    def get_firestore(self):
        return self.firestore

    def get_bank_name(self, bin) -> str:
        bin = str(bin)
        doc_ref = self.firestore.collection(self.BANK_COLLECTION).document(bin)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            return data["code"] + " - " + data["name"]
            
        print(f"Document {bin} does not exist.")
        return bin

    def get_new_order_id(self, default=123) -> int:
        ref = self.realtime_db.reference("/new_order_id")
        new_order_id = ref.get()
        if new_order_id is None:
            new_order_id = default
        ref.set(new_order_id + 1)
        return new_order_id

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
