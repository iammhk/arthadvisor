from extensions import db, login_manager
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    full_name = db.Column(db.String(150))
    email = db.Column(db.String(150))
    phone = db.Column(db.String(20))
    kite_api_key = db.Column(db.String(100))
    kite_api_secret = db.Column(db.String(100))
    kite_access_token = db.Column(db.String(200))
    # Add more fields as needed

class GPTTickerLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    system_prompt = db.Column(db.Text, nullable=False)
    ticker_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    global_advice_timestamp = db.Column(db.String(32), nullable=True)  # ISO format string

    user = db.relationship('User', backref=db.backref('gpt_ticker_logs', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
