from app.utils.validators import validate_user
# Import from models without circular dependency

class UserService:
    def create_user(self, name):
        if validate_user(name):
            from app.models.user import User  # Lazy import if needed
            return User(name)
        return None