from .. import db
from werkzeug.security import generate_password_hash

class UserAccount(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(190), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey('user_profiles.id'), nullable=False)
    is_suspended = db.Column(db.Boolean, default=False, nullable=False)

    profile = db.relationship('UserProfile', backref='users')

    @staticmethod
    def CreateUserAC(name: str, email: str, password: str, profile_id: int, is_suspended: int):
        return UserAccount(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            profile_id=profile_id,
            is_suspended=bool(is_suspended),
        )
