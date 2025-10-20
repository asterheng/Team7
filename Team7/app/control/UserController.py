from ..entity.UserAccount import UserAccount

class CreateUserController:
    def CreateUserAC(self, name: str, email: str, password: str,
                     profile_id: int, is_suspended: int):
        # just delegate — entity handles validation + persistence
        return UserAccount.CreateUserAC(
            name, email, password, profile_id, is_suspended
        )
        
        
class ListUserController:
    def list_all_users(self, page=1, per_page=20):
        return UserAccount.list_all(page=page, per_page=per_page)

    def get_user_by_id(self, user_id: int):
            return UserAccount.get_by_id(user_id)

class UserSearchController:
    def search(self, term: str, page: int | None = None, per_page: int = 20):
        return UserAccount.search(term, page=page, per_page=per_page)

class UpdateUserController:
    def update(self, user_id, name, email, password, profile_id, is_suspended):
        return UserAccount.update_user(user_id, name, email, password, profile_id, is_suspended)

    def get(self, user_id):
        return UserAccount.query.get(user_id)
