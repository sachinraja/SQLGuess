import json
from flask import session
from flask_socketio import SocketIO, emit, join_room, leave_room
from app import app, game_database, room_manager

socketio = SocketIO(app, async_mode='threading')

@socketio.on('connect')
def connect_user():
    room = room_manager.get_room(session.get('room_code'))

    if not room:
        return

    user_conn_id = session.get('_id')
    user = room.get_user(user_conn_id)
    if not user:
        return

    user.connections += 1

    output = {
        'users' : room.get_display_names_and_statuses(),
        'hints' : room.given_hints,
        'query_count' : user.query_count,
        }

    # add end round data if the room is currently in that phase
    if room.status == 2:
        output['user_query_counts'] = room.get_user_query_counts()
        output['correct_location'] = room.location.name

    # if user was disconnected, reconnect and remove disconnected flag
    if user.status == 0:
        user.status = 1
        emit('user_reconnect', room.get_user_index(user_conn_id), room=room.room_code)

    # connecting for the first time
    # tell others that the user has joined
    # have to do this before user joins or joining user will receive the emit too, alongside the full list of users
    elif user.status == 2:
        user.status = 1
        emit('add_user', user.display_name, room=room.room_code)

    join_room(room.room_code)

    # send full list of display names to user who joined
    emit('join_room', json.dumps(output))

@socketio.on('disconnect')
def remove_user():
    room_code = session.get('room_code')
    room = room_manager.get_room(room_code)
    if not room:
        return

    user_conn_id = session.get('_id')
    if not user_conn_id:
        return

    index = room.get_user_index(user_conn_id)
    if index is None:
        return

    user = room.get_user(user_conn_id)
    user.connections -= 1

    # if user does not have any other connections, disconnect
    if not user.connections:
        room.disconnect_user(user_conn_id)
        emit('user_disconnect', index, room=room_code)

@socketio.on('start_game')
def start_game():
    room = room_manager.get_room(session.get('room_code'))
    if not room:
        return

    # if game has started already
    if room.status:
        return

    if not room.is_host(session.get('_id')):
        return

    room.start()

    emit('start_game', room=room.room_code)

@socketio.on('guess')
def guess(guess_text):
    output = {}

    guess_text = guess_text.strip().lower()
    if not guess_text:
        output['error'] = "Bad Request, no guess"

    elif len(guess_text) > 1000:
        output['error'] = "Bad Request, guess is over 1000 characters"

    else:
        room = room_manager.get_room(session.get('room_code'))

        # if room has not started yet
        if not room.status:
            return

        user = room.get_user(session.get('_id'))
        if not user:
            output['error'] = "Not Authenticated, you are not validated for this room"

        else:
            output['result'] = room.check_guess(user, guess_text)

    emit('guess', output)


@socketio.on('query')
def query(query_text):
    output = {}

    if not query_text:
        output['error'] = "Bad Request, no query"

    elif len(query_text) > 1000:
        output['error'] = "Bad Request, query is over 1000 characters"

    else:
        room = room_manager.get_room(session.get('room_code'))

        if not room.status:
            return

        user = room.get_user(session.get('_id'))
        if not user:
            output['error'] = "Not Authenticated, you are not validated for this room"

        else:
            output = game_database.execute_user_input(query_text)

    user.query_count += 1
    emit('query', output)

@socketio.on('next_round')
def next_round():
    room = room_manager.get_room(session.get('room_code'))
    if not room:
        return

    # if room is not in-between rounds
    if not room.status == 2:
        return

    if not room.is_host(session.get('_id')):
        return

    room.next_round()

@socketio.on('end_game')
def end_game():
    room = room_manager.get_room(session.get('room_code'))
    if not room:
        return

    # if room is not in-between rounds
    if not room.status == 2:
        return

    if not room.is_host(session.get('_id')):
        return

    room_manager.close_room(room)
    socketio.emit('end_game', room=room.room_code)
