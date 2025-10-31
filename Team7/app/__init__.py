from flask import Flask, request, make_response, current_app
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
    
    @app.after_request
    def add_no_cache_headers(response):
        # Don’t cache dynamic pages
        if not request.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response
    
    @app.context_processor
    def utility_processor():
        def has_endpoint(name: str) -> bool:
            return name in current_app.view_functions
        return {"has_endpoint": has_endpoint}
        
    return app


from .entity.UserProfile import UserProfile
from .entity.UserAccount import UserAccount
from . import db

def seed_defaults():
    # 1️⃣ Ensure user profiles exist
    profile_names = ["Admin", "CRS Rep", "PIN", "Platform Management"]
    existing_profiles = {p.name for p in UserProfile.query.all()}

    for name in profile_names:
        if name not in existing_profiles:
            db.session.add(UserProfile(name=name, description=f"Default role: {name}", is_suspended=False))
    db.session.commit()

    # 2️⃣ Ensure an admin account exists
    admin_profile = UserProfile.query.filter_by(name="Admin").first()
    if not admin_profile:
        print("⚠️ Admin profile not found; skipping admin user seed.")
        return

    admin_email = "admin@example.com"
    existing_admin = UserAccount.query.filter_by(email=admin_email).first()

    if not existing_admin:
        # Plain-text password
        admin_user = UserAccount(
            name="Administrator",
            email=admin_email,
            password="admin123",  # plain text, for development only
            profile_id=admin_profile.id,
            is_suspended=False
        )
        db.session.add(admin_user)
        db.session.commit()
        print(f"✅ Created default admin user ({admin_email}, password: admin123)")
    else:
        print("ℹ️ Admin user already exists.")