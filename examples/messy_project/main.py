from app.models import User
from app.services import UserService

# This will actually cause import errors!
user = User("test")
print("Messy project with circular imports")