from app import create_app
from settings import DEV_PORT

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=DEV_PORT)
