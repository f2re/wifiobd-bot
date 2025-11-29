"""
YooKassa Payment Service
"""
from typing import Optional, Dict, Any
from decimal import Decimal
import uuid

from yookassa import Configuration, Payment
from yookassa.domain.notification import WebhookNotification

from config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class YooKassaService:
    """YooKassa payment integration service"""

    def __init__(self):
        """Initialize YooKassa configuration"""
        Configuration.account_id = settings.YOOKASSA_SHOP_ID
        Configuration.secret_key = settings.YOOKASSA_SECRET_KEY
        logger.info("YooKassa configuration initialized")

    async def create_payment(
        self,
        amount: Decimal,
        description: str,
        return_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Create payment in YooKassa"""
        try:
            idempotence_key = str(uuid.uuid4())
            
            payment_data = {
                "amount": {
                    "value": str(amount),
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": return_url or settings.OPENCART_URL
                },
                "capture": True,
                "description": description[:128],  # YooKassa limit
            }

            if metadata:
                payment_data["metadata"] = metadata

            payment = Payment.create(payment_data, idempotence_key)

            logger.info(f"Payment created: {payment.id}, amount: {amount}")

            return {
                "id": payment.id,
                "status": payment.status,
                "amount": float(payment.amount.value),
                "currency": payment.amount.currency,
                "confirmation_url": payment.confirmation.confirmation_url,
                "created_at": payment.created_at.isoformat() if payment.created_at else None,
                "description": payment.description,
                "metadata": payment.metadata
            }

        except Exception as e:
            logger.error(f"Error creating payment: {e}", exc_info=True)
            return None

    async def check_payment_status(self, payment_id: str) -> Optional[str]:
        """Check payment status by ID"""
        try:
            payment = Payment.find_one(payment_id)
            
            if payment:
                logger.info(f"Payment {payment_id} status: {payment.status}")
                return payment.status
            
            return None

        except Exception as e:
            logger.error(f"Error checking payment {payment_id}: {e}")
            return None

    async def get_payment_info(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """Get full payment information"""
        try:
            payment = Payment.find_one(payment_id)
            
            if not payment:
                return None

            return {
                "id": payment.id,
                "status": payment.status,
                "amount": float(payment.amount.value),
                "currency": payment.amount.currency,
                "description": payment.description,
                "metadata": payment.metadata,
                "created_at": payment.created_at.isoformat() if payment.created_at else None,
                "paid": payment.paid,
                "refundable": payment.refundable,
                "test": payment.test
            }

        except Exception as e:
            logger.error(f"Error getting payment info {payment_id}: {e}")
            return None

    async def cancel_payment(self, payment_id: str) -> bool:
        """Cancel payment"""
        try:
            payment = Payment.find_one(payment_id)
            
            if payment and payment.status == "waiting_for_capture":
                Payment.cancel(payment_id)
                logger.info(f"Payment {payment_id} cancelled")
                return True
            
            return False

        except Exception as e:
            logger.error(f"Error cancelling payment {payment_id}: {e}")
            return False

    async def process_webhook(
        self,
        request_body: str,
        notification_type: str
    ) -> Optional[Dict[str, Any]]:
        """Process webhook notification from YooKassa"""
        try:
            notification = WebhookNotification(request_body)
            payment = notification.object

            result = {
                "type": notification_type,
                "event": notification.event,
                "payment_id": payment.id,
                "status": payment.status,
                "amount": float(payment.amount.value),
                "metadata": payment.metadata,
                "paid": payment.paid
            }

            logger.info(
                f"Webhook processed: {notification.event}, "
                f"payment {payment.id}, status {payment.status}"
            )

            return result

        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            return None

    async def create_refund(
        self,
        payment_id: str,
        amount: Decimal,
        reason: Optional[str] = None
    ) -> Optional[str]:
        """Create refund for payment"""
        try:
            from yookassa import Refund
            
            idempotence_key = str(uuid.uuid4())
            
            refund_data = {
                "payment_id": payment_id,
                "amount": {
                    "value": str(amount),
                    "currency": "RUB"
                }
            }

            if reason:
                refund_data["description"] = reason[:250]

            refund = Refund.create(refund_data, idempotence_key)
            
            logger.info(f"Refund created: {refund.id} for payment {payment_id}")
            
            return refund.id

        except Exception as e:
            logger.error(f"Error creating refund for {payment_id}: {e}")
            return None


# Create global instance
yookassa_service = YooKassaService()
