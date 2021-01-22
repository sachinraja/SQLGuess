from flask import Blueprint, render_template, url_for, session
from app import room_manager

game = Blueprint('game', __name__, url_prefix='/game')

@game.route('/room/<room_code>', methods=['GET', 'POST'])
def room(room_code):
    game_room = room_manager.get_room(room_code)

    if not game_room:
        return render_template('status.html', status_msg="Invalid Room Code", description=f"""<a class="link-light" href="{url_for('room.join')}">Join a room</a>""")

    if not game_room.validate_user(session.get("_id")):
        return render_template('status.html', status_msg="Unable to Authenticate", description=f"""<a class="link-light" href="{url_for('room.join')}">Try to join a room again.</a>""")

    return render_template('game.html', room_status=game_room.status, is_host=session.get('user_type')=='host' != None, current_time=game_room.current_time)
