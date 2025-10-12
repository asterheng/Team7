
from app import create_app, db, seed_defaults

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_defaults()
    app.run(debug=True)
