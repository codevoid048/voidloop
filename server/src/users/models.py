from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from _sdk.models import TimestampedModel


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
