from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from forms import SettingsForm
from models import User

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    form = SettingsForm(obj=current_user)
    if form.validate_on_submit():
        current_user.risk_appetite = form.risk_appetite.data
        current_user.kite_api_key = form.kite_api_key.data
        current_user.kite_api_secret = form.kite_api_secret.data
        current_user.goal_short_term = form.goal_short_term.data
        current_user.goal_medium_term = form.goal_medium_term.data
        current_user.goal_long_term = form.goal_long_term.data
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('settings.settings'))
    return render_template('settings.html', form=form)
