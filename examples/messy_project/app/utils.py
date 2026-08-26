from app.models import User  # Circular import!


def validate_user(name):
    User(name)  # This creates the cycle
    return len(name) > 0