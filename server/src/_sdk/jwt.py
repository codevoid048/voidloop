"""
JWT Utilities for Tracker Backend

Provides convenient utilities for JWT token management using django-ninja-jwt.
Handles token generation, validation, refresh, and user authentication.
"""

from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.conf import settings
from ninja_jwt.tokens import RefreshToken
from ninja_jwt.exceptions import TokenError, InvalidToken
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.settings import api_settings

from .exceptions import (
    AuthenticationRequiredException,
    TokenInvalidException,
    TokenExpiredException,
)

User = get_user_model()


class JWTService:
    """
    Service class for JWT operations.
    Provides high-level methods for token management and user authentication.
    """

    @staticmethod
    def generate_tokens_for_user(user: User) -> Dict[str, str]:
        """
        Generate access and refresh tokens for a user.

        Args:
            user: User instance to generate tokens for

        Returns:
            Dictionary with 'access' and 'refresh' tokens

        Example:
            tokens = JWTService.generate_tokens_for_user(user)
            # Returns: {'access': 'eyJ0eXAi...', 'refresh': 'eyJ0eXAi...'}
        """
        refresh = RefreshToken.for_user(user)

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

    @staticmethod
    def decode_access_token(token: str) -> Dict[str, Any]:
        """
        Decode and validate an access token.

        Args:
            token: JWT access token string

        Returns:
            Decoded token payload

        Raises:
            TokenInvalidException: If token is invalid or malformed
            TokenExpiredException: If token is expired
        """
        try:
            # Use ninja_jwt's built-in token validation
            from ninja_jwt.tokens import UntypedToken

            # Validate token structure and signature
            untyped_token = UntypedToken(token)

            # Get the payload
            payload = untyped_token.payload

            # Check if token is expired
            if (
                payload.get("exp")
                and datetime.fromtimestamp(payload["exp"]) < datetime.now()
            ):
                raise TokenExpiredException()

            return payload

        except TokenError as e:
            if "expired" in str(e).lower():
                raise TokenExpiredException()
            raise TokenInvalidException(message=str(e))
        except Exception as e:
            raise TokenInvalidException(message=f"Token validation failed: {str(e)}")

    @staticmethod
    def refresh_access_token(refresh_token: str) -> Dict[str, str]:
        """
        Generate a new access token using a refresh token.

        Args:
            refresh_token: JWT refresh token string

        Returns:
            Dictionary with new 'access' token and same 'refresh' token

        Raises:
            TokenInvalidException: If refresh token is invalid
            TokenExpiredException: If refresh token is expired
        """
        try:
            refresh = RefreshToken(refresh_token)

            token_jti = str(refresh.get("jti") or "")
            if token_jti and cache.get(f"jwt:blacklisted:{token_jti}"):
                raise TokenInvalidException(message="Refresh token has been revoked")

            return {
                "access": str(refresh.access_token),
                "refresh": refresh_token,  # Keep same refresh token
            }

        except TokenError as e:
            if "expired" in str(e).lower():
                raise TokenExpiredException()
            raise TokenInvalidException(message=f"Invalid refresh token: {str(e)}")

    @staticmethod
    def get_user_from_token(token: str) -> Optional[User]:
        """
        Get user instance from JWT access token.

        Args:
            token: JWT access token string

        Returns:
            User instance if token is valid, None if user doesn't exist

        Raises:
            TokenInvalidException: If token is invalid
            TokenExpiredException: If token is expired
        """
        try:
            payload = JWTService.decode_access_token(token)
            user_id = payload.get("user_id")

            if not user_id:
                raise TokenInvalidException(message="Token missing user_id")

            try:
                user = User.objects.get(id=user_id)
                return user
            except User.DoesNotExist:
                return None

        except (TokenInvalidException, TokenExpiredException):
            raise

    @staticmethod
    def blacklist_token(refresh_token: str) -> bool:
        """
        Blacklist a refresh token (logout functionality).

        Args:
            refresh_token: JWT refresh token string

        Returns:
            True if successfully blacklisted

        Raises:
            TokenInvalidException: If token is invalid
        """
        try:
            token = RefreshToken(refresh_token)
            token_jti = str(token.get("jti") or "")
            expires_at = token.get("exp")

            if token_jti and expires_at:
                ttl = max(1, int(datetime.fromtimestamp(expires_at).timestamp() - datetime.now().timestamp()))
                cache.set(f"jwt:blacklisted:{token_jti}", True, timeout=ttl)

            token.blacklist()
            return True

        except TokenError as e:
            raise TokenInvalidException(message=f"Cannot blacklist token: {str(e)}")

    @staticmethod
    def get_token_expiry(token: str) -> Optional[datetime]:
        """
        Get expiry datetime from a token.

        Args:
            token: JWT token string

        Returns:
            Expiry datetime or None if not found
        """
        try:
            payload = JWTService.decode_access_token(token)
            exp_timestamp = payload.get("exp")

            if exp_timestamp:
                return datetime.fromtimestamp(exp_timestamp)
            return None

        except:
            return None


class JWTAuthBackend(JWTAuth):
    """
    Custom JWT authentication backend for Django Ninja.
    Extends ninja_jwt.JWTAuth with custom exception handling.
    """

    def authenticate(self, request, token: str) -> Optional[User]:
        """
        Authenticate user from JWT token.

        Args:
            request: Django request object
            token: JWT token string

        Returns:
            User instance if authenticated successfully

        Raises:
            AuthenticationRequiredException: If authentication fails
        """
        try:
            user = JWTService.get_user_from_token(token)

            if not user:
                raise AuthenticationRequiredException(message="User not found")

            if not user.is_active:
                raise AuthenticationRequiredException(
                    message="User account is disabled"
                )

            return user

        except (TokenInvalidException, TokenExpiredException) as e:
            raise AuthenticationRequiredException(message=str(e))
        except Exception as e:
            raise AuthenticationRequiredException(
                message=f"Authentication failed: {str(e)}"
            )


# Utility functions for convenience
def generate_tokens(user: User) -> Dict[str, str]:
    """Convenience function for generating tokens."""
    return JWTService.generate_tokens_for_user(user)


def decode_token(token: str) -> Dict[str, Any]:
    """Convenience function for decoding tokens."""
    return JWTService.decode_access_token(token)


def refresh_token(refresh_token: str) -> Dict[str, str]:
    """Convenience function for refreshing tokens."""
    return JWTService.refresh_access_token(refresh_token)


def get_user_from_jwt(token: str) -> Optional[User]:
    """Convenience function for getting user from token."""
    return JWTService.get_user_from_token(token)


def logout_user(refresh_token: str) -> bool:
    """Convenience function for logging out user."""
    return JWTService.blacklist_token(refresh_token)


# JWT Configuration Helper
def get_jwt_settings() -> Dict[str, Any]:
    """
    Get current JWT settings configuration.

    Returns:
        Dictionary of JWT settings
    """
    return {
        "access_token_lifetime": api_settings.ACCESS_TOKEN_LIFETIME,
        "refresh_token_lifetime": api_settings.REFRESH_TOKEN_LIFETIME,
        "algorithm": api_settings.ALGORITHM,
        "signing_key": api_settings.SIGNING_KEY,
        "rotate_refresh_tokens": api_settings.ROTATE_REFRESH_TOKENS,
        "blacklist_after_rotation": api_settings.BLACKLIST_AFTER_ROTATION,
    }
