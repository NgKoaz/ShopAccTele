from database.manager.base_manager import BaseManager
from exceptions.bank_exception import NotFoundBankError
from database.models.setting import Setting
from dataclasses import asdict


class CommonManager(BaseManager):
    @staticmethod
    async def get_bank_name(bin: int) -> str:
        """
            Args:
                bin: A bin code of a bank

            Returns:
                bank: Bank's name
            
            Raise:
                NotFoundBankError: The bank is not found
        """
        bank = await CommonManager._db.banks.find_one({"bin": bin})
        if bank:
            return bank.get("name")
        else:
            raise NotFoundBankError("The bin code you passed have not found, please double-check in your database!")

    @staticmethod
    async def get_setting(session=None) -> Setting:
        setting = await CommonManager._db.settings.find_one({}, session=session)
        if setting:
            return Setting(setting)
        else:
            setting = Setting()
            await CommonManager._db.settings.insert_one(asdict(setting), session=session)
            return setting
    
    @staticmethod
    async def update_storage_chat_id(new_storage_chat_id: int):
        setting = await CommonManager.get_setting()
        await CommonManager._db.settings.update_one({'_id': setting._id}, {'$set': {'storage_chat_id': new_storage_chat_id}})

    @staticmethod
    async def generate_category_id(session) -> int:
        setting = await CommonManager.get_setting(session=session)
        new_category_id = setting.next_category_id
        await CommonManager._db.settings.update_one(
            {"$inc": {"next_category_id": 1}}  
        )
        return new_category_id
    
    # @staticmethod
    # async def update_setting(setting: Setting, session=None):
    #     if not setting._id:
    #         raise Exception("Setting object doesn't have _id for updating!")

    #     await CommonManager._db.settings.update_one(
    #         {"_id": setting._id},  
    #         {"$set": {  
    #             "password": setting.password,
    #             "storage_group_id": setting.storage_chat_id,
    #             "next_category_id": setting.next_category_id
    #         }},
    #         session=session
    #     )