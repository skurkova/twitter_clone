from api.main import create_app  # type: ignore
from db.models import db   # type: ignore

app = create_app()
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
