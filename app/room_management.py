import string
import uuid
import threading
import time
import random
import json
from typing import Union, List, Dict, Tuple
from flask_socketio import SocketIO
from app import game_database

socketio = None
room_manager = None

class User():
    def __init__(self, display_name : str):
        self.display_name = display_name
        self.conn_id = uuid.uuid4()
        self.status = 2 # 0 = disconnected, 1 = connected, 2 = connecting for the first time
        self.connections = 0
        self.query_count = 0
        self.guessed_correctly = False

class Host(User):
    def __init__(self, display_name : str):
        super().__init__(display_name)
        self.sid = None

    def set_sid(self, sid : str):
        """Set the sid of the host's connection.

        Args:
            sid (str): The sid of the host's connection.
        """

        self.sid = sid

class Room():
    def __init__(self, room_id : int):
        self.room_id = room_id

        # generate alphabetical code from id int
        full_ids, remainder = divmod(room_id, 26)
        room_code = 'z' * full_ids + string.ascii_lowercase[remainder]
        self.room_code = room_code.ljust(4, 'a')

        self.users = []
        self.host = None

        self.location = None
        self.available_hints = None
        self.answer = None
        self._generate_answer_and_hints()
        self.given_hints = []

        self.is_closed = False
        self.start_time = 80
        self.current_time = self.start_time
        self.status = 0 # 0 = waiting for users to connect, 1 = game started and in round, 2 = in-between rounds

    def start(self) -> None:
        """Start the room's schedule timer."""
        self.status = 1
        threading.Thread(target=self.manage_time).start()

    def manage_time(self) -> None:
        """Manage the room's event schedule."""
        self._send_hint()

        hints_count = 4
        time_per_loop = self.start_time / hints_count

        for hint_round in range(hints_count):
            i = 0
            while i < time_per_loop:
                time.sleep(1)
                self.current_time -= 1
                i += 1

            if not hint_round == hints_count - 1:
                self._send_hint()
        
         # Check if the room was closed
        if self.is_closed:
            room_manager.close_room(self)
            return

        self.status = 2
        socketio.emit('end_round', json.dumps({'user_query_counts' : self.get_user_query_counts(), 'correct_location' : self.location.name}), room=self.room_code)
        self.given_hints = []

    def next_round(self) -> None:
        """Reset room for the next round."""
        self.reset_query_counts()
        self._generate_answer_and_hints()

        self.current_time = self.start_time
        self.start()
        socketio.emit('begin_round', room=self.room_code)

    def get_user_query_counts(self) -> List[Tuple[str, str]]:
        """Get a list of users and their respective query counts.

        Returns:
            List[Tuple[str, str]]: The first string in the tuple is the display_name and the second is the query_count.
        """

        successful_users = []
        unsuccessful_users = []
        for user in self.users:
            if user.guessed_correctly:
                successful_users.append(user)
            
            else:
                unsuccessful_users.append(user)

        sorted_users = sorted(successful_users, key=lambda user: user.query_count)
        sorted_unsuccessful_users = sorted(unsuccessful_users, key=lambda user: user.query_count)
        sorted_users.extend(sorted_unsuccessful_users)

        return [(user.display_name, user.query_count, user.guessed_correctly) for user in sorted_users]

    def reset_query_counts(self) -> None:
        """Set the query count of all users to 0."""

        for user in self.users:
            user.query_count = 0
            user.guessed_correctly = False

    def set_host(self, display_name : str) -> uuid.UUID:
        """Set the host of the room.

        Args:
            display_name (str): The display name that the user is represented by.
            request_sid (str): The sid of the host's connection.

        Returns:
            uuid.UUID: The UUID of the new user.
        """

        host = Host(display_name)
        self.host = host
        self.users.append(host)
        return host.conn_id

    def is_host(self, user_conn_id : uuid.UUID) -> bool:
        """Returns if the specified conn id matches the host's or not.

        Args:
            user_conn_id (uuid.UUID): The id of the user that is checked against the room's host.

        Returns:
            bool: If the user is the host or not.
        """

        return self.host.conn_id == user_conn_id

    def add_user(self, display_name : str) -> uuid.UUID:
        """Add a user to the room.

        Args:
            display_name (str): The display name that the user is represented by.

        Returns:
            uuid.UUID: The UUID of the new user.
        """

        user = User(display_name)
        self.users.append(user)
        return user.conn_id

    def remove_user(self, user_conn_id : uuid.UUID) -> None:
        """Removes a user from the room.

        Args:
            user_conn_id (uuid.UUID): The id of the user that is checked against the room's list of ids.
        """
        i = 0
        for user in self.users:
            if user.conn_id == user_conn_id:
                self.users.pop(i)
                break

            i += 1

        return i

    def get_user(self, user_conn_id : uuid.UUID) -> Union[User, None]:
        """Get a user if they exist. Doubles as a validation.

        Args:
            user_conn_id (uuid.UUID): The id of the user that is checked against the room's list of ids.

        Returns:
            Union[User, None]: User if the user exists, None if they do not.
        """

        return next(filter(lambda user: user.conn_id == user_conn_id, self.users), None)

    def get_user_index(self, user_conn_id : uuid.UUID) -> Union[User, None]:
        """Get a user's index if they exist. Doubles as a validation.

        Args:
            user_conn_id (uuid.UUID): The id of the user that is checked against the room's list of ids.

        Returns:
            Union[User, None]: User if the user exists, None if they do not.
        """

        index = None
        for i, user in enumerate(self.users):
            if user.conn_id == user_conn_id:
                index = i
                break

        return index

    def disconnect_user(self, user_conn_id : uuid.UUID) -> None:
        """Set a user's status to disconnected.

        Args:
            user_conn_id (uuid.UUID): The id of the user that is checked against the room's list of ids.
        """

        user = self.get_user(user_conn_id)
        user.status = 0

        self._check_empty()

    def _check_empty(self) -> None:
        """Checks if the room is empty (no user has any connections)."""

        room_empty = not any(user.connections > 0 for user in self.users)

        if room_empty:
            # mark for closure so thread doesn't send any events later on
            if self.status == 1:
                self.is_closed = True

            # close immediately if there is no thread
            else:
                room_manager.close_room(self)

    def validate_user(self, user_conn_id : uuid.UUID) -> bool:
        """Check if a user is allowed to connect to the room.

        Args:
            user_conn_id (uuid.UUID): The id of the user that is checked against the room's list of ids.

        Returns:
            bool: If the user is validated for the room or not.
        """

        return any(user.conn_id == user_conn_id for user in self.users)

    def get_display_names_and_statuses(self) -> List[Dict[str, str]]:
        """Get the display names of all the users in this room.

        Returns:
            list[str]: The display names of all the users.
        """

        output = []
        for user in self.users:
            output.append({
                'display_name' : user.display_name,
                'status' : user.status
            })
        return output

    def check_guess(self, user : User, guess : str) -> bool:
        """Check if a guess matched the answer.

        Args:
            user (User): The user making the guess.
            guess (str): The guess.

        Returns:
            bool: If the guess was correct or not.
        """

        answer_correct = self.answer == guess.lower()
        user.guessed_correctly = answer_correct
        return answer_correct

    def _generate_answer_and_hints(self) -> None:
        """Create the answer and hints for this room."""

        self.location, self.available_hints = game_database.get_random_location()
        random.shuffle(self.available_hints)
        self.answer = self.location.name.lower()

    def _send_hint(self) -> None:
        """Send a hint to the users in the room."""

        hint = self.available_hints.pop(random.randrange(len(self.available_hints)))
        self.given_hints.append(hint)
        socketio.emit('hint', {'name': hint[0], 'value': hint[1]}, room=self.room_code)

class RoomManager():
    def __init__(self):
        self._active_rooms = []
        self._open_room_ids = []
        self._next_room_id = 0

    def host_room(self) -> Room:
        """Get an open room or create one.

        Returns:
            Room: The open or new room.
        """

        if self._open_room_ids:
            room = Room(self._open_room_ids.pop(0))
        else:
            room = self._create_room()

        self._active_rooms.append(room)
        return room

    def add_user_to_room(self, room_code : str, display_name : str) -> Union[uuid.UUID, None]:
        """Add a user to a room using a room_code.

        Args:
            room_code (str): The 4 letter code that users use to join the room.
            display_name (str): The display name that the user is represented by.

        Returns:
            Union[uuid.UUID, None]: The UUID of the new user or None if the room does not exist.
        """

        room = self.get_room(room_code.lower())
        if not room:
            return None

        return room.add_user(display_name)

    def get_room(self, room_code : str) -> Union[Room, None]:
        """Searches for the room that room_code is associated with and returns the room or None.

        Args:
            room_code (str): The 4 letter code that users use to join the room.

        Returns:
            Union[Room, None]: Room if the room with room_code is found, None if there is no room with room_code.
        """

        return next(filter(lambda room : room.room_code == room_code.lower(), self._active_rooms), None)

    def _room_exists(self, room_code : str) -> bool:
        """Searches for the room that room_code is associated with and returns a bool.

        Args:
            room_code (str): The 4 letter code that users use to join the room.

        Returns:
            bool: True if the room with room_code exists, False if it does not.
        """

        return any(room.room_code == room_code for room in self._active_rooms)

    def _create_room(self) -> Room:
        """Create a new room.

        Returns:
            Room: The new room.
        """

        room = Room(self._next_room_id)
        self._next_room_id += 1
        return room

    def close_room(self, room : Room):
        """Close a room and add it to open rooms."""

        self._active_rooms.remove(room)
        self._open_room_ids.append(room.room_id)

    def register_socketio(self, socketio_in : SocketIO) -> None:
        """Register the socket.io connection manager for room management.

        Args:
            socketio_in (SocketIO): The socket.io connection manager.
        """

        global socketio
        socketio = socketio_in
    
    def register_room_manager(self, room_manager_in) -> None:
        """Register the room manager for use in the module.

        Args:
            room_manager (RoomManager): The room manager.
        """

        global room_manager
        room_manager = room_manager_in