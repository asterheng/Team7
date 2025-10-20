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
    
    @classmethod
    def list_all(cls, page: int | None = None, per_page: int = 20):
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
  
    @classmethod
    def search(cls, term: str, page: int | None = None, per_page: int = 20):
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
  
  
    @classmethod
    def get_by_id(cls, user_id: int):
        return (
            cls.query.options(joinedload(cls.profile))
            .filter_by(id=user_id)
            .first()
        )
    
    @classmethod
    def update_user(cls, user_id: int, name: str, email: str, password: str | None,
                    profile_id: int, is_suspended: int | bool):
        """
        Update a user. If password is blank/None, keep the current password.
        Returns: {"ok": bool, "errors": [..]}
        """
        res = {"ok": False, "errors": []}

        # Find the user
        user = cls.query.get(user_id)
        if not user:
            res["errors"].append("User not found.")
            return res

        # Duplicate email check (exclude self)
        dup = cls.query.filter(cls.email == email, cls.id != user_id).first()
        if dup:
            res["errors"].append("A user with this email already exists.")
            return res

        # Apply changes
        user.name = name
        user.email = email
        if password:                  # only change if provided
            user.password = password  # plain text per your current design
        user.profile_id = int(profile_id)
        user.is_suspended = bool(is_suspended)

        try:
            db.session.commit()
            res["ok"] = True
            return res
        except Exception as e:
            db.session.rollback()
            res["errors"].append(f"Database error: {e}")
            return res
