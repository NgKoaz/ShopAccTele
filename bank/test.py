from ocr_scanner import OcrScanner
import cv2
import numpy as np
import os

folder_path = r"D:\telecode\ShopAccXuanHai\bank\test"
filepaths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]


ocr_scanner = OcrScanner()

index = 1
for filepath in filepaths:
    with open(os.path.abspath(filepath), "rb") as f:
        img_bytes = f.read()
        print(ocr_scanner.process_image(img_bytes))

    index += 1


# def test():
#     mb = MBBank(username="0905770857", password="Arigato147!", proxy=None, ocr_class=OcrScanner())
#     today = datetime.today()
#     seven_days_ago = datetime.today() - timedelta(days=7)
#     print(mb.getTransactionAccountHistory(accountNo="0905770857", from_date=seven_days_ago, to_date=today))
