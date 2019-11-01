import os
from flask import Flask, escape, request, redirect, render_template, session
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import *


app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Initializing Bootstrap
Bootstrap(app)

# Initializing Navbar
nav = Nav()

# registers the "top" menubar

topbar = Navbar('',
    View('Home', 'index'),
    View('Activities','activities'),
    View('Leaderboard','leaderboard'),
    View('Teams','teams'),
    Link('Logout', 'http://jonathantrinh.com')
    # View('Your Account', 'frontend.account_info'),
)

nav.register_element('top', topbar)

nav.init_app(app)

from models import Team, User, Activity


@app.route('/')
def index():
  print(os.getenv('APP_SETTINGS'))
  return render_template('index.html', user_first_name=User.query.first().first_name)


@app.route('/<name>')
def hello_name(name):
  return "Hello {}!".format(name)

@app.route('/user_main')
def user_main():
  return render_template('user_index.html')

@app.route('/leaderboard')
def leaderboard():
  return render_template('leaderboard.html')

@app.route('/teams')
def teams():
  return render_template('teams.html')

@app.route('/activities')
def activities():
  return render_template('activities.html')

if __name__ == '__main__':
  app.run()


