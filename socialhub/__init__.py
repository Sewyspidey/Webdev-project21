from flask import Blueprint
from flask_socketio import SocketIO

# Initialize SocketIO (will be attached to app in app.py)
socketio = SocketIO()

socialhub_bp = Blueprint(
    'socialhub', 
    __name__, 
    template_folder='../templates',
    static_folder='static',
    static_url_path='/socialhub/static'
)

from . import routes
