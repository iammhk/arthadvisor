from flask import Flask, render_template
from extensions import db, login_manager, limiter, bcrypt, start_scheduler  # removed mail
from flask_migrate import Migrate
from routes.auth import auth_bp
from routes.core import core_bp
from routes.dashboard import dashboard_bp
from routes.predictions import predictions_bp
from routes.charts import charts_bp  
from routes.backtest import backtest_bp
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config.from_object('config.Config')

db.init_app(app)
# mail.init_app(app)  # Removed
login_manager.init_app(app)
limiter.init_app(app)
bcrypt.init_app(app)
migrate = Migrate(app, db)

login_manager.login_view = 'auth.login'

app.register_blueprint(auth_bp)
app.register_blueprint(core_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(predictions_bp) 
app.register_blueprint(charts_bp)  
app.register_blueprint(backtest_bp)


@app.route('/')
def index():
    return render_template('index.html')

@app.context_processor
def inject_current_year():
    return {'current_year': datetime.now().year}

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        start_scheduler()  # Start the scheduler
    app.run(debug=True)
