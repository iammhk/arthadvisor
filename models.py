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
    risk_appetite = db.Column(db.String(50))  # e.g. 'Low', 'Medium', 'High'
    goal_short_term = db.Column(db.Text)
    goal_medium_term = db.Column(db.Text)
    goal_long_term = db.Column(db.Text)
    profile_pic = db.Column(db.String(256))  # Path to uploaded profile picture
    telegram_user_id = db.Column(db.String(32))  # Telegram user ID for bot messages
    # Add more fields as needed

class GPTTickerLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    system_prompt = db.Column(db.Text, nullable=False)
    ticker_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    global_advice_timestamp = db.Column(db.String(32), nullable=True)  # ISO format string

    user = db.relationship('User', backref=db.backref('gpt_ticker_logs', lazy=True))

class UserOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_id = db.Column(db.String(64), nullable=False)
    tradingsymbol = db.Column(db.String(32), nullable=False)
    transaction_type = db.Column(db.String(8), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    order_type = db.Column(db.String(16), nullable=False)
    status = db.Column(db.String(32), nullable=False)
    order_timestamp = db.Column(db.String(32), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def __repr__(self):
        return f'<UserOrder {self.order_id} {self.tradingsymbol} {self.status}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
