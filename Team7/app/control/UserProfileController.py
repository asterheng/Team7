from ..entity.UserProfile import UserProfile

class CreateUserProfileController:
    def CreateUserProfile(self, name: str, description: str, is_suspended: int | bool):
        return UserProfile.CreateUserProfile(name, description, is_suspended)

class ListUserProfileController:
    def ListUserProfile(self):
        return UserProfile.ListUserProfile()

class UserProfileSearchController:
    def SearchUserProfile(self, term: str):
        return UserProfile.SearchUserProfile(term)

class UpdateUserProfileController:
    def UpdateUserProfile(self, profile_id: int, name: str, description: str, is_suspended: int | bool):
        return UserProfile.UpdateUserProfile(profile_id, name, description, is_suspended)
        
    def get(self, profile_id: int):
        return UserProfile.get_by_id(profile_id)
        
class SuspendedUserProfileController:
    def SuspendedUserProfile(self, profile_id: int, is_suspended: int | bool) -> str:
        return UserProfile.SuspendedUserProfile(profile_id, is_suspended)