# app/control/ProfileController.py
from ..entity.UserProfile import UserProfile
from .. import db

class ProfileController:
    def __init__(self):
        pass

    def CreateUserProfile(self, name: str, description: str, is_suspended: int):
        """Create a new profile and save to the DB."""
        result = {'ok': False, 'errors': [], 'profile_id': None}
        if not name.strip():
            result['errors'].append('Name is required.')
            return result

        try:
            new_profile = UserProfile(
                name=name.strip(),
                description=description,
                is_suspended=bool(is_suspended)
            )
            db.session.add(new_profile)
            db.session.commit()
            result['ok'] = True
            result['profile_id'] = new_profile.id
        except Exception as e:
            msg = str(e)
            if 'UNIQUE' in msg:
                result['errors'].append('A profile with this name already exists.')
            else:
                result['errors'].append('Database error: ' + msg)
        return result

    def list_profiles(self):
        """Fetch all profiles in ascending order by ID."""
        return UserProfile.query.order_by(UserProfile.id.asc()).all()
