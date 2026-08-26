from app.services import UserService  # Circular import!


class User:
    def __init__(self, name):
        self.name = name
    
    def get_service(self):
        return UserService()
