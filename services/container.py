from dependency_injector import containers, providers
from services.database import Database
from services.payos_payment import PayOsPayment

class Container(containers.DeclarativeContainer):
    # Services
    db = providers.Singleton(Database)
    payos = providers.Singleton(PayOsPayment)

