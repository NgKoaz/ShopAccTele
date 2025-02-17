from dependency_injector import containers, providers
from services.database import Database
from database.manager.category_manager import CategoryManager
from database.manager.product_manager import ProductManager
from database.manager.user_manager import UserManager
from database.manager.transaction_manager import TransactionManager

class Container(containers.DeclarativeContainer):
    db = providers.Singleton(Database)
    category_manager = providers.Singleton(CategoryManager, db=db)
    product_manager = providers.Singleton(ProductManager, db=db)
    user_manager = providers.Singleton(UserManager, db=db)
    transaction_manager = providers.Singleton(TransactionManager, db=db)

