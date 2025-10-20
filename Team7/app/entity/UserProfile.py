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

    # ------------ Read helpers ------------
    @classmethod
    def list_all(cls):
        """Return all profiles ordered by ID ASC."""
        try:
            rows = cls.query.order_by(cls.id.asc()).all()
            return {"ok": True, "data": rows}
        except Exception as e:
            db.session.rollback()
            return {"ok": False, "errors": [f"Database error: {e}"]}

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

    @classmethod
    def search(cls, term: str):
        try:
            like = f"%{(term or '')}%"
            rows = (cls.query
                        .filter(or_(cls.name.ilike(like),
                                    cls.description.ilike(like)))
                        .order_by(cls.id.asc())
                        .all())
            return {"ok": True, "data": rows, "errors": []}
        except Exception as e:
            db.session.rollback()
            return {"ok": False, "data": [], "errors": [f"Database error: {e}"]}

    @classmethod
    def find_by_name(cls, name: str):
        return cls.query.filter_by(name=(name or "").strip()).first()

    # ------------ Write helpers ------------
    @classmethod
    def CreateUserProfile(cls, name: str, description: str = "", is_suspended: int | bool = 0):
        """
        Create a profile, validate, commit, and flash messages directly.
        Returns a dict with ok, errors, and profile_id.
        """
        res = {"ok": False, "errors": [], "profile_id": None}
        name_n = (name or "").strip()

        # --- Duplicate check ---
        existing = cls.query.filter_by(name=name_n).first()
        if existing:
            msg = "A profile with this name already exists."
            flash(msg, "create_profile:err")
            res["errors"].append(msg)
            return res

        # --- Create + Commit ---
        try:
            row = cls(name=name_n, description=description, is_suspended=bool(is_suspended))
            db.session.add(row)
            db.session.commit()
            msg = f"Profile created successfully."
            flash(msg, "create_profile:ok")
            res.update({"ok": True, "profile_id": row.id})
            return res
                
        except IntegrityError:
            db.session.rollback()
            msg = "A profile with this name already exists."
            flash(msg, "create_profile:err")
            res["errors"].append(msg)
            return res

        except Exception as e:
            db.session.rollback()
            msg = f"Database error: {e}"
            flash(msg, "create_profile:err")
            res["errors"].append(msg)
            return res

    @classmethod
    def update_profile(cls, profile_id: int, name: str, description: str, is_suspended: int | bool):
        """Update profile; ensure unique name (excluding self)."""
        res = {"ok": False, "errors": []}

        # fetch target
        row = cls.query.get(profile_id)
        if not row:
            res["errors"].append("Profile not found.")
            return res

        name_n = (name or "").strip()

        # unique name check (exclude current)
        dup = cls.query.filter(cls.name == name_n, cls.id != profile_id).first()
        if dup:
            res["errors"].append("A profile with this name already exists.")
            return res

        # apply changes
        row.name = name_n
        row.description = description
        row.is_suspended = bool(is_suspended)

        try:
            db.session.commit()
            res["ok"] = True
            return res
        except Exception as e:
            db.session.rollback()
            res["errors"].append(f"Database error: {e}")
            return res
