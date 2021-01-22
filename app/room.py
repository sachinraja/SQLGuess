from flask import Blueprint, request, render_template, redirect, url_for, session
from wtforms import Form, StringField, SubmitField, validators
from app import room_manager

room = Blueprint('room', __name__, url_prefix='/room')

class CreateRoomForm(Form):
    display_name = StringField('Your Display Name', validators=[validators.InputRequired(), validators.Length(max=50)])
    create_room_submit = SubmitField('Create Room')

class JoinRoomForm(Form):
    display_name = StringField('Your Display Name', validators=[validators.InputRequired(), validators.Length(max=50)])
    room_code = StringField('Room Code', validators=[
        validators.InputRequired(),
        validators.Length(min=4, max=4),
        validators.Regexp('^[A-Za-z]+$', message="Codes must only consist of four alphabetical characters")
        ])
    join_room_submit = SubmitField('Join Room')

@room.route('/create', methods=['GET', 'POST'])
def create():
    form = CreateRoomForm(request.form)
    if request.method == 'POST' and form.validate():

        created_room = room_manager.host_room()
        user_id = created_room.set_host(form.display_name.data)

        session['_id'] = user_id
        session['room_code'] = created_room.room_code
        session['user_type'] = 'host'

        return redirect(url_for('game.room', room_code=created_room.room_code.upper()))

    return render_template('create_room.html', form=form)

@room.route('/join', methods=['GET', 'POST'])
def join():
    form = JoinRoomForm(request.form)
    if request.method == 'POST' and form.validate():
        room_code = form.room_code.data
        user_id = room_manager.add_user_to_room(room_code, form.display_name.data)

        if user_id:
            session['_id'] = user_id
            session['room_code'] = room_code
            session['user_type'] = 'regular'

            return redirect(url_for('game.room', room_code=room_code.upper()))

        form.room_code.errors.append("Room code is invalid")

    return render_template('join_room.html', form=form)
