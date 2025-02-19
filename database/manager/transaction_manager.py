
from database.manager.base_manager import BaseManager
from database.models.deposit import Deposit
from dataclasses import asdict



class TransactionManager(BaseManager):
    @staticmethod
    async def find_deposit(id: str) -> Deposit | None:
        deposit = await TransactionManager._db.deposits.find_one({'id': id})
        return Deposit(deposit) if deposit else None
    
    @staticmethod
    async def create_deposit(deposit: Deposit):
        await TransactionManager._db.deposits.insert_one(asdict(deposit)) 

    @staticmethod
    async def find_deposit(id: str) -> Deposit | None:
        deposit = await TransactionManager._db.deposits.find_one({'id': id})
        return Deposit(deposit) if deposit else None

    