from ..entity.UserProfile import UserProfile

class CreateProfileController:
    def CreateUserProfile(self, name: str, description: str, is_suspended: int | bool):
        return UserProfile.CreateUserProfile(name, description, is_suspended)

class ListProfileController:
    def list_profiles_all(self):
        return UserProfile.list_all()

    def get_profile(self, profile_id: int):
        return UserProfile.get_by_id(profile_id)

class ProfileSearchController:
    """Thin controller dedicated to searching profiles."""

    def search(self, term: str):
        """
        Search profiles by name or description.
        Returns: {"ok": bool, "data": [UserProfile], "errors": [str]}
        """
        if not term:
            return {"ok": True, "data": [], "errors": []}  # empty search -> no results
        return UserProfile.search(term)

class UpdateProfileController:
    def get(self, profile_id: int):
        return UserProfile.get_by_id(profile_id)

    def update(self, profile_id: int, name: str, description: str, is_suspended: int | bool):
        return UserProfile.update_profile(profile_id, name, description, is_suspended)
