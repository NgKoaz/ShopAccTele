import json
import os 


class LocalStorage:
    ORDER_ID_START = 100
    LOCAL_STORAGE_DIR = "local/temp.json"

    @staticmethod
    def load_json() -> dict:
        try:
            with open(LocalStorage.LOCAL_STORAGE_DIR, "r", encoding="utf-8") as file:
                data = json.load(file)
            return data
        except FileNotFoundError:
            return {}

    @staticmethod
    def save_json(data: dict) -> None:
        with open(LocalStorage.LOCAL_STORAGE_DIR, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    @staticmethod
    def generate_new_order_id():
        data = LocalStorage.load_json()
        new_order_id = data.get("new_order_id", LocalStorage.ORDER_ID_START)
        data["new_order_id"] = new_order_id + 1  
        LocalStorage.save_json(data)
        return new_order_id
    
