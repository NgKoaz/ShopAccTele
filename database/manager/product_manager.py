from database.manager.base_manager import BaseManager
from database.models.product import Product
from database.models.category import Category
from exceptions.product_exceptions import NotEnoughProductsError
from exceptions.category_exceptions import NotFoundCategoryError
import database.manager.category_manager as category_manager
from typing import List, Callable
from dataclasses import asdict



class ProductManager(BaseManager):
    # @staticmethod
    # def get_product(category_id: str, product_id: str, is_sold: False, session) -> Product | None:
    #     product = await ProductManager._db.products.find_one_and_delete(
    #         {'category_id': category_id, 'user_id': -1 if not is_sold else {'$ne': -1}},
    #         session=session
    #     )
    #     products = await cursor.to_list(length=limit, session=session)  
    #     return [Product(product) for product in products]
    
        # product_status = self.SOLD if is_sold else self.AVAILABLE

        # doc_ref = self.firestore.document("/".join((self.CATEGORY_COLLECTION, category_id, product_status, product_id)))
        # doc = doc_ref.get()
        # return Product(**doc.to_dict()) if doc.exists else None

    @staticmethod
    async def get_products(category_id: int, limit: int, is_sold: bool, session) -> List[Product]:
        cursor = ProductManager._db.products.find(
            {'category_id': category_id, 'user_id': -1 if not is_sold else {'$ne': -1}},
            session=session
        )
        products = await cursor.to_list(length=limit, session=session)  
        return [Product(product) for product in products]
    
    @staticmethod
    async def create_product(category_id: int, original_chat_id: int, original_message_id: int, backup_message_id: int, backup_chat_id: int, session) -> int:
        product_id = await category_manager.CategoryManager.generate_product_id(category_id=category_id, session=session)
        new_product = Product(
            id=product_id,
            category_id=category_id,
            original_chat_id=original_chat_id,
            original_message_id=original_message_id,
            backup_message_id=backup_message_id,
            backup_chat_id=backup_chat_id
        )
        await ProductManager._db.products.insert_one(asdict(new_product), session=session)
        category_manager.CategoryManager.inc_num_products(category_id, inc_amount=1, is_sold=False, session=session)
        return product_id

    @staticmethod
    async def buy_products(category_id: int, user_id: int, limit: int, session) -> List[Product]:
        products = await ProductManager.get_products(category_id, limit, False, session=session)
        delete_ids = [product['_id'] for product in products]
        await ProductManager._db.products.update_many({'_id': {'$in': delete_ids}}, {'$set': {'user_id': user_id}}, session=session)
        return products
    
    @staticmethod
    async def delete_product(category_id: int, product_id: int, session) -> Product | None:
        product = await ProductManager._db.products.find_one_and_delete({'id': product_id, 'category_id': category_id}, session=session)
        product = Product(product) if product else None
        if product is not None:
            category_manager.CategoryManager.inc_num_products(category_id=category_id, inc_amount=-1, is_sold=(product.user_id != -1), session=session)
        return product
    
    @staticmethod
    async def delete_products(category_id: int, session) -> List[Product]:
        cursor = ProductManager._db.products.find({'category_id': category_id}, session=session)
        products = await cursor.to_list(session=session)
        products = [Product(product) for product in products]
        delete_ids = [product._id for product in products]
        await ProductManager._db.products.delete_many({'_id': {'$in': delete_ids}}, session=session)
        return products


    