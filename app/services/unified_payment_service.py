from app.extensions import db
from app.models.booking_payment import Booking, Payment
from app.payment_stripe.views.views import StripeService
from app.services.payment_servicesmpesa import process_payment as mpesa_process
from decimal import Decimal

class UnifiedPaymentService:
    @staticmethod
    def initiate_payment(booking_id, provider, user_id, amount, **kwargs):
        """
        Initiates a payment for a booking using the specified provider.
        """
        booking = Booking.query.get(booking_id)
        if not booking:
            raise ValueError("Booking not found")

        if provider == "stripe":
            # Stripe amount is in cents
            stripe_amount = int(amount * 100)
            intent = StripeService.create_payment_intent(
                user_id=user_id,
                amount=stripe_amount,
                currency=kwargs.get("currency", "usd"),
                metadata={"booking_id": str(booking_id)}
            )
            
            # Record in unified Payment table
            payment = Payment(
                booking_id=booking_id,
                amount=amount,
                status="pending",
                transaction_id=intent.id,
                provider="stripe"
            )
            db.session.add(payment)
            db.session.commit()
            return {"clientSecret": intent.client_secret, "paymentIntentId": intent.id}

        elif provider == "mpesa":
            phone_number = kwargs.get("phone_number")
            if not phone_number:
                raise ValueError("Phone number required for M-Pesa")

            result = mpesa_process({
                "user_id": user_id,
                "amount": amount,
                "phone_number": phone_number,
                "reference": booking.reference_number
            })

            # Record in unified Payment table
            payment = Payment(
                booking_id=booking_id,
                amount=amount,
                status="pending",
                transaction_id=result["checkout_request_id"],
                provider="mpesa"
            )
            db.session.add(payment)
            db.session.commit()
            return result

        else:
            raise ValueError(f"Unsupported payment provider: {provider}")

    @staticmethod
    def update_payment_status(transaction_id, status, provider, raw_response=None):
        """
        Updates the unified payment and booking status.
        """
        payment = Payment.query.filter_by(transaction_id=transaction_id, provider=provider).first()
        if not payment:
            return None

        payment.status = status
        if raw_response:
            payment.raw_response = raw_response

        # If payment succeeded, update booking status
        if status == "succeeded" or status == "success":
            booking = Booking.query.get(payment.booking_id)
            if booking:
                booking.status = "confirmed"
        
        db.session.commit()
        return payment
