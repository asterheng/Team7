
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, template_folder='boundary')
    app.config['SECRET_KEY'] = 'dev-secret'  # replace in production
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Team7.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from .routes import bp as boundary_bp
    app.register_blueprint(boundary_bp)

    return app

def seed_defaults():
    from .entity.UserProfile import UserProfile
    names = ["Admin", "CRS Rep", "PIN", "Platform Management"]
    existing = {p.name for p in UserProfile.query.all()}
    for n in names:
        if n not in existing:
            db.session.add(UserProfile(name=n, description=f"Default role: {n}", is_suspended=False))
    db.session.commit()
