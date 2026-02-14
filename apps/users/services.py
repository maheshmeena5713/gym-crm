"""
OTP Service - Handles OTP generation, sending, and verification.
Supports bypass mode for development (OTP_BYPASS=True → always 123456).
Twilio configured but gated behind OTP_BYPASS=False.
"""

import logging
import random
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.users.models import OTPSession, GymUser

logger = logging.getLogger('apps.users')


class OTPService:
    """Service for managing OTP lifecycle."""

    MAX_ATTEMPTS = 5
    RATE_LIMIT_SECONDS = 60  # Min gap between OTP requests for same phone

    @staticmethod
    def _generate_otp():
        """Generate a 6-digit OTP. Returns bypass code if OTP_BYPASS is True."""
        if settings.OTP_BYPASS:
            return settings.OTP_DEFAULT_CODE
        return str(random.randint(100000, 999999))

    @staticmethod
    def _send_via_twilio(phone, otp_code):
        """
        Send OTP via Twilio SMS.
        Only called when OTP_BYPASS is False.
        """
        try:
            from twilio.rest import Client

            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            message = client.messages.create(
                body=f"Your GymAI verification code is: {otp_code}. Valid for {settings.OTP_EXPIRY_MINUTES} minutes.",
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone,
            )
            logger.info(f"Twilio SMS sent to {phone}, SID: {message.sid}")
            return True
        except Exception as e:
            logger.error(f"Twilio SMS failed for {phone}: {str(e)}")
            return False

    @classmethod
    def send_otp(cls, phone):
        """
        Generate and send OTP to phone number.
        Returns (success: bool, message: str).
        """
        # Rate limiting: check if OTP was sent recently
        recent_otp = OTPSession.objects.filter(
            phone=phone,
            is_verified=False,
            created_at__gte=timezone.now() - timedelta(seconds=cls.RATE_LIMIT_SECONDS),
        ).first()

        if recent_otp:
            return False, "OTP already sent. Please wait before requesting again."

        # Invalidate any previous unused OTPs for this phone
        OTPSession.objects.filter(phone=phone, is_verified=False).delete()

        # Generate OTP
        otp_code = cls._generate_otp()

        # Create OTP session
        otp_session = OTPSession.objects.create(
            phone=phone,
            otp_code=otp_code,
            expires_at=timezone.now() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES),
        )

        # Send OTP (skip if bypass mode)
        if not settings.OTP_BYPASS:
            sent = cls._send_via_twilio(phone, otp_code)
            if not sent:
                otp_session.delete()
                return False, "Failed to send OTP. Please try again."

        if settings.OTP_BYPASS:
            logger.info(f"[OTP BYPASS] Code for {phone}: {otp_code}")

        return True, "OTP sent successfully."

    @classmethod
    def verify_otp(cls, phone, otp_code):
        """
        Verify OTP and return the user (create if new).
        Returns (success: bool, data: dict or str).
        """
        otp_session = OTPSession.objects.filter(
            phone=phone,
            is_verified=False,
        ).order_by('-created_at').first()

        if not otp_session:
            return False, "No OTP found for this number. Please request a new one."

        # Check expiry
        if otp_session.is_expired:
            otp_session.delete()
            return False, "OTP has expired. Please request a new one."

        # Check max attempts
        if otp_session.attempts >= cls.MAX_ATTEMPTS:
            otp_session.delete()
            return False, "Too many failed attempts. Please request a new OTP."

        # Verify code
        if otp_session.otp_code != otp_code:
            otp_session.attempts += 1
            otp_session.save(update_fields=['attempts'])
            remaining = cls.MAX_ATTEMPTS - otp_session.attempts
            return False, f"Invalid OTP. {remaining} attempt(s) remaining."

        # Mark as verified
        otp_session.is_verified = True
        otp_session.save(update_fields=['is_verified'])

        # Get or create user
        user, created = GymUser.objects.get_or_create(
            phone=phone,
            defaults={
                'name': f'User {phone[-4:]}',
                'role': GymUser.Role.OWNER,
            },
        )

        # Update last login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        return True, {'user': user, 'is_new_user': created}
