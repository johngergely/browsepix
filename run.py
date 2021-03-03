from app import app
from config import HOST, PORT
from waitress import serve

serve(app, host=HOST, port=PORT)
