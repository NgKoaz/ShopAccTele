from dataclasses import dataclass


@dataclass
class Category:
    id: str
    name: str
    price: int 
    adding_instruction: str
    avai_products: int
    sold_products: int


