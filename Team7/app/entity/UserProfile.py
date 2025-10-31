from flask import flash
from sqlalchemy.exc import IntegrityError
from .. import db
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_suspended = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<UserProfile {self.name}>"

    # -------------------------------
    # Create
    # -------------------------------
    @classmethod
    def CreateUserProfile(cls, name: str, description: str = "", is_suspended: int = 0) -> str:
        """
        Create a profile.
        Returns one of: 'success', 'invalid', 'duplicate', 'error'.
        """
        try:
            if not name:
                return "invalid"

            # Duplicate check
            if cls.query.filter_by(name=name).first():
                return "duplicate"

            row = cls(
                name=name,
                description=(description or ""),
                is_suspended=int(is_suspended),
            )
            db.session.add(row)
            db.session.commit()
            return "success"

        except Exception as e:
            db.session.rollback()
            print(f"Error creating profile: {e}")
            return "error"
       
    # -------------------------------
    # Read / List
    # -------------------------------        
    @classmethod
    def ListUserProfile(cls):
        """Return all service categories ordered by ID ASC."""
        try:
            rows = cls.query.order_by(cls.id.asc()).all()
            return {"ok": True, "data": rows, "errors": []}
        except Exception as e:
            db.session.rollback()
            return {"ok": False, "data": [], "errors": [f"Database error: {e}"]}

    # -------------------------------
    # Update
    # -------------------------------
    @classmethod
    def UpdateUserProfile(cls, profile_id: int, name: str, description: str, is_suspended: int | bool) -> str:
        """
        Update a profile record.
        Returns one of: 'success', 'not_found', 'duplicate', 'invalid', 'error'.
        """
        try:
            # fetch target
            row = cls.query.get(profile_id)
            if not row:
                return "not_found"

            if not name:
                return "invalid"

            # unique name check (exclude current)
            dup = cls.query.filter(cls.name == name, cls.id != profile_id).first()
            if dup:
                return "duplicate"

            # apply changes
            row.name = name
            row.description = description or ""
            row.is_suspended = bool(is_suspended)

            db.session.commit()
            return "success"

        except Exception as e:
            db.session.rollback()
            print(f"Error updating profile {profile_id}: {e}")
            return "error"
                    
    @classmethod
    def get_by_id(cls, profile_id: int):
        try:
            row = cls.query.get(profile_id)
            if row:
                return {"ok": True, "data": row}
            return {"ok": False, "errors": ["Profile not found."]}
        except Exception as e:
            db.session.rollback()
            return {"ok": False, "errors": [f"Database error: {e}"]}
    
    # -------------------------------
    # Search
    # -------------------------------            
    @classmethod
    def SearchUserProfile(cls, term: str):
        try:
            like = f"%{(term or '')}%"
            rows = (
                cls.query
                .filter(
                    or_(cls.name.ilike(like), cls.description.ilike(like))
                )
                .order_by(cls.id.asc())
                .all()
            )
            return {"ok": True, "data": rows, "errors": []}
        except Exception as e:
            db.session.rollback()
            return {"ok": False, "data": [], "errors": [f"Database error: {e}"]}
            
    # -------------------------------
    # Suspended
    # -------------------------------   
    @classmethod
    def SuspendedUserProfile(cls, profile_id: int, is_suspended: int | bool) -> str:
        try:
            row = cls.query.get(profile_id)
            if not row:
                return "not_found"
            new_val = bool(is_suspended)
            if row.is_suspended == new_val:
                return "noop"
            row.is_suspended = new_val
            db.session.commit()
            return "success"
        except Exception as e:
            db.session.rollback()
            print(f"[UserProfile] set_suspended error id={profile_id}: {e}")
            return "error"