from typing import Dict, List

from django.contrib.auth import get_user_model, authenticate
from django.db import transaction
from ninja import Router

from _sdk.decorators import require_auth, require_staff
from _sdk.jwt import generate_tokens, JWTService
from _sdk.turnstile import require_turnstile
from _sdk.exceptions import (
    AuthenticationRequiredException,
    ResourceNotFoundException,
    ValidationException,
)
from users.models import Invite
from users.schemas import (
    RegisterRequestSchema,
    LoginRequestSchema,
    RefreshTokenRequestSchema,
    TokenResponseSchema,
    UserResponseSchema,
    CreateInviteRequestSchema,
    InviteResponseSchema,
    InviteValidateResponseSchema,
)

User = get_user_model()
auth_router = Router(tags=["Authentication"])
invites_router = Router(tags=["Invites"])


def _serialize_invite(invite: Invite) -> dict:
    return {
        "id": invite.id,
        "token": invite.token,
        "email": invite.email,
        "expires_at": invite.expires_at,
        "max_uses": invite.max_uses,
        "uses_count": invite.uses_count,
        "status": invite.status,
        "invite_path": invite.invite_path(),
        "created_at": invite.created_at,
        "revoked_at": invite.revoked_at,
        "created_by_id": invite.created_by_id,
    }


def _get_valid_invite(token: str) -> Invite:
    invite = Invite.objects.filter(token=token, deleted_at__isnull=True).first()
    if not invite:
        raise ValidationException(message="Invalid invite token.")
    if invite.is_revoked:
        raise ValidationException(message="This invite has been revoked.")
    if invite.is_expired:
        raise ValidationException(message="This invite has expired.")
    if invite.is_exhausted:
        raise ValidationException(message="This invite has already been used.")
    return invite


@auth_router.post("/register", response={200: TokenResponseSchema})
def register(request, payload: RegisterRequestSchema):
    require_turnstile(request, payload.cf_turnstile_token)

    invite = _get_valid_invite(payload.invite_token.strip())

    email = payload.email.strip().lower()
    if invite.email:
        locked = invite.email.strip().lower()
        if email != locked:
            raise ValidationException(
                message="This invite is locked to a different email address."
            )
        email = locked

    if User.objects.filter(email__iexact=email).exists():
        raise ValidationException(message="A user with this email already exists.")
    if User.objects.filter(username=payload.username).exists():
        raise ValidationException(message="A user with this username already exists.")

    with transaction.atomic():
        user = User.objects.create_user(
            username=payload.username,
            email=email,
            password=payload.password,
            name=payload.name or "",
        )
        try:
            invite.consume(user)
        except ValueError as exc:
            raise ValidationException(message=str(exc)) from exc

    tokens = generate_tokens(user)
    return {
        "access": tokens["access"],
        "refresh": tokens["refresh"],
        "user": user,
    }


@auth_router.post("/login", response={200: TokenResponseSchema})
def login(request, payload: LoginRequestSchema):
    require_turnstile(request, payload.cf_turnstile_token)

    username_or_email = payload.email.strip()
    user = None

    if "@" in username_or_email:
        user = User.objects.filter(email=username_or_email).first()

    if not user:
        user = User.objects.filter(username=username_or_email).first()

    if not user:
        raise AuthenticationRequiredException(message="Invalid credentials")

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
    try:
        JWTService.blacklist_token(payload.refresh)
    except Exception:
        pass
    return {"message": "Logged out successfully"}


@auth_router.get("/me", response={200: UserResponseSchema})
@require_auth
def me(request):
    return request.auth_user


@auth_router.get("/invites/{token}", response={200: InviteValidateResponseSchema})
def validate_invite(request, token: str):
    invite = Invite.objects.filter(token=token, deleted_at__isnull=True).first()
    if not invite:
        return {
            "valid": False,
            "email": None,
            "status": "invalid",
            "expires_at": None,
        }

    return {
        "valid": invite.is_valid,
        "email": invite.email if invite.is_valid else None,
        "status": invite.status,
        "expires_at": invite.expires_at,
    }


@invites_router.post("", response={200: InviteResponseSchema})
@require_staff
def create_invite(request, payload: CreateInviteRequestSchema):
    email = payload.email.strip().lower() if payload.email else None
    if email and User.objects.filter(email__iexact=email).exists():
        raise ValidationException(message="A user with this email already exists.")

    invite = Invite.objects.create(
        email=email,
        created_by=request.auth_user,
        expires_at=Invite.default_expires_at(payload.expires_in_days),
        max_uses=payload.max_uses,
    )
    return _serialize_invite(invite)


@invites_router.get("", response={200: List[InviteResponseSchema]})
@require_staff
def list_invites(request):
    invites = Invite.objects.filter(deleted_at__isnull=True).select_related("created_by")
    return [_serialize_invite(invite) for invite in invites]


@invites_router.delete("/{invite_id}", response={200: InviteResponseSchema})
@require_staff
def revoke_invite(request, invite_id: int):
    invite = Invite.objects.filter(pk=invite_id, deleted_at__isnull=True).first()
    if not invite:
        raise ResourceNotFoundException(message="Invite not found.")

    invite.revoke()
    return _serialize_invite(invite)
