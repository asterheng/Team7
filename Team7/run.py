
from app import create_app, db, seed_defaults

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        # db.drop_all()   # 🧨 deletes all tables
        db.create_all() # 🔁 recreates tables
        seed_defaults() # 🌱 reseed defaults
    app.run(debug=True)
