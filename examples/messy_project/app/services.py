from app.models import User  # Circular import!
from app.utils import validate_user  # Circular import!


class UserService:
    def create_user(self, name):
        if validate_user(name):
            return User(name)
        return None
