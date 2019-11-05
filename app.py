import os, json
import datetime
from collections import defaultdict
from flask import Flask, escape, request, redirect, render_template, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import *
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
# from flask_security import Security, SQLAlchemyUserDatastore, \
#    login_required, current_user, login_user, logout_user
from oauthlib.oauth2 import WebApplicationClient
import requests

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Creating database
db = SQLAlchemy(app)

# Google Login Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

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
    View('Logout','logout')
    # View('Your Account', 'frontend.account_info'),
)

nav.register_element('top', topbar)

nav.init_app(app)

from models import Team, User, Activity, User, Role
from calculator import *

# user_datastore = SQLAlchemyUserDatastore(db.session, User, Role)
# security = Security(app, user_datastore)

# LOGIN Section
@login_manager.user_loader
def load_user(user_id):
  return User.query.get(user_id)

def get_google_provider_cfg():
  return requests.get(GOOGLE_DISCOVERY_URL).json()

@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@app.route("/login/callback")
def callback():
  # Get authorization code Google sent back to you
  code = request.args.get("code")

  # Find out what URL to hit to get tokens that allow you to ask for
  # things on behalf of a user
  google_provider_cfg = get_google_provider_cfg()
  token_endpoint = google_provider_cfg["token_endpoint"]

  # Prepare and send a request to get tokens! Yay tokens!
  token_url, headers, body = client.prepare_token_request(
      token_endpoint,
      authorization_response=request.url,
      redirect_url=request.base_url,
      code=code
  )
  token_response = requests.post(
      token_url,
      headers=headers,
      data=body,
      auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
  )

  # Parse the tokens!
  client.parse_request_body_response(json.dumps(token_response.json()))

  # Now that you have tokens (yay) let's find and hit the URL
  # from Google that gives you the user's profile information,
  # including their Google profile image and email
  userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
  uri, headers, body = client.add_token(userinfo_endpoint)
  userinfo_response = requests.get(uri, headers=headers, data=body)

  # You want to make sure their email is verified.
  # The user authenticated with Google, authorized your
  # app, and now you've verified their email through Google!
  if userinfo_response.json().get("email_verified"):
      #unique_id = userinfo_response.json()["sub"]
      users_email = userinfo_response.json()["email"]
      users_first_name = userinfo_response.json()["given_name"]
      users_last_name = userinfo_response.json()["family_name"]
  else:
      return "User email not available or not verified by Google.", 400

  # Doesn't exist? Add it to the database.
  if not User.query.filter(User.email==users_email).all():
    user = User(first_name=users_first_name, last_name=users_last_name, email=users_email, active=True)
    db.session.add(user)
    db.session.commit()
  else:
    user = User.query.filter(User.email==users_email).first()

  # Begin user session by logging the user in
  login_user(user)

  # Send user back to homepage
  return redirect(url_for("index"))

@app.route("/logout")
@login_required
def logout():
  logout_user()
  session.clear()
  return redirect(url_for("index"))

@app.route('/')
def index():
  if current_user.is_authenticated:
    team=None
    teammates=None
    team_dict={}
    if current_user.team_id:
      team=Team.query.get(current_user.team_id)
      teammates=User.query.filter_by(team_id = current_user.team_id).filter(User.id != current_user.id).all()
    #   for teammate in teammates:
    #     print(teammate.first_name)
    #     team_dict[teammate.first_name] = [total_user_bike(teammate.id), total_user_run(teammate.id), total_user_swim(teammate.id)]
    # print(team_dict)

    return render_template('index.html',
                          user_first_name=current_user.first_name,
                          user_bike=total_user_bike(current_user.id),
                          user_run=total_user_run(current_user.id),
                          user_swim=total_user_swim(current_user.id),
                          team=team,
                          teammates=teammates
                          )
  else:
    return render_template('welcome.html')

@app.route('/<name>')
def hello_name(name):
  return "Hello {}!".format(name)

@app.route('/user_main')
def user_main():
  return render_template('user_index.html')

@app.route('/leaderboard')
def leaderboard():
  teams=Team.query.all()
  return render_template('leaderboard.html',teams=teams)

#------------------------------------ Team Methods ------------------------------------

@app.route('/teams')
def teams():
  valid_team_list = Team.query.filter(Team.member_count < 3).filter(Team.id != current_user.team_id).all()
  return render_template('teams.html', team_exist=False, team_list = valid_team_list, has_current_team=current_user.team_id)

@app.route('/addteam', methods=['GET','POST'])
def create_team():
    if request.method == 'POST':
        team_name = request.form.get("newteam")
        # If team exists in database
        if Team.query.filter(team_name == Team.team_name).all():
            return render_template('teams.html', team_exist=True)
        else:
            old_team_id = current_user.team_id
            if old_team_id:
                current_user.team_id=None
                if Team.query.get(old_team_id).member_count == 1:
                    db.session.delete(Team.query.get(old_team_id))
                else:
                    old_team = Team.query.get(old_team_id)
                    old_team.member_count = old_team.member_count - 1
            team = Team(team_name=team_name, member_count=1)
            db.session.add(team)
            db.session.commit()
            current_user.team_id = Team.query.filter(team_name == Team.team_name).first().id
            db.session.commit()
            return redirect(url_for("index"))

@app.route('/jointeam/<team_id>', methods=['GET', 'POST'])
def join_team(team_id):
    old_team_id = current_user.team_id
    if old_team_id:
        current_user.team_id=None
        if Team.query.get(old_team_id).member_count == 1:
            Team.query.filter_by(id=old_team_id).delete()
        else:
            old_team = Team.query.get(old_team_id)
            old_team.member_count = old_team.member_count - 1

    team = Team.query.get(team_id)
    team.member_count = team.member_count + 1
    current_user.team_id = team_id
    db.session.commit()
    return redirect(url_for("index"))

@app.route('/quitteam', methods=['GET', 'POST'])
def quit_team():
    old_team_id = current_user.team_id
    if old_team_id:
        current_user.team_id=None
        if Team.query.get(old_team_id).member_count == 1:
            Team.query.filter_by(id=old_team_id).delete()
        else:
            old_team = Team.query.get(old_team_id)
            old_team.member_count = old_team.member_count - 1
        db.session.commit()
    return redirect(url_for("index"))

#------------------------------------ Activity Methods ------------------------------------

@app.route('/activities')
def activities():
  print(f'Total User Swim is: {total_user_swim(current_user.id)}')
  print(f'Total User Run is: {total_user_run(current_user.id)}')
  print(f'Total User Bike is: {total_user_bike(current_user.id)}')
  print(f'Total Team Swim is: {total_team_swim(current_user.team_id)}')
  print(f'Total Team Run is: {total_team_run(current_user.team_id)}')
  print(f'Total Team Bike is: {total_team_bike(current_user.team_id)}')
  print(f'Total Team Progress is: {team_progress(current_user.team_id)}')
  valid_activities_list = Activity.query.filter_by(user_id = current_user.id).order_by(desc(Activity.date_completed)).all()
  return render_template('activities.html', activities_list=valid_activities_list)

@app.route('/addactivity', methods=['GET', 'POST'])
def add_activity():
  if request.method == 'POST':
    activity_select = request.form.get("activity_select")
    distance = request.form.get("distance")
    activity = Activity(activity_type=activity_select,
                        distance=distance,
                        date_completed=datetime.datetime.now(),
                        user_id=current_user.id
                        )
    db.session.add(activity)
    db.session.commit()
    return redirect(url_for("activities"))

@app.route('/editactivity/<activity_id>', methods=['GET', 'POST'])
def edit_activity(activity_id):
  if request.method=='POST':
    activity_select = request.form.get("activity_select")
    distance = request.form.get("distance")
    activity = Activity.query.get(activity_id)
    activity.activity_type = activity_select
    activity.distance = distance
    db.session.commit()
    return redirect(url_for("activities"))
  else:
    activity = Activity.query.get(activity_id)
    return render_template('edit_activity.html',activity=activity)

@app.route('/removeactivity/<activity_id>', methods=['GET','POST'])
def remove_activity(activity_id):
  activity = Activity.query.get(activity_id)
  db.session.delete(activity)
  db.session.commit()
  return redirect(url_for("activities"))



# @app.route('edit')

if __name__ == '__main__':
  app.run(ssl_context="adhoc")
