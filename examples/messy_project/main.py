from app.models import User

# This will actually cause import errors!
user = User("test")
print("Messy project with circular imports")
