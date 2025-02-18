
from services.database import Database
from database.models.product import Product
from database.models.category import Category
from dataclasses import asdict
import services.container as container
from firebase_admin import firestore
from google.cloud.firestore_v1.transaction import Transaction
from typing import List, Callable
from exceptions.product_exceptions import NotEnoughProductsError
from exceptions.category_exceptions import NotFoundCategoryError


class ProductManager:
    CATEGORY_COLLECTION = "categories"
    AVAILABLE = "avai"
    SOLD = "sold"

    def __init__(self, db: Database):
        self.db = db
        self.firestore = db.get_firestore()

    def get_products(self, category_id: str, limit: int, is_sold=False) -> dict[Product]:
        product_status = self.SOLD if is_sold else self.AVAILABLE

        col_ref = self.firestore.collection("/".join((self.CATEGORY_COLLECTION, category_id, product_status)))
        docs = col_ref.limit(limit).get()
        products = [Product(**doc.to_dict()) for doc in docs]
        return products

    def save_product(self, category_id: str, product: Product):
        col_ref = self.firestore.collection("/".join((self.CATEGORY_COLLECTION, category_id, self.AVAILABLE)))
        doc_ref = col_ref.document(product.id)
        doc_ref.set(asdict(product))

    def get_product(self, category_id: str, product_id: str, is_sold=False) -> Product | None:
        product_status = self.SOLD if is_sold else self.AVAILABLE

        doc_ref = self.firestore.document("/".join((self.CATEGORY_COLLECTION, category_id, product_status, product_id)))
        doc = doc_ref.get()
        return Product(**doc.to_dict()) if doc.exists else None

    def delete_product(self, category_id: str, product_id: str):
        category_manager = container.Container.category_manager()
        doc_ref = self.firestore.document("/".join((self.CATEGORY_COLLECTION, category_id, self.AVAILABLE, product_id)))
        doc_ref.delete()
        category_manager.add_total_product(category_id, -1)


    def pop_products_transaction(self, category_id: str) -> List[Product]:
        def transaction_operation(transaction, category_id):
            avai_products_ref = self.firestore.collection("/".join([self.CATEGORY_COLLECTION, category_id, self.AVAILABLE]))

            # Use a query to fetch the documents
            avai_products_query = avai_products_ref.stream() 
            products = []

            # Loop through the products in the query result
            for product_doc in avai_products_query:
                product_ref = self.firestore.document("/".join([self.CATEGORY_COLLECTION, category_id, self.AVAILABLE, product_doc.id]))
                transaction.delete(product_ref)
                products.append(Product(**product_doc.to_dict()))
            return products
        
        transaction = self.firestore.transaction()
        products = transaction_operation(transaction, category_id) 
        transaction.commit()
        return products


    def generate_product_id(self, category_id: str) -> str:
        category_manager = container.Container.category_manager()
        category = category_manager.get_category(category_id)
        if category is None:
            raise Exception("Category ID is not found!")
        next_product_id = category.next_product_id
        category.next_product_id += 1
        category_manager.save_category(category_id, category)
        return "product" + str(next_product_id)
    
   
    def buy_products_transaction(self, category_id: str, user_id: int, limit: int) -> Callable[[Transaction], None]:
        """
            Raise: NotEnoughProductsError
            Raise: NotFoundCategoryError
        """
        cate_doc_ref = self.db.document(self.CATEGORY_COLLECTION, category_id)
        avai_col_ref = self.db.collection(self.CATEGORY_COLLECTION, category_id, self.AVAILABLE)
        sold_col_ref = self.db.collection(self.CATEGORY_COLLECTION, category_id, self.SOLD)

        async def transaction_operation(transaction: Transaction) -> None:
            cate_doc = await cate_doc_ref.get(transaction=transaction)
            if cate_doc.exists:
                category = Category(**cate_doc.to_dict())
                if category.avai_products < limit:
                    raise NotEnoughProductsError(f"Not enough products to move. Available: {category.avai_products}, Required: {limit}")
                else:
                    category.avai_products -= limit
                    transaction.update(cate_doc_ref, {'avai_products': category.avai_products})
            else:
                raise NotFoundCategoryError(f"Category is not found!")

            products_query = avai_col_ref.stream(transaction=transaction)
            count = 0
            async for product_doc in products_query:
                if count >= limit:
                    break  
                product = Product(**product_doc.to_dict())
                product.user_id = user_id

                # Set the product data in the target category (moving the product)
                transaction.set(sold_col_ref.document(product_doc.id), asdict(product))

                # Delete the product from the source category
                transaction.delete(product_doc.reference)

                count += 1
            return
        return transaction_operation
    