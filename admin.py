from app import db
import sys
from models import User, Role

# admin_role = Role(name="admin")
# db.session.commit()

inp = sys.argv[1]
user = User.query.get(inp)
user.admin = True
db.session.commit()
