import os

from app import create_app
from app.extensions.db import db


# Gunicorn entrypoint: `gunicorn run:app --bind 0.0.0.0:$PORT`
# create_app() initializes Flask and runs startup checks inside app.app_context().
app = create_app()

if os.getenv("APP_ENV", "development") != "production":
    with app.app_context():
        db.create_all()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=os.getenv("APP_ENV", "development") != "production",
    )
