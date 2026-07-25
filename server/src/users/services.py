from django.contrib.auth import get_user_model

User = get_user_model()


class UserService:
    """Service layer for user operations."""

    @staticmethod
    def get_user_by_id(user_id: int):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
