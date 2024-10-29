import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///C:/Users/bali/OneDrive - PESUNIVERSITY/Documents/iitmbs/sqlite.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'mad1iitm'
    
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
