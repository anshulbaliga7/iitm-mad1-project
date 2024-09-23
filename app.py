from flask import Flask
from config import Config
from models import db

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Create tables if they don't exist
with app.app_context():
    db.create_all()

# Import routes
import routes

if __name__ == '__main__':
    app.run(debug=True)