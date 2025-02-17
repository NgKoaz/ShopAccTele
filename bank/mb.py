from mbbank import MBBank, MBBankError
from .ocr_scanner import OcrScanner
from datetime import datetime, timedelta
from services.container import Container
from database.models.transaction_in import TransactionIn
import time
import json
import re


prefix = "TELE"


def check_transaction_history():
    mb = MBBank(username="0905770857", password="Arigato147!", proxy=None, ocr_class=OcrScanner())
    while True:
        try:
            today = datetime.today()
            seven_days_ago = datetime.today() - timedelta(days=2)
            result = mb.getTransactionAccountHistory(accountNo="0905770857", from_date=seven_days_ago, to_date=today)
            with open("bank/result.json", 'w', encoding='utf-8') as file:
                json.dump(result, file, ensure_ascii=False, indent=4)
            _save_transactions(result["transactionHistoryList"])
            
            time.sleep(12)
        except MBBankError:
            mb = MBBank(username="0905770857", password="Arigato147!", proxy=None, ocr_class=OcrScanner())
    

def _save_transactions(transactions):
    user_manager = Container.user_manager()
    transaction_manager = Container.transaction_manager()

    pattern = fr"{prefix}\d+"
    for transaction in transactions:
        match = re.search(pattern, transaction["addDescription"].replace(" ", ""))

        if match:
            matched_text = match.group()
            user_id = matched_text[len(prefix):]

            ingoing_transaction_id = transaction_manager.create_mbbank_ingoing_transaction_id(transaction["transactionDate"], transaction["refNo"])
            ingoing_transaction = transaction_manager.find_ingoing_transaction_by_id(user_id, ingoing_transaction_id)
            if ingoing_transaction is None:
                # Mark ingoing transaction
                creditAmount = int(transaction["creditAmount"])
                transaction_in = TransactionIn(amount=creditAmount)
                transaction_in_id = transaction_manager.create_mbbank_ingoing_transaction_id(transaction["transactionDate"], transaction["refNo"])
                transaction_manager.save_ingoing_transaction(user_id, transaction_in_id, transaction_in)

                # Add funds for user
                user = user_manager.get_user(user_id)
                user.balance += creditAmount
                user_manager.save_user(user_id, user)


                
    