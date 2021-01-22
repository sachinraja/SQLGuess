from app.game_db import GameDatabase

game_database = GameDatabase()

from app.room_management import RoomManager
room_manager = RoomManager()

from app.app import app, register_blueprints
from app.socket import socketio

room_manager.register_socketio(socketio)
room_manager.register_room_manager(room_manager)
register_blueprints()
