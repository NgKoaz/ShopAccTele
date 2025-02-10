from payos import PayOS, ItemData, PaymentData
from services.ipayment import BasicPaymentInfo
from dotenv import load_dotenv
import os
from payos.type import (
    PaymentData,
    CreatePaymentResult,
    Transaction,
    PaymentLinkInformation,
    WebhookData,
)

load_dotenv()


class PayOsPayment:
     def __init__(self):
          self.payOS = PayOS(
               client_id=os.getenv("PAYOS_CLIENT_ID"), 
               api_key=os.getenv("PAYOS_API_KEY"), 
               checksum_key=os.getenv("PAYOS_CHECK_SUM")
          )

     def create_new_payment(self, order_id, quantity, price) -> BasicPaymentInfo:
          item = ItemData(name=f"Nạp {price} VND", quantity=quantity, price=price)
          paymentData = PaymentData(
               orderCode=order_id, 
               amount=price, 
               description="",
               items=[item], 
               cancelUrl="", 
               returnUrl=""
          )
          result = self.payOS.createPaymentLink(paymentData = paymentData)

          return BasicPaymentInfo(
               bin=result.bin,
               account_number=result.accountNumber, 
               account_name=result.accountName,
               amount=result.amount,
               qr_code=result.qrCode,
               currency=result.currency,
               description=result.description,
               expired_at=result.expiredAt
          )
     
     def cancel_payment(self, order_id) -> PaymentLinkInformation:
          paymentLinkInfo = self.payOS.cancelPaymentLink(orderId=order_id)
          return paymentLinkInfo
          
     def get_payment(self, order_id) -> PaymentLinkInformation:
          paymentLinkInfo = self.payOS.getPaymentLinkInformation(order_id)
          return paymentLinkInfo




