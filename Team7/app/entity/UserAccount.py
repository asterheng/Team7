from flask import flash
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from ..entity.UserProfile import UserProfile  # make sure this import exists
from .. import db

class UserAccount(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(190), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey('user_profiles.id'), nullable=False)
    is_suspended = db.Column(db.Boolean, default=False, nullable=False)

    profile = db.relationship('UserProfile', backref='users')
    
    """Create user""" 
    @classmethod
    def CreateUserAC(cls, name: str, email: str, password: str, profile_id: int, is_suspended: int):
        # duplicate check (use same normalized value)
        if cls.query.filter_by(email=email).first():
            flash("A user with this email already exists.", "create_user:err")
            return {"ok": False, "errors": ["A user with this email already exists."]}

        try:
            user = cls(
                name=name,
                email=email,
                password=password,                     
                profile_id=int(profile_id),
                is_suspended=bool(is_suspended),
            )
            db.session.add(user)
            db.session.commit()
            flash("User created successfully.", "create_user:ok")
            return {"ok": True, "user_id": user.id}

        except IntegrityError:
            db.session.rollback()
            flash("A user with this email already exists (race condition).", "create_user:err")
            return {"ok": False, "errors": ["Duplicate email"]}

        except Exception as e:
            db.session.rollback()
            flash("Database error: " + str(e), "create_user:err")
            return {"ok": False, "errors": [str(e)]}
    
    """Display of List of user"""        
    @classmethod
    def list_all(cls):
        """
        Return all users joined with their profiles,
        ordered by user ID ascending.
        """
        try:
            rows = (
                db.session.query(cls, UserProfile)   # use cls instead of UserAccount
                .join(UserProfile)                   # inner join on relationship FK
                .order_by(cls.id.asc())
                .all()                               # -> list[(UserAccount, UserProfile)]
            )
            return {"data": rows}
        except Exception as e:
            db.session.rollback()

    @classmethod
    def get_by_id(cls, user_id: int):
        return (
            cls.query.options(joinedload(cls.profile))
            .filter_by(id=user_id)
            .first()
        )
