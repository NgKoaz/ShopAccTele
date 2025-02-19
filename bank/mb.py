from mbbank import MBBank, MBBankError
from .ocr_scanner import OcrScanner
from datetime import datetime, timedelta
from database.manager.all_managers import *
from database.models.deposit import Deposit
from functools import partial
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
            
            time.sleep(15)
        except MBBankError:
            mb = MBBank(username="0905770857", password="Arigato147!", proxy=None, ocr_class=OcrScanner())
    

async def _save_transactions(transactions):
    pattern = fr"{prefix}\d+"
    for transaction in transactions:
        desc_match = re.search(pattern, transaction["addDescription"].replace(" ", ""))

        if desc_match:
            desc = desc_match.group()
            # Remove prefix of description
            user_id = desc[len(prefix):]

            deposit = await TransactionManager.find_deposit(id=transaction["refNo"])

            if deposit is None:
                amount = int(transaction['creditAmount'])
                await TransactionManager.create_deposit(Deposit(
                    id=transaction['refNo'], 
                    user_id=user_id, 
                    amount=amount, 
                    datetime=datetime.strptime(transaction["transactionDate"], "%d/%m/%Y %H:%M:%S")
                ))
                await TransactionManager.exec_transactions([partial(UserManager.add_balance, user_id=user_id, amount=amount)])


                
    