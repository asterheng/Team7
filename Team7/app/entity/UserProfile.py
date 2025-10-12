from .. import db

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_suspended = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<UserProfile {self.name}>"