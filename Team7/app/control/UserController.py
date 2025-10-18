from ..entity.UserAccount import UserAccount

class CreateUserController:
    def CreateUserAC(self, name: str, email: str, password: str,
                     profile_id: int, is_suspended: int):
        # just delegate — entity handles validation + persistence
        return UserAccount.CreateUserAC(
            name, email, password, profile_id, is_suspended
        )
        
        
class ListUserController:
    def list_all_users(self):
        return UserAccount.list_all()

def get_user_by_id(self, user_id: int):
        return UserAccount.get_by_id(user_id)
