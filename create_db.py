from app import app, db   # import Flask app and db from your main file

def reset_database():
    with app.app_context():
        db.drop_all()
        print("✅ Database tables dropped.")

        db.create_all()
        print("✅ Database tables created.")
