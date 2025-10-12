from sqlalchemy.exc import IntegrityError
from . import db
from .entity.UserProfile import UserProfile
from .entity.UserAccount import UserAccount

class UserProfileRepository:
    def all(self):
        return UserProfile.query.order_by(UserProfile.id).all()

    def create(self, profile: UserProfile):
        try:
            db.session.add(profile)
            db.session.commit()
            return profile.id
        except Exception:
            db.session.rollback()
            raise

class UserRepository:
    def find_by_email(self, email: str):
        return UserAccount.query.filter_by(email=email.strip().lower()).first()

    def create(self, user: UserAccount):
        try:
            db.session.add(user)
            db.session.commit()
            return user.id
        except IntegrityError:
            db.session.rollback()
            raise          # let caller decide how to message “email exists”
        except Exception:
            db.session.rollback()
            raise
