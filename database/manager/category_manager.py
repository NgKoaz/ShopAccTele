from services.database import Database
from database.models.category import Category
from database.models.common_data import CommonData
from database.models.product import Product
from dataclasses import asdict


class CategoryManager:
    CATEGORY_COLLECTION = "categories"
    AVAILABLE = "avai"
    SOLD = "sold"
    COMMON_DATA_DOCUMENT = "data/common"


    def __init__(self, db: Database):
        self.firestore = db.get_firestore()

    def get_categories(self) -> dict[Category]:
        query = self.firestore.collection(self.CATEGORY_COLLECTION)
        docs = query.get()
        categories = [Category(**doc.to_dict()) for doc in docs]
        return categories

    def get_category(self, category_id: str) -> Category | None: 
        doc_ref = self.firestore.collection(self.CATEGORY_COLLECTION).document(category_id)
        doc = doc_ref.get()
        if doc.exists:
            return Category(**doc.to_dict())
        return None

    def has_category(self, category_id: str) -> bool:
        doc = self.get_category(category_id)
        return doc is not None

    def total_avai_accounts_in_category(self, category_id: str) -> int:
        doc = self.get_category(category_id)
        if doc:
            category = Category(**doc.to_dict())
            total_avai_products = category.avai_products
            return total_avai_products
        else:
            return 0

    def save_category(self, category_id: str, category: Category):
        category_ref = self.firestore.collection(self.CATEGORY_COLLECTION).document(category_id)
        category_ref.set(asdict(category))

    def transfer_avai_to_sold(self, category_id: str, user_id: str, product_id: str) -> int:
        avai_ref = self.firestore.document("/".join((self.CATEGORY_COLLECTION, category_id, self.AVAILABLE, product_id)))
        doc = avai_ref.get()
        product = Product(**doc.to_dict())
        avai_ref.delete()

        sold_ref = self.firestore.document("/".join((self.CATEGORY_COLLECTION, category_id, self.SOLD, product_id)))
        product.user_id = user_id
        sold_ref.set(asdict(product))

        # Edit category
        category = self.get_category(category_id)
        category.avai_products -= 1
        category.sold_products += 1
        self.save_category(category_id, category)
    
    def add_total_product(self, category_id: str, number: int) -> None:
        category = self.get_category(category_id)
        if category:
            category.avai_products += number
            self.save_category(category_id, category)

    def get_common_data(self) -> CommonData:
        doc_ref = self.firestore.document(self.COMMON_DATA_DOCUMENT)
        doc = doc_ref.get()
        if doc.exists:
            return CommonData(**doc.to_dict())
        else:
            common_data = CommonData()
            doc_ref.set(asdict(common_data))
            return common_data

    def save_common_data(self, common_data: CommonData) -> str:
        doc_ref = self.firestore.document(self.COMMON_DATA_DOCUMENT)
        doc_ref.set(asdict(common_data))

    def generate_category_id(self):
        common_data = self.get_common_data()
        next_category_id = common_data.next_category_id

        common_data.next_category_id += 1
        self.save_common_data(common_data)

        return f"category{next_category_id}"

    def delete_category_transaction(self, category_id: str):
        cate_ref = self.firestore.collection(self.CATEGORY_COLLECTION).document(category_id)
        def transaction_operation(transaction):
            transaction.delete(cate_ref)  
            
        transaction = self.firestore.transaction()
        transaction_operation(transaction) 
        transaction.commit()


