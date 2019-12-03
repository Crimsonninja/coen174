# Simon Liu, Jonathan Trinh
#Summery: Functions that determines what information should be loaded
#         into a page and how input should interact with the database
import os, json
import datetime
from collections import defaultdict
from flask import Flask, escape, request, redirect, render_template, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, asc
# from flask_security import roles_required, SQLAlchemyUserDatastore
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import *
# from flask_user import UserManager, roles_required
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
# from flask_security import roles_required
# from flask_security import SQLAlchemyUserDatastore
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

EVENT_START = datetime.datetime(2019, 11, 10)

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
)

nav.register_element('top', topbar)

nav.init_app(app)

from models import Team, User, Activity, User, Role


#Name:login manager
#Summery: get specific user data
#Input: user id
#Output: user data
@login_manager.user_loader
def load_user(user_id):
  return User.query.get(user_id)

#Name: Google authentication
#Summery: get google authentication
#Input:
#Output: get google authentication results
def get_google_provider_cfg():
  return requests.get(GOOGLE_DISCOVERY_URL).json()

#Name: Login from Google
#Summery: Login with Google and get user data
#Input:
#Output: user data from Google
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
        prompt='consent'
    )
    return redirect(request_uri)

#Name:Login function
#Summery: Calls Google Login and if correct shows user homepage
#Input:
#Output: show homepage if correct, else show login page again
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

  current_user.token = token_response

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
      users_email = userinfo_response.json()["email"]
      users_first_name = userinfo_response.json()["given_name"]
      users_last_name = userinfo_response.json()["family_name"]
  else:
      return "User email not available or not verified by Google.", 400

  # Doesn't exist? Add it to the database.
  if not User.query.filter(User.email==users_email).all():
    user = User(first_name=users_first_name, last_name=users_last_name, email=users_email, active=True, admin=False)
    db.session.add(user)
    db.session.commit()
  else:
    user = User.query.filter(User.email==users_email).first()

  # Begin user session by logging the user in
  login_user(user)

  # Send user back to homepage
  return redirect(url_for("index"))

#Name: Before Request
#Summery: handle https & http exchange
#Input:
#Output: https page
@app.before_request
def before_request():
    if not request.is_secure and app.env != "development":
        url = request.url.replace("http://", "https://", 1)
        code = 302
        return redirect(url, code=code)

#Name: Logout
#Summery: logout of the application
#Input:
#Output: show login page
@app.route("/logout")
@login_required
def logout():
  logout_user()
  session.clear()
  return redirect(url_for("index"))

#Name: Login page
#Summery: the welcome login page
#Input: Google's login information
#Output: Load the dashboard if correct, else show welcome page
@app.route('/')
def index():
  if current_user.is_authenticated:
    team=None
    teammates=None
    team_dict={}
    is_admin = False
    if current_user.team_id:
      team=Team.query.get(current_user.team_id)
      teammates=User.query.filter_by(team_id = current_user.team_id).filter(User.id != current_user.id).all()
    if current_user.admin:
      is_admin=True

    return render_template('index.html',
                          user_first_name=current_user.first_name,
                          user_bike=current_user.total_user_bike(),
                          user_run=current_user.total_user_run(),
                          user_swim=current_user.total_user_swim(),
                          team=team,
                          teammates=teammates,
                          is_admin=is_admin
                          )
  else:
    return render_template('welcome.html')

#Name: Hello Name
#Summery: Get user name and show it
#Input: User name
#Output: Show the username in the format
@app.route('/<name>')
def hello_name(name):
  return "Hello {}!".format(name)

#Name: Leaderboard
#Summery: Get the leaderboard of the event
#Input: Team database
#Output: sorted list of teams that are approved
@app.route('/leaderboard')
def leaderboard():
  if not current_user.is_authenticated:
    return redirect(url_for("index"))
  else:
    teams=Team.query.filter(Team.status == 'approved').order_by(Team.progress.desc(),Team.date_completed.asc()).all()
    for team in teams:
      print(team.team_name)
    return render_template('leaderboard.html',teams=teams, event_start=EVENT_START)

#------------------------------------ Team Methods ------------------------------------

#Name: Teams
#Summery: Show the list of team avaliable to join
#Input: Team database
#Output: a list of teams avaliable for user to join
@app.route('/teams')
def teams():
  if not current_user.is_authenticated:
    return redirect(url_for("index"))
  else:
    valid_team_list = Team.query.filter(Team.member_count < 3).filter(Team.id != current_user.team_id).all()
    return render_template('teams.html', team_exist=False, team_list = valid_team_list, has_current_team=current_user.team_id)

#Name: Create team
#Summery: Create a new unique team
#Input: User team name, Team database
#Output: If successful, show the dashboard with the new team name
#         and stats. If not show team page again
@app.route('/addteam', methods=['GET','POST'])
def create_team():
    if request.method == 'POST':
        team_name = request.form.get("newteam")
        if len(team_name) > 20:
          valid_team_list = Team.query.filter(Team.member_count < 3).filter(Team.id != current_user.team_id).all()
          return render_template('teams.html', team_exist=False, team_list = valid_team_list, has_current_team=current_user.team_id)        # If team exists in database
        no_spaces = team_name.replace(" ","")
        if no_spaces == "":
          valid_team_list = Team.query.filter(Team.member_count < 3).filter(Team.id != current_user.team_id).all()
          return render_template('teams.html', team_exist=False, team_list = valid_team_list, has_current_team=current_user.team_id)        # If team exists in database
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
                    old_team.progress = old_team.team_progress()
                    if old_team.progress >= 100:
                        old_team.date_completed = datetime.datetime.now()
                    else:
                        old_team.date_completed = None
            team = Team(team_name=team_name, member_count=1,status='pending')
            db.session.add(team)
            db.session.commit()
            current_user.team_id = Team.query.filter(team_name == Team.team_name).first().id
            current_user.team.progress = current_user.team.team_progress()
            if current_user.team.progress >= 100:
                current_user.team.date_completed = datetime.datetime.now()
            else:
                current_user.team.date_completed = None
            db.session.commit()
            return redirect(url_for("index"))

#Name: Join Team
#Summery: Join any team that are listed
#Input: id of the team to join, Team database
#Output: Show the dahsboard with team stats and name of the team user
#         joined
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
            old_team.progress = old_team.team_progress()
            if old_team.progress >= 100:
              old_team.date_completed = datetime.datetime.now()
            else:
              old_team.date_completed = None

    team = Team.query.get(team_id)
    team.member_count = team.member_count + 1
    current_user.team_id = team_id
    db.session.commit()
    current_user.team.progress = current_user.team.team_progress()
    print(current_user.team.progress)
    if current_user.team.progress >= 100:
        current_user.team.date_completed = datetime.datetime.now()
    else:
        current_user.team.date_completed = None
    db.session.commit()
    return redirect(url_for("index"))

#Name: Quit Team
#Summery: Let user quit current team
#Input: Team database
#Output: Show dashboard, but without old team's data
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
            old_team.progress = old_team.team_progress()
            if old_team.progress >= 100:
                old_team.date_completed = datetime.datetime.now()
            else:
                old_team.date_completed = None
        db.session.commit()
    return redirect(url_for("index"))

#------------------------------------ Activity Methods ------------------------------------
#Name: Activities
#Summery: Show the user's activity and allow user to add new activity
#Input: Activity database, user id
#Output: the activity page for user
@app.route('/activities')
def activities():
  if not current_user.is_authenticated:
    return redirect(url_for("index"))
  else:
    valid_activities_list = Activity.query.filter_by(user_id = current_user.id).order_by(desc(Activity.date_completed)).all()
    return render_template('activities.html', activities_list=valid_activities_list)

#Name: Add Activity
#Summery: Let user to add new activities
#Input: User new activity input, Activity database
#Output: User dashboard when successful
@app.route('/addactivity', methods=['GET', 'POST'])
def add_activity():
  if not current_user.is_authenticated:
    return redirect(url_for("index"))
  else:
    if request.method == 'POST':
      activity_select = request.form.get("activity_select")
      if activity_select not in ['biking', 'running','swimming']:
       return redirect(url_for("activities"))
      distance = request.form.get("distance")
      if not distance:
        print("NOT DISTANCE")
        return redirect(url_for("activities"))
      if not isinstance(distance, float):
        print("NOT INTEGER")
        return redirect(url_for("activities"))
      if distance < 0 or distance > 250:
        print("NOT BETWEEN RANGE")
        return redirect(url_for("activities"))

      activity = Activity(activity_type=activity_select,
                          distance=distance,
                          date_completed=datetime.datetime.now(),
                          user_id=current_user.id,
                          status="pending"
                          )
      db.session.add(activity)
      db.session.commit()
      if current_user.team:
        current_user.team.progress = current_user.team.team_progress()
        if current_user.team.progress >= 100:
            current_user.team.date_completed = datetime.datetime.now()
        else:
            current_user.team.date_completed = None
        db.session.commit()
      return redirect(url_for("activities"))

#Name: Edit Activity
#Summery: Allow user to edit their acitivity perviously added
#Input: Activity Database, activity id
#Output: Show Acitivity Page
@app.route('/editactivity/<activity_id>', methods=['GET', 'POST'])
def edit_activity(activity_id):
  if not current_user.is_authenticated:
    return redirect(url_for("index"))
  else:
    if request.method=='POST':
      activity_select = request.form.get("activity_select")
      distance = request.form.get("distance")
      activity = Activity.query.get(activity_id)
      activity.activity_type = activity_select
      activity.distance = distance
      activity.status = "pending"
      db.session.commit()
      if current_user.team:
        current_user.team.progress = current_user.team.team_progress()
        if current_user.team.progress >= 100:
            current_user.team.date_completed = datetime.datetime.now()
        else:
            current_user.team.date_completed = None
        db.session.commit()
      return redirect(url_for("activities"))
    else:
      activity = Activity.query.get(activity_id)
      return render_template('edit_activity.html',activity=activity)
#Name: Remove Activity
#Summery: Allow user to delete an activity
#Input: activity id, Activity database
#Output: Activity page
@app.route('/removeactivity/<activity_id>', methods=['GET','POST'])
def remove_activity(activity_id):
  activity = Activity.query.get(activity_id)
  db.session.delete(activity)
  db.session.commit()
  if current_user.team:
      current_user.team.progress = current_user.team.team_progress()
      if current_user.team.progress >= 100:
          current_user.team.date_completed = datetime.datetime.now()
      else:
          current_user.team.date_completed = None
      db.session.commit()
  return redirect(url_for("activities"))

#============================= Admin Methods =============================
#Name: Admin Dashboard
#Summery: Display all teams and users to admin
#Input: Team and User Database
#Output: Admin dashboard
@app.route('/admin')
def admin_dashboard():
  if current_user.is_authenticated:
    if current_user.admin:
      team_list = Team.query.order_by(asc(Team.id)).all()
      user_list = User.query.order_by(asc(User.id)).all()
      return render_template('admin_dashboard.html',user_first_name=current_user.first_name,team_list=team_list,user_list=user_list)
    else:
      return render_template('error.html')
  else:
    return render_template('welcome.html')

#Name: Admin Edit Teams
#Summery: Show all the memebers in a team and allow admin to kick
#         memeber out of the team
#Input: team id, Team Database
#Output: admin team edit page
@app.route('/admin/edit_team/<teamid>', methods=['GET', 'POST'])
def admin_edit_team(teamid):
    print(teamid)
    team = Team.query.get(teamid)
    users = team.users
    return render_template('admin_edit_team.html', team = team, users = users)

#Name: Admin kicked member
#Summery: Kick memeber from team
#Input: user id, Team database
#Output: admin dashboard
@app.route('/admin/edit_team/kicked/<userid>', methods=['GET', 'POST'])
def admin_kicked_member(userid):
    current_user = User.query.get(userid)
    old_team_id = current_user.team_id
    if old_team_id:
        current_user.team_id=None
        if Team.query.get(old_team_id).member_count == 1:
            Team.query.filter_by(id=old_team_id).delete()
        else:
            old_team = Team.query.get(old_team_id)
            old_team.member_count = old_team.member_count - 1
            old_team.progress = old_team.team_progress()
            if old_team.progress >= 100:
                old_team.date_completed = datetime.datetime.now()
            else:
                old_team.date_completed = None
        db.session.commit()
    return redirect(url_for("admin_dashboard"))

#Name: admin approve team
#Summery: Approve the team
#Input: team id
#Output: Admin dashboard
@app.route('/admin/edit_team/approve/<teamid>', methods=['GET', 'POST'])
def admin_approve_team(teamid):
    team = Team.query.get(teamid)
    team.status = 'approved'
    db.session.commit()
    team.progress = team.team_progress()
    print(f'Admin approving team with progress: {team.progress}')
    if team.progress >= 100:
      team.date_completed = datetime.datetime.now()
    else:
      team.date_completed = None
    db.session.commit()
    return redirect(url_for("admin_dashboard"))

#Name: Admin Reject team
#Summery: Reject the team name
#Input: teamid
#Output: Admin Dashboard
@app.route('/admin/edit_team/reject/<teamid>', methods=['GET', 'POST'])
def admin_reject_team(teamid):
    team = Team.query.get(teamid)
    team.status = 'rejected'
    db.session.commit()
    return redirect(url_for("admin_dashboard"))

#Name: Admin edit user
#Summery: Get user information for add to a team
#Input: user_id, Team Database
#Output: admine edit user page
@app.route('/admin/edit_user/<userid>', methods=['GET', 'POST'])
def admin_edit_user(userid):
    user = User.query.get(userid)
    valid_team_list = Team.query.filter(Team.member_count < 3).filter(Team.id != user.team_id).all()
    return render_template('admin_edit_user.html', team_exist=False, team_list = valid_team_list, has_current_team=user.team_id,user=user)

#Name: Admin Create team
#Summery: Allow admin to create team for a user
#Input: userid, Team Database
#Output: Admin Dashboard
@app.route('/admin/edit_user/addteam/<userid>', methods=['GET','POST'])
def admin_create_team(userid):
    user = User.query.get(userid)
    if request.method == 'POST':
        team_name = request.form.get("newteam")
        # If team exists in database
        if Team.query.filter(team_name == Team.team_name).all():
            return render_template('teams.html', team_exist=True)
        else:
            old_team_id = user.team_id
            if old_team_id:
                user.team_id=None
                if Team.query.get(old_team_id).member_count == 1:
                    db.session.delete(Team.query.get(old_team_id))
                else:
                    old_team = Team.query.get(old_team_id)
                    old_team.member_count = old_team.member_count - 1
                    old_team.progress = old_team.team_progress()
                    if old_team.progress >= 100:
                        old_team.date_completed = datetime.datetime.now()
                    else:
                        old_team.date_completed = None
            team = Team(team_name=team_name, member_count=1,status='pending')
            db.session.add(team)
            db.session.commit()
            user.team_id = Team.query.filter(team_name == Team.team_name).first().id
            user.team.progress = user.team.team_progress()
            if user.team.progress >= 100:
                user.team.date_completed = datetime.datetime.now()
            else:
                user.team.date_completed = None
            db.session.commit()
            return redirect(url_for("admin_dashboard"))

#Name: Admin join team
#Summery: Allow admin to add user to a existing team
#Input: user_id, Team Database
#Output: admin dashboard
@app.route('/admin/edit_user/jointeam/<team_id>/<userid>', methods=['GET', 'POST'])
def admin_join_team(team_id,userid):
    user = User.query.get(userid)
    old_team_id = user.team_id
    if old_team_id:
        user.team_id=None
        if Team.query.get(old_team_id).member_count == 1:
            Team.query.filter_by(id=old_team_id).delete()
        else:
            old_team = Team.query.get(old_team_id)
            old_team.member_count = old_team.member_count - 1

    team = Team.query.get(team_id)
    team.member_count = team.member_count + 1
    user.team_id = team_id
    db.session.commit()
    user.team.progress = user.team.team_progress()
    if user.team.progress >= 100:
        user.team.date_completed = datetime.datetime.now()
    else:
        user.team.date_completed = None
    db.session.commit()
    return redirect(url_for("admin_dashboard"))

#Name: Admin Logs
#Summery: Show all user activity inputs
#Input: Acitivity Database
#Output: If user is admin, whow admin log page. If not, welcome page
@app.route('/admin/logs')
def admin_logs():
  if current_user.is_authenticated:
    if current_user.admin:
      activity_list = Activity.query.order_by(desc(Activity.date_completed)).all()
      return render_template('admin_logs.html',activity_list=activity_list)
    else:
      return render_template('error.html')
  else:
    return render_template('welcome.html')

#Name: Approve Activity
#Summery: Allow Admin to approve acitivity
#Input: activity id, Activity Database
#Output: admin log page
@app.route('/admin/logs/approve/<activity_id>', methods=['GET', 'POST'])
def approve_activity(activity_id):
    activity = Activity.query.get(activity_id)
    activity.status = 'approved'
    db.session.commit()
    user = activity.user
    print(f'The User of Approving Activity is: {user.email}')
    if user.team:
      user.team.progress = user.team.team_progress()
      if user.team.progress >= 100:
          user.team.date_completed = datetime.datetime.now()
      else:
          user.team.date_completed = None
      db.session.commit()
      return redirect(url_for("admin_logs"))

#Name: Reject Activity
#Summery: Allow Admin to reject acitivity
#Input: activity_id, Activity Database
#Output: Admin log page
@app.route('/admin/logs/reject/<activity_id>', methods=['GET', 'POST'])
def reject_activity(activity_id):
    activity = Activity.query.get(activity_id)
    activity.status = 'rejected'
    db.session.commit()
    return redirect(url_for("admin_logs"))

if __name__ == '__main__':
  app.run(ssl_context="adhoc")
