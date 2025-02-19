from typing import Callable, Any, List
from motor.motor_asyncio import AsyncIOMotorClient



class BaseManager:
    _client = AsyncIOMotorClient("mongodb://localhost:27017")
    _db = _client["teleapp"]
    
    @staticmethod
    def get_db():
        return BaseManager._db

    @staticmethod
    async def exec_transactions(transactions: Callable[[Any], Any]) -> List[Any]:
        # Start a session to begin a transaction
        async with BaseManager._db.client.start_session() as session:
            # Start the transaction
            async with session.start_transaction():
                # Update bank document
                results = [await transaction(session=session) for transaction in transactions]
                return results

