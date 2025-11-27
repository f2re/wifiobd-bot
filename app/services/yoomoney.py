"""
YooMoney payment integration service
"""
import time
from typing import Dict, Optional
from yoomoney import Client, Quickpay
from config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class YooMoneyService:
    """Service for YooMoney payment processing"""

    def __init__(self):
        self.token = settings.YOOMONEY_TOKEN
        self.wallet = settings.YOOMONEY_WALLET
        self.client = None

        if self.token:
            try:
                self.client = Client(self.token)
                logger.info("YooMoney client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize YooMoney client: {e}")

    def create_payment(self, order_id: int, amount: float) -> Dict[str, str]:
        """
        Create payment form for order

        Args:
            order_id: Order ID in bot's database
            amount: Payment amount in rubles

        Returns:
            Dict with payment_url and label
        """
        try:
            # Create unique label for this payment
            label = f"order_{order_id}_{int(time.time())}"

            # Create Quickpay form
            quickpay = Quickpay(
                receiver=self.wallet,
                quickpay_form="shop",
                targets=f"Оплата заказа #{order_id} в магазине wifiobd.ru",
                paymentType="SB",  # Payment from any bank card
                sum=amount,
                label=label
            )

            payment_url = quickpay.redirected_url

            logger.info(f"Created payment for order {order_id}: {label}")

            return {
                "payment_url": payment_url,
                "label": label
            }

        except Exception as e:
            logger.error(f"Failed to create payment: {e}")
            raise

    def check_payment(self, label: str) -> Dict[str, any]:
        """
        Check payment status by label

        Args:
            label: Payment label

        Returns:
            Dict with status, amount, datetime
        """
        if not self.client:
            logger.error("YooMoney client not initialized")
            return {"status": "error", "message": "Payment service not configured"}

        try:
            # Get operation history filtered by label
            history = self.client.operation_history(label=label)

            if history.operations:
                # Check for successful payment
                for operation in history.operations:
                    if operation.status == "success" and operation.label == label:
                        logger.info(f"Payment confirmed: {label} - {operation.amount} RUB")

                        return {
                            "status": "success",
                            "amount": float(operation.amount),
                            "datetime": operation.datetime,
                            "operation_id": operation.operation_id,
                            "sender": getattr(operation, "sender", None)
                        }

            # Payment not found or not successful yet
            return {"status": "pending"}

        except Exception as e:
            logger.error(f"Failed to check payment: {e}")
            return {"status": "error", "message": str(e)}

    def get_account_info(self) -> Optional[Dict]:
        """Get YooMoney account information"""
        if not self.client:
            return None

        try:
            account_info = self.client.account_info()
            return {
                "account": account_info.account,
                "balance": float(account_info.balance),
                "currency": account_info.currency
            }
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            return None

    def create_refund_payment(self, amount: float, recipient: str, comment: str = "") -> Dict:
        """
        Create a refund payment (requires additional YooMoney permissions)

        Args:
            amount: Refund amount
            recipient: Recipient wallet/card
            comment: Payment comment

        Returns:
            Dict with operation details
        """
        if not self.client:
            raise Exception("YooMoney client not initialized")

        try:
            # Note: This requires payment-p2p permission
            payment = self.client.send(
                to=recipient,
                amount=amount,
                comment=comment
            )

            logger.info(f"Refund created: {amount} RUB to {recipient}")

            return {
                "status": "success",
                "operation_id": payment.operation_id
            }

        except Exception as e:
            logger.error(f"Failed to create refund: {e}")
            raise


# Singleton instance
yoomoney_service = YooMoneyService()
