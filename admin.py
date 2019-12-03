# Simon Liu, Jonathan Trinh
# Summery: Add new admin
#Input: user id, User database
#Output:
from app import db
import sys
from models import User, Role

# admin_role = Role(name="admin")
# db.session.commit()

inp = sys.argv[1]
user = User.query.get(inp)
user.admin = True
db.session.commit()
