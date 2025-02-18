import firebase_admin
from firebase_admin import credentials, firestore, db
from google.cloud import firestore
from dataclasses import asdict
from database.models.setting_document import SettingDocument
from typing import Callable, Any, List
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
        args = [str(arg) for arg in args]
        return self.firestore.document("/".join(args))

    def collection(self, *args: str):
        args = [str(arg) for arg in args]
        return self.firestore.collection("/".join(args))

    async def exec_transactions(self, transaction_operations: List[Callable[[Transaction], Any]]) -> List[Any]:
        @firestore.async_transactional
        async def transaction_wrapper(transaction: Transaction) -> List[Any]:
            results = []
            for transaction_operation in transaction_operations:
                pass
                # result = await transaction_operation(transaction)  # Execute each transaction operation
                # results.append(result)
            return results

        return await transaction_wrapper(self.firestore.transaction())
    