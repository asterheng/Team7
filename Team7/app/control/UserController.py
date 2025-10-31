from ..entity.UserAccount import UserAccount

class CreateUserController:
    def CreateUserAC(self, name: str, email: str, password: str,
                     profile_id: int, is_suspended: int):
        # just delegate — entity handles validation + persistence
        return UserAccount.CreateUserAC(
            name, email, password, profile_id, is_suspended
        )
                
class ListUserController:
    def ListUsers(self, page=1, per_page=20):
        return UserAccount.ListUsers(page=page, per_page=per_page)

class UserSearchController:
    def SearchUser(self, term: str, page: int | None = None, per_page: int = 20):
        return UserAccount.SearchUser(term, page=page, per_page=per_page)

class UpdateUserController:
    def UpdateUser(self, user_id, name, email, password, profile_id, is_suspended):
        return UserAccount.UpdateUser(user_id, name, email, password, profile_id, is_suspended)
        
    def get(self, user_id):
        return UserAccount.get_by_id(user_id)  
        
class SuspendedUserController:
    def SuspendedUser(self, user_id: int, is_suspended: int | bool) -> str:
        return UserAccount.SuspendedUser(user_id, is_suspended)
        
class LoginUserController:
    def login(self, email: str, password: str):
        return UserAccount.login(email, password)