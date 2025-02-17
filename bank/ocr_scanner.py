from mbbank import CapchaProcessing
import cv2
from PIL import Image
import easyocr
import numpy as np


class OcrScanner(CapchaProcessing):
    def __init__(self):
        super().__init__()
        self.reader = easyocr.Reader(['en'])  # Initialize EasyOCR for English

    def keep_black_remove_others(self, image_bytes: bytes) -> bytes:
        # Convert the byte data to a numpy array
        np_arr = np.frombuffer(image_bytes, np.uint8)
        
        # Decode the image from the byte array
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # Convert the image to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Define the range for black color (or near black)
        lower_black = np.array([0, 0, 0])
        upper_black = np.array([180, 255, 80])

        # Create mask to keep black
        mask = cv2.inRange(hsv, lower_black, upper_black)

        # Create the result image (keep black, set others to white)
        result = np.full_like(image, 255)  # Create a white image
        result[mask > 0] = image[mask > 0]  # Keep black pixels

        # Encode the result to byte data again
        _, img_encoded = cv2.imencode('.jpg', result)
        img_bytes = img_encoded.tobytes()

        return img_bytes

    def process_image(self, img: bytes) -> str:
        img = self.keep_black_remove_others(img)

        # Convert bytes to numpy array
        np_img = np.frombuffer(img, np.uint8)

        # Decode image
        image = cv2.imdecode(np_img, cv2.IMREAD_GRAYSCALE)

        # Preprocess image (optional: denoising, thresholding)
        _, thresh = cv2.threshold(image, 128, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # OCR recognition
        result = self.reader.readtext(thresh, detail=0)

        return str("".join(result)).replace(" ", "")
