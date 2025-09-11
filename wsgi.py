import os
from app import app
from create_db import reset_database

# Path must match what's in app.py
db_path = os.path.join(os.getcwd(), 'db', 'glassware.sqlite3')

if not os.path.exists(db_path):
    print("📦 First start: creating database...")
    reset_database()
else:
    print("✅ Database already exists, skipping reset.")

application = app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)
