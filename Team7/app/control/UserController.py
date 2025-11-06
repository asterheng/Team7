from ..entity.UserAccount import UserAccount
from ..entity.UserAdmin import UserAdmin

class CreateUserController:
    def CreateUserAC(self, name: str, email: str, password: str,
                     profile_id: int, is_suspended: int):
        # just delegate — entity handles validation + persistence
        return UserAdmin.CreateUserAC(
            name, email, password, profile_id, is_suspended
        )
                
class ListUserController:
    def ListUsers(self, page=1, per_page=20):
        return UserAdmin.ListUsers(page=page, per_page=per_page)

class UserSearchController:
    def SearchUser(self, term: str, page: int | None = None, per_page: int = 20):
        return UserAdmin.SearchUser(term, page=page, per_page=per_page)

class UpdateUserController:
    def UpdateUser(self, user_id, name, email, password, profile_id, is_suspended):
        return UserAdmin.UpdateUser(user_id, name, email, password, profile_id, is_suspended)
        
    def get(self, user_id):
        return UserAdmin.get_by_id(user_id)  
        
class SuspendedUserController:
    def SuspendedUser(self, user_id: int, is_suspended: int | bool) -> str:
        return UserAdmin.SuspendedUser(user_id, is_suspended)
        
class LoginUserController:
    def login(self, email: str, password: str):
        return UserAccount.login(email, password)