from flask import Blueprint
from flask_socketio import SocketIO
import os

# Initialize SocketIO (will be attached to app in app.py)
socketio = SocketIO(
    cors_allowed_origins=os.getenv('SOCKETIO_CORS_ALLOWED_ORIGINS', '*'),
    async_mode=os.getenv('SOCKETIO_ASYNC_MODE', 'threading')
)

socialhub_bp = Blueprint(
    'socialhub', 
    __name__, 
    template_folder='../templates',
    static_folder='static',
    static_url_path='/socialhub/static'
)

from . import routes
