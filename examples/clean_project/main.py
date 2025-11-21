from app.services.user_service import UserService

service = UserService()
user = service.create_user("test")
print("Clean project with proper architecture")