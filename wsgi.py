from app import app

if __name__ == "__main__":
    from create_db import reset_database
    reset_database() 
    app.run()
