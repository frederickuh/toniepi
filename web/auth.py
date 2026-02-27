from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user

login_manager = LoginManager()
login_manager.login_view = "login"

# Simple single-user system (upgradeable later)
USERNAME = "admin"
PASSWORD = "changeme"

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

def authenticate(username, password):
    if username == USERNAME and password == PASSWORD:
        return User(username)
    return None