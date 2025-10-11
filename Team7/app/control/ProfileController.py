from ..repositories import UserProfileRepository
from ..entity.UserProfile import UserProfile

class ProfileController:
    def __init__(self):
        self.repo = UserProfileRepository()

    def CreateUserProfile(self, name: str, description: str, is_suspended: int):
        result = {'ok': False, 'errors': [], 'profile_id': None}
        if not name.strip():
            result['errors'].append('Name is required.')
            return result
        profile = UserProfile(name=name.strip(), description=description, is_suspended=bool(is_suspended))
        try:
            result['profile_id'] = self.repo.create(profile)
            result['ok'] = True
        except Exception as e:
            msg = str(e)
            if 'UNIQUE' in msg:
                result['errors'].append('A profile with this name already exists.')
            else:
                result['errors'].append('DB error: ' + msg)
        return result
