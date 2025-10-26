# 📦 File: app/entity/ServiceCategory.py
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from .. import db


class ServiceCategory(db.Model):
    __tablename__ = 'service_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_suspended = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<ServiceCategory {self.name}>"

    # -------------------------------
    # Create
    # -------------------------------
    @classmethod
    def CreateServiceCategory(cls, name: str, description: str = "", is_suspended: int | bool = 0) -> str:
        """
        Create a service category.
        Returns one of: 'success', 'duplicate', 'invalid', or 'error'.
        """
        try:
            if not name:
                return "invalid"

            # Duplicate check (case-insensitive)
            exists = cls.query.filter_by(name=name).first()
            if exists:
                return "duplicate"

            row = cls(
                name=name,
                description=(description or "").strip(),
                is_suspended=bool(is_suspended)
            )

            db.session.add(row)
            db.session.commit()
            return "success"

        except IntegrityError:
            db.session.rollback()
            return "duplicate"  # Integrity constraint triggered (e.g., unique name)
        except Exception as e:
            db.session.rollback()
            print(f"Database error creating category: {e}")
            return "error"

    # -------------------------------
    # Read / List
    # -------------------------------
    @classmethod
    def ListServiceCategory(cls, page: int | None = 1, per_page: int = 20):
        q = cls.query.order_by(cls.id.asc())
        if page is None:
            rows = q.all()
            return {"ok": True, "data": rows, "errors": []}
        pg = q.paginate(page=page, per_page=per_page)
        return {"ok": True, "data": pg.items, "pagination": pg, "errors": []}

    # -------------------------------
    # Update
    # -------------------------------
    @classmethod
    def UpdateServiceCategory(cls, category_id: int, name: str, description: str, is_suspended: int | bool) -> str:
        """
        Update a service category.
        Returns one of: 'success', 'not_found', 'duplicate', 'invalid', 'error'.
        """
        try:
            row = cls.query.get(category_id)
            if not row:
                return "not_found"

            if not name:
                return "invalid"

            # Check for duplicate name (case-insensitive, excluding self)
            dup = cls.query.filter(
                cls.name == name,
                cls.id != category_id
            ).first()
            if dup:
                return "duplicate"

            # Apply updates
            row.name = name
            row.description = (description or "")
            row.is_suspended = bool(is_suspended)

            db.session.commit()
            return "success"

        except Exception as e:
            db.session.rollback()
            print(f"Database error updating category {category_id}: {e}")
            return "error"
    
    @classmethod
    def get_by_id(cls, category_id: int):
        row = cls.query.get(category_id)
        return {"ok": bool(row), "data": row, "errors": ([] if row else ["Category not found."])}
    
    # -------------------------------
    # Search
    # -------------------------------
    @classmethod
    def SearchServiceCategory(cls, term: str, page: int | None = 1, per_page: int = 20):
        like = f"%{(term or '').strip()}%"
        q = cls.query.filter(or_(cls.name.ilike(like), cls.description.ilike(like))).order_by(cls.id.asc())
        if page is None:
            return {"ok": True, "data": q.all(), "errors": []}
        pg = q.paginate(page=page, per_page=per_page)
        return {"ok": True, "data": pg.items, "pagination": pg, "errors": []}
        
    # -------------------------------
    # Suspended
    # -------------------------------
    @classmethod
    def SuspendedServiceCategory(cls, category_id: int, is_suspended: int | bool) -> str:
        try:
            row = cls.query.get(category_id)
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
            print(f"[ServiceCategory] set_suspended error id={category_id}: {e}")
            return "error"
