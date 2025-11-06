from flask import flash
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from ..entity.UserAdmin import UserAdmin

from .. import db

class UserAccount:
       
    # -------------------------------
    # Login
    # -------------------------------   
    @classmethod
    def login(cls, email: str, password: str):
        user = UserAdmin.query.filter_by(email=email).first()

        if not user:
            return {"ok": False, "data": None, "errors": ["Invalid email."]}
        if user.is_suspended:
            return {"ok": False, "data": None, "errors": ["Account suspended."]}
        if user.password != password:  # later: check_password_hash
            return {"ok": False, "data": None, "errors": ["Invalid password."]}

        return {"ok": True, "data": user, "errors": []}