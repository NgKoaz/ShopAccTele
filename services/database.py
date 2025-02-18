import firebase_admin
from firebase_admin import credentials, firestore, db
from dataclasses import asdict
from database.models.setting_document import SettingDocument
from typing import Callable, Any
from google.cloud.firestore_v1.transaction import Transaction



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


    def document(self, *args: str):
        return self.firestore.document(args)

    def collection(self, *args: str):
        return self.firestore.collection(args)

    def transaction(self, transaction_operation: Callable[[Transaction], Any]) -> Any:
        transaction = self.firestore.transaction()
        result = transaction_operation(transaction) 
        transaction.commit()
        return result
    