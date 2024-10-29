from flask import Flask
from config import Config
from models import db
import os

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

with app.app_context():
    db.create_all()

import routes

if __name__ == '__main__':
    app.run(debug=True)
