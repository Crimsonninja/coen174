from models import Team, Activity, User
from sqlalchemy import func
# from app import db

# CONSTANTS
BIKE_GOAL = 112
RUN_GOAL = 26.2
SWIM_GOAL = 2.4

BIKE_WEIGHT = 0.4
RUN_WEIGHT = 0.3
SWIM_WEIGHT = 0.3

def total_user_swim(user_id):
  return Activity.query.filter_by(user_id = user_id) \
                .filter_by(activity_type = "swimming") \
                .with_entities(func.sum(Activity.distance)).scalar() or 0

def total_user_run(user_id):
  return Activity.query.filter_by(user_id = user_id) \
                .filter_by(activity_type = "running") \
                .with_entities(func.sum(Activity.distance)).scalar() or 0

def total_user_bike(user_id):
  return Activity.query.filter_by(user_id = user_id) \
                .filter_by(activity_type = "biking") \
                .with_entities(func.sum(Activity.distance)).scalar() or 0

def total_team_swim(team_id):
  users = User.query.filter_by(team_id = team_id).all()
  final_swim = 0
  for user in users:
    final_swim = final_swim + total_user_swim(user.id)
  return final_swim

def total_team_run(team_id):
  users = User.query.filter_by(team_id = team_id).all()
  final_run = 0
  for user in users:
    final_run = final_run + total_user_run(user.id)
  return final_run

def total_team_bike(team_id):
  users = User.query.filter_by(team_id = team_id).all()
  final_bike = 0
  for user in users:
    final_bike = final_bike + total_user_bike(user.id)
  return final_bike

# People are welcome to add more distance if they like, but team progress is capped so progress is
# not increased if more distance is added beyond the goals for each event
def team_progress(team_id):
  weighted_swim = total_team_swim(team_id)/SWIM_GOAL * SWIM_WEIGHT
  if weighted_swim > SWIM_WEIGHT:
    weighted_swim = SWIM_WEIGHT
  print(f'WEIGHTED SWIM: {weighted_swim}')
  weighted_run = total_team_run(team_id)/RUN_GOAL * RUN_WEIGHT
  if weighted_swim > RUN_WEIGHT:
    weighted_swim = RUN_WEIGHT
  print(f'WEIGHTED RUN: {weighted_run}')
  weighted_bike = total_team_bike(team_id)/BIKE_GOAL * BIKE_WEIGHT
  if weighted_swim > BIKE_WEIGHT:
    weighted_swim = BIKE_WEIGHT
  print(f'WEIGHTED BIKE: {weighted_bike}')

  return weighted_bike + weighted_run + weighted_run
