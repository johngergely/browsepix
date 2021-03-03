import os
basedir = os.path.abspath(os.path.dirname(__file__))

WTF_CSRF_ENABLED=True
SECRET_KEY='impossibly_so'

##### DEPLOYMENT CONFIGURATION #####

SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://app_admin:admin@localhost:5434/browsepix'
SQLALCHEMY_TRACK_MODIFICATIONS=False

## FTP SERVER
HOST = "127.0.0.1"
PORT = 5000

## user defined
ROOT = "D:\\SerenityTransfer\\nhavlin\\Pictures"
STAGE = "/static/photos"
