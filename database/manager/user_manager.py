from database.manager.base_manager import BaseManager
from database.models.user import User
from dataclasses import asdict
from exceptions.user_exceptions import NegativeBalanceError
from typing import Callable


class UserManager(BaseManager):
    @staticmethod
    async def get_user(id: str, session=None) -> User:
        user = await UserManager._db.users.find_one({'id': id}, session=session)
        if user:
            return User(user)
        else:
            user = User(id=id)
            await UserManager._db.users.insert_one(asdict(user), session=session)
            return user
        
    @staticmethod
    async def add_balance(user_id: str, amount: int, session) -> None:
        user = await UserManager.get_user(user_id)
        new_balance = user.balance + amount
        if new_balance < 0:
            raise NegativeBalanceError("Negative balance!")
        UserManager._db.users.update_one({'_id': user._id}, {'$set': { 'balance': new_balance }}, session=session)

    # def find_user_by_id(self, user_id: str) -> User | None:
    #     doc_ref = self.firestore.collection(self.USER_COLLECTION).document(str(user_id))
    #     doc = doc_ref.get()
    #     return User(**doc.to_dict()) if doc.exists else None

    # def save_user(self, user_id: str, user: User) -> None:
    #     doc_ref = self.firestore.collection(self.USER_COLLECTION).document(str(user_id))
    #     doc_ref.set(asdict(user))

    # async def add_balance(self, user_id: str, amount: int) -> None:
    #     """
    #         Raise: NegativeBalanceError
    #     """
    #     user_ref = self.db.document(self.USER_COLLECTION, user_id)

    #     async def transaction_operation(transaction: Transaction):
    #         user_doc = await user_ref.get(transaction=transaction)
    #         user = User(**user_doc.to_dict()) if user_doc.exists else  User(balance = amount, admin_password="")
    #         user.balance += amount

    #         if user.balance < 0:
    #             raise NegativeBalanceError("Negative balance!")
            
    #         transaction.set(user_ref, asdict(user))

    #     await self.db.transaction(transaction_operation)


    # def add_balance_transaction(self, user_id: str, amount: int) -> Callable[[Transaction], None]:
    #     """
    #         Raise: NegativeBalanceError
    #     """
    #     user_ref = self.db.document(self.USER_COLLECTION, user_id)

    #     async def transaction_operation(transaction: Transaction) -> None:
    #         user_doc = await user_ref.get(transaction=transaction)
    #         user = User(**user_doc.to_dict()) if user_doc.exists else User(balance = amount, admin_password="")
    #         user.balance += amount

    #         if user.balance < 0:
    #             raise NegativeBalanceError("Negative balance!")
            
    #         transaction.set(user_ref, asdict(user))

    #     return transaction_operation



