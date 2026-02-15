"""
Users Views - OTP authentication endpoints.
"""

import logging

from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema

from apps.users.serializers import (
    SendOTPSerializer,
    VerifyOTPSerializer,
    AuthTokenSerializer,
    UserProfileSerializer,
    OTPResponseSerializer,
    SelectAccountSerializer,
)
from apps.users.services import OTPService

logger = logging.getLogger('apps.users')


class SendOTPView(APIView):
    """
    Send OTP to phone number.

    POST /api/v1/auth/send-otp/
    Body: {"phone": "9876543210"}
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=['Auth'],
        request=SendOTPSerializer,
        responses={200: OTPResponseSerializer},
        summary="Send OTP",
        description="Send a 6-digit OTP to the given phone number. "
                    "In development (OTP_BYPASS=True), the OTP is always 123456.",
    )
    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data['phone']
        success, message = OTPService.send_otp(phone)

        return Response(
            {'success': success, 'message': message},
            status=status.HTTP_200_OK if success else status.HTTP_429_TOO_MANY_REQUESTS,
        )


class VerifyOTPView(APIView):
    """
    Verify OTP and get JWT tokens.

    POST /api/v1/auth/verify-otp/
    Body: {"phone": "9876543210", "otp": "123456"}
    Returns: {"access": "...", "refresh": "...", "is_new_user": true, "user": {...}}
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=['Auth'],
        request=VerifyOTPSerializer,
        responses={200: AuthTokenSerializer},
        summary="Verify OTP & Get Token",
        description="Verify the OTP code and receive JWT access/refresh tokens. "
                    "If the user doesn't exist, a new account is created automatically.",
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        phone = serializer.validated_data['phone']
        otp_code = serializer.validated_data['otp']

        success, result = OTPService.verify_otp(phone, otp_code)

        if not success:
            return Response(
                {'success': False, 'message': result},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Helper to generate token response
        def get_auth_response(user, is_new=False):
            refresh = RefreshToken.for_user(user)
            return {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'is_new_user': is_new,
                'user': UserProfileSerializer(user).data,
                'is_multi_account': False
            }

        # Handle Multi-Account Scenario
        if isinstance(result, dict) and result.get('is_multi_account'):
            from apps.users.serializers import AccountListSerializer
            # Generate a temporary selection token (e.g., signed phone number)
            # For simplicity, we'll use a signed JWT with short expiry containing the phone
            selection_token = RefreshToken().for_user(result['accounts'][0]) # Dummy user for signing
            selection_token.payload['phone_verification'] = result['phone']
            selection_token.set_exp(lifetime=timedelta(minutes=5))

            return Response({
                'is_multi_account': True,
                'accounts': AccountListSerializer(result['accounts'], many=True).data,
                'selection_token': str(selection_token),
                'message': 'Multiple accounts found. Please select one.'
            })

        # Single Account Scenario
        return Response(get_auth_response(result['user'], result['is_new_user']))


class SelectAccountView(APIView):
    """
    Finalize login by selecting a specific account.
    POST /api/v1/auth/select-account/
    Body: {"account_id": "uuid", "selection_token": "jwt"}
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=['Auth'],
        request=SelectAccountSerializer,
        responses={200: AuthTokenSerializer},
        summary="Select Account",
        description="Complete login by selecting a specific account from the list."
    )
    def post(self, request):
        serializer = SelectAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['selection_token']
        account_id = serializer.validated_data['account_id']

        # Verify token
        try:
            from rest_framework_simplejwt.tokens import UntypedToken
            decoded = UntypedToken(token)
            phone = decoded.get('phone_verification')
            if not phone:
                raise Exception("Invalid token scope")
        except Exception:
            return Response(
                {'success': False, 'message': 'Invalid or expired selection session.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Verify account belongs to phone
        from apps.users.models import GymUser
        user = GymUser.objects.filter(id=account_id, phone=phone).first()

        if not user:
            return Response(
                {'success': False, 'message': 'Invalid account selection.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Generate final tokens
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'is_new_user': False,
            'user': UserProfileSerializer(user).data,
        })


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update the authenticated user's profile.

    GET /api/v1/auth/profile/
    PUT /api/v1/auth/profile/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    @extend_schema(tags=['Auth'], summary="Get My Profile")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(tags=['Auth'], summary="Update My Profile")
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(tags=['Auth'], summary="Partial Update My Profile")
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def get_object(self):
        return self.request.user
