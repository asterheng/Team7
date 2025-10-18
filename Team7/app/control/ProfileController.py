from ..entity.UserProfile import UserProfile

class CreateProfileController:
    def CreateUserProfile(self, name: str, description: str, is_suspended: int | bool):
        return UserProfile.CreateUserProfile(name, description, is_suspended)

class ListProfileController:
    def list_profiles_all(self):
        return UserProfile.list_all()

    def get_profile(self, profile_id: int):
        return UserProfile.get_by_id(profile_id)
