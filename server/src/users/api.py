from typing import Any, Dict
from django.contrib.auth import get_user_model, authenticate
from ninja import Router
from _sdk.decorators import require_auth
from _sdk.jwt import generate_tokens, JWTService
from _sdk.exceptions import AuthenticationRequiredException, ValidationException
from users.schemas import (
    RegisterRequestSchema,
    LoginRequestSchema,
    RefreshTokenRequestSchema,
    TokenResponseSchema,
    UserResponseSchema,
)

User = get_user_model()
auth_router = Router(tags=["Authentication"])


@auth_router.post("/register", response={200: TokenResponseSchema})
def register(request, payload: RegisterRequestSchema):
    """
    Register a new user and generate JWT auth tokens.
    """
    if User.objects.filter(email=payload.email).exists():
        raise ValidationException(message="A user with this email already exists.")
    if User.objects.filter(username=payload.username).exists():
        raise ValidationException(message="A user with this username already exists.")

    user = User.objects.create_user(
        username=payload.username,
        email=payload.email,
        password=payload.password,
        name=payload.name or "",
    )

    tokens = generate_tokens(user)
    return {
        "access": tokens["access"],
        "refresh": tokens["refresh"],
        "user": user,
    }


@auth_router.post("/login", response={200: TokenResponseSchema})
def login(request, payload: LoginRequestSchema):
    """
    Authenticate user via email or username and return JWT tokens.
    """
    username_or_email = payload.email.strip()
    user = None

    # Try finding user by email first
    if "@" in username_or_email:
        user = User.objects.filter(email=username_or_email).first()

    # Fallback to username search if not found or not email
    if not user:
        user = User.objects.filter(username=username_or_email).first()

    if not user:
        raise AuthenticationRequiredException(message="Invalid credentials")

    # Authenticate using django auth
    authenticated_user = authenticate(username=user.username, password=payload.password)
    if not authenticated_user:
        raise AuthenticationRequiredException(message="Invalid credentials")

    if not authenticated_user.is_active:
        raise AuthenticationRequiredException(message="Account is inactive")

    tokens = generate_tokens(authenticated_user)
    return {
        "access": tokens["access"],
        "refresh": tokens["refresh"],
        "user": authenticated_user,
    }


@auth_router.post("/refresh", response={200: Dict[str, str]})
def refresh(request, payload: RefreshTokenRequestSchema):
    """
    Refresh access token using refresh token.
    """
    try:
        tokens = JWTService.refresh_access_token(payload.refresh)
        return {
            "access": tokens["access"],
            "refresh": tokens["refresh"],
        }
    except Exception as e:
        raise AuthenticationRequiredException(message=f"Token refresh failed: {str(e)}")


@auth_router.post("/logout", response={200: Dict[str, str]})
def logout(request, payload: RefreshTokenRequestSchema):
    """
    Blacklist the refresh token to terminate session.
    """
    try:
        JWTService.blacklist_token(payload.refresh)
    except Exception:
        # Ignore failure if token is already expired/blacklisted
        pass
    return {"message": "Logged out successfully"}


@auth_router.get("/me", response={200: UserResponseSchema})
@require_auth
def me(request):
    """
    Retrieve authenticated user profile.
    """
    return request.auth_user
