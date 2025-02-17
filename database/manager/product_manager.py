
from services.database import Database
from database.models.product import Product
from dataclasses import asdict
import services.container as container


class ProductManager:
    CATEGORY_COLLECTION = "categories"
    AVAILABLE = "avai"
    SOLD = "sold"

    def __init__(self, db: Database):
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

    def generate_product_id(self, category_id: str) -> str:
        category_manager = container.Container.category_manager()
        category = category_manager.get_category(category_id)
        if category is None:
            raise Exception("Category ID is not found!")
        next_product_id = category.next_product_id
        category.next_product_id += 1
        category_manager.save_category(category_id, category)
        return "product" + str(next_product_id)
    
