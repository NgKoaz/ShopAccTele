from dataclasses import dataclass


@dataclass
class Category:
    id: str = ""
    name: str = ""
    price: int = 9999999999
    adding_instruction: str = ""
    avai_products: int = 0
    sold_products: int = 0
    next_product_id: int = 0