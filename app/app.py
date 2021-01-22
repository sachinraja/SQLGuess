from flask import Flask, request, render_template, url_for

app = Flask(__name__)

from dotenv import load_dotenv
import os
app.config['SECRET_KEY'] = bytes(os.environ['SECRET_KEY'], 'utf-8')

def register_blueprints():
    from app.room import room
    from app.game import game
    app.register_blueprint(room)
    app.register_blueprint(game)

@app.route('/')
def home():
    return render_template('home.html')