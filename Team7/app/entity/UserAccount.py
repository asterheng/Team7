from flask import flash
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from ..entity.UserProfile import UserProfile  # make sure this import exists
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

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
    
    # -------------------------------
    # Create
    # -------------------------------
    @classmethod
    def CreateUserAC(cls, name, email, password, profile_id, is_suspended) -> str:
        """Create a new user; returns 'success', 'duplicate', or 'error'."""
        try:
            # Check duplicate
            if cls.query.filter_by(email=email).first():
                return "duplicate"

            user = cls(
                name=name,
                email=email,
                password=password,
                profile_id=int(profile_id),
                is_suspended=int(is_suspended),
            )
            db.session.add(user)
            db.session.commit()
            return "success"

        except IntegrityError:
            db.session.rollback()
            return "error"

        except Exception:
            db.session.rollback()
            return "error"

    # -------------------------------
    # Read / List
    # -------------------------------
    @classmethod
    def ListUsers(cls, page: int | None = None, per_page: int = 20):
        """
        Return all users joined with their profiles, ordered by ID ASC.
        - If page is given -> returns pagination dict with .items in data
        - Else -> returns full list (no pagination)
        """
        try:
            q = (db.session.query(cls, UserProfile)
                 .join(UserProfile)
                 .order_by(cls.id.asc()))

            if page is not None:
                pg = q.paginate(page=page, per_page=per_page, error_out=False)
                return {
                    "ok": True,
                    "data": pg.items,        # list[(UserAccount, UserProfile)]
                    "pagination": {
                        "page": pg.page, "pages": pg.pages,
                        "has_prev": pg.has_prev, "has_next": pg.has_next,
                        "prev_num": pg.prev_num, "next_num": pg.next_num,
                        "total": pg.total, "per_page": pg.per_page,
                    },
                    "errors": [],
                }

            rows = q.all()
            return {"ok": True, "data": rows, "errors": []}

        except Exception as e:
            db.session.rollback()
            return {"ok": False, "data": [], "errors": [f"Database error: {e}"]}
  
    # -------------------------------
    # Update
    # -------------------------------
    @classmethod
    def UpdateUser(cls, user_id: int, name: str, email: str, password: str | None,
                    profile_id: int, is_suspended: int) -> str:
        """
        Update a user record.
        Returns one of: 'success', 'not_found', 'duplicate', 'error'.
        """
        try:
            # Find the user
            user = cls.query.get(user_id)
            if not user:
                return "not_found"

            # Duplicate email check (exclude self)
            dup = cls.query.filter(cls.email == email, cls.id != user_id).first()
            if dup:
                return "duplicate"

            # Apply changes
            user.name = name
            user.email = email
            if password:  # only change if provided
                user.password = password
            user.profile_id = int(profile_id)
            user.is_suspended = int(is_suspended)

            db.session.commit()
            return "success"

        except Exception as e:
            db.session.rollback()
            print(f"Error updating user {user_id}: {e}")
            return "error"
    
    @classmethod
    def get_by_id(cls, user_id: int):
        return (
            cls.query.options(joinedload(cls.profile))
            .filter_by(id=user_id)
            .first()
        )
     
    # -------------------------------
    # Search
    # -------------------------------
    @classmethod
    def SearchUser(cls, term: str, page: int | None = None, per_page: int = 20):
        like = f"%{(term or '').strip()}%"
        q = (
            db.session.query(cls, UserProfile)
            .outerjoin(UserProfile)  # <- outer join so users still appear if profile missing
            .filter(
                or_(
                    cls.name.ilike(like),
                    cls.email.ilike(like),
                    UserProfile.name.ilike(like),
                )
            )
            .order_by(cls.id.asc())
        )
        if page is not None:
            pg = q.paginate(page=page, per_page=per_page, error_out=False)
            return {"ok": True, "data": pg.items, "pagination": {
                "page": pg.page, "pages": pg.pages, "has_prev": pg.has_prev,
                "has_next": pg.has_next, "prev_num": pg.prev_num,
                "next_num": pg.next_num, "total": pg.total, "per_page": pg.per_page
            }, "errors": []}
        rows = q.all()
        return {"ok": True, "data": rows, "errors": []}
        
    # -------------------------------
    # Suspended
    # -------------------------------    
    @classmethod
    def SuspendedUser(cls, row_id: int, is_suspended: int | bool) -> str:
        """
        Set suspension flag only.
        Returns: 'success' | 'noop' | 'not_found' | 'error'
        """
        try:
            row = cls.query.get(row_id)
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
            print(f"[{cls.__name__}] set_suspended error for id={row_id}: {e}")
            return "error"
            
    # -------------------------------
    # Suspended
    # -------------------------------   
    @classmethod
    def login(cls, email: str, password: str):
        user = cls.query.filter_by(email=email).first()

        if not user:
            return {"ok": False, "data": None, "errors": ["Invalid email."]}
        if user.is_suspended:
            return {"ok": False, "data": None, "errors": ["Account suspended."]}
        if user.password != password:  # later: check_password_hash
            return {"ok": False, "data": None, "errors": ["Invalid password."]}

        return {"ok": True, "data": user, "errors": []}
