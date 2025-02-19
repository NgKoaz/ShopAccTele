from database.models.category import Category
from database.models.product import Product
from database.manager.base_manager import BaseManager
from database.manager.common_manager import CommonManager
from functools import partial
from dataclasses import asdict
from typing import List


class CategoryManager(BaseManager):
    _instance = None

    @staticmethod
    def get_ins():
        if CategoryManager._instance is None:
            CategoryManager._instance = CategoryManager()
        return CategoryManager._instance

    @staticmethod
    async def get_categories() -> List[Category]:
        cursor = CategoryManager._db.categories.find()
        categories = [Category(category) for category in await cursor.to_list()]
        return categories
    
    @staticmethod
    async def get_category(id: str, session=None) -> Category | None:
        category = await CategoryManager._db.categories.find_one({"id": id}, session=session)
        return Category(category) if category else None
    
    @staticmethod
    async def create_category(category: Category):
        result = CategoryManager.exec_transactions([CommonManager.generate_category_id])
        category.id = result[0]
        await CategoryManager._db.categories.insert_one(asdict(category))

    @staticmethod
    async def generate_product_id(category_id: int, session) -> int:
        category = await CategoryManager.get_category(category_id, session=session)
        if category is None:
            raise Exception("Category ID is not found!")
        
        new_product_id = category.next_product_id
        await CategoryManager._db.categories.update_one({"id": category_id}, {"$inc": {"next_product_id": 1}}, session=session)
        return new_product_id

    @staticmethod
    async def inc_num_products(category_id: int, inc_amount: int, is_sold: bool, session):
        """ Only add with number of available products """
        if is_sold:
            return
        await CategoryManager._db.categories.update_one(
            {'id': category_id}, 
            {'$inc': { 'num_avai_products' : inc_amount }}, 
            session=session
        )

    @staticmethod
    async def delete_category(category_id: str, session) -> Category | None:
        category = await CategoryManager._db.categories.find_one_and_delete({'id': category_id}, session=session)
        return Category(category) if category else None

