from app.app import create_app
from app.settings import DEBUG, DEV_PORT

app = create_app()

if __name__ == "__main__":
    app.run(debug=DEBUG, port=DEV_PORT)
