
from services.database import Database
from database.manager.user_manager import UserManager
from database.models.user import User
from database.models.transaction_in import TransactionIn
from dataclasses import asdict
from datetime import datetime



class TransactionManager:
    INGOING_TRANSACTIONS = "INGOING_TRANSACTIONS"

    def __init__(self, db: Database):
        self.firestore = db.get_firestore()


    def _exchange_datetime_str(self, date_string: str):
        """ From 17/02/2025 11:32:30 to %d-%m-%Y %H:%M:%S for saving to firestore """
        # Convert string to datetime object
        date_obj = datetime.strptime(date_string, "%d/%m/%Y %H:%M:%S")

        # Convert datetime object back to string with the new format
        return date_obj.strftime("%d-%m-%Y %H:%M:%S")
    

    def create_mbbank_ingoing_transaction_id(self, datetime: str, refNo: str) -> str:
        """ Only for MbBank """
        return self._exchange_datetime_str(datetime) + " " + refNo


    def find_ingoing_transaction_by_id(self, user_id: str, ingoing_transaction_id: str) -> TransactionIn | None:
        """ Format of ingoing_transaction_id: %d-%m-%Y %H:%M:%S FTxxxxxxxx """ 
        doc_ref = self.firestore.document(
            "/".join([UserManager.USER_COLLECTION, str(user_id), self.INGOING_TRANSACTIONS, ingoing_transaction_id])
        )
        doc = doc_ref.get()
        return TransactionIn(**doc.to_dict()) if doc.exists else None
    
        
    def save_ingoing_transaction(self, user_id: str, ingoing_transaction_id: str, ingoing_transaction: TransactionIn) -> User:
        doc_ref = self.firestore.document(
            "/".join([UserManager.USER_COLLECTION, str(user_id), self.INGOING_TRANSACTIONS, ingoing_transaction_id])
        )
        doc = doc_ref.set(asdict(ingoing_transaction))
    

