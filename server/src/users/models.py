import secrets
from datetime import timedelta

from django.db import models, transaction
from django.db.models import F
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from _sdk.models import TimestampedModel


def generate_invite_token() -> str:
    return secrets.token_urlsafe(32)


class ActiveUserManager(BaseUserManager):
    """Auth-compatible manager that hides soft-deleted users by default."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

    def deleted(self):
        """Return only soft-deleted users."""
        return super().get_queryset().filter(deleted_at__isnull=False)

    def all_with_deleted(self):
        """Return all users including soft-deleted users."""
        return super().get_queryset()

    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)


class AllUserManager(BaseUserManager):
    """Unrestricted manager to access all users, including soft-deleted."""
    pass


class User(AbstractBaseUser, PermissionsMixin, TimestampedModel):
    """
    Custom user model for Tracker.
    """
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255, blank=True)
    
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    # Managers
    objects = ActiveUserManager()
    all_objects = AllUserManager()

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        db_table = "users_user"
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["email"], name="user_email_idx"),
            models.Index(fields=["created_at"], name="user_created_at_idx"),
        ]

    def __str__(self):
        if self.name:
            return f"{self.name} ({self.email})"
        return self.email


class Invite(TimestampedModel):
    """
    Registration invite. Email-locked when email is set; open link when null.
    """

    token = models.CharField(
        max_length=64,
        unique=True,
        default=generate_invite_token,
        db_index=True,
    )
    email = models.EmailField(null=True, blank=True, db_index=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_invites",
    )
    expires_at = models.DateTimeField(db_index=True)
    max_uses = models.PositiveIntegerField(default=1)
    uses_count = models.PositiveIntegerField(default=0)
    accepted_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="accepted_invites",
    )
    revoked_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = "users_invite"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["expires_at"], name="invite_expires_at_idx"),
            models.Index(fields=["revoked_at"], name="invite_revoked_at_idx"),
        ]

    def __str__(self):
        target = self.email or "open link"
        return f"Invite {self.token[:8]}… ({target})"

    @classmethod
    def default_expires_at(cls, days: int = 7):
        return timezone.now() + timedelta(days=days)

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def is_exhausted(self) -> bool:
        return self.uses_count >= self.max_uses

    @property
    def is_valid(self) -> bool:
        return not self.is_revoked and not self.is_expired and not self.is_exhausted

    @property
    def status(self) -> str:
        if self.is_revoked:
            return "revoked"
        if self.is_expired:
            return "expired"
        if self.is_exhausted:
            return "used"
        return "pending"

    def invite_path(self) -> str:
        return f"/register?token={self.token}"

    def revoke(self) -> None:
        if self.revoked_at is None:
            self.revoked_at = timezone.now()
            self.save(update_fields=["revoked_at", "updated_at"])

    def consume(self, user: User) -> None:
        """Atomically mark invite as used by the newly registered user."""
        with transaction.atomic():
            invite = Invite.objects.select_for_update().get(pk=self.pk)
            if invite.revoked_at is not None:
                raise ValueError("Invite has been revoked")
            if timezone.now() >= invite.expires_at:
                raise ValueError("Invite has expired")
            if invite.uses_count >= invite.max_uses:
                raise ValueError("Invite has no uses remaining")

            updates = {
                "uses_count": F("uses_count") + 1,
                "updated_at": timezone.now(),
            }
            if invite.accepted_by_id is None:
                updates["accepted_by"] = user

            Invite.objects.filter(pk=invite.pk).update(**updates)
            self.refresh_from_db()
