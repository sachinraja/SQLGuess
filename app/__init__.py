from app.game_db import GameDatabase

game_database = GameDatabase()

from app.room_management import room_manager, register_socketio

from app.app import app, register_blueprints
from app.socket import socketio

register_socketio(socketio)
register_blueprints()
