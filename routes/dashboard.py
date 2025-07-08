from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from kiteconnect import KiteConnect
import pandas as pd
from extensions import db
from models import User
import os

dashboard_bp = Blueprint('dashboard', __name__)

def get_kite_client():
    api_key = current_user.kite_api_key
    api_secret = current_user.kite_api_secret
    if not api_key or not api_secret:
        return None
    kite = KiteConnect(api_key=api_key)
    access_token = getattr(current_user, 'kite_access_token', None)
    if not access_token:
        return None
    kite.set_access_token(access_token)
    return kite

@dashboard_bp.route('/connect_zerodha')
@login_required
def connect_zerodha():
    api_key = current_user.kite_api_key
    if not api_key:
        flash('Please set your Kite API Key in your profile.', 'danger')
        return redirect(url_for('auth.profile'))
    kite = KiteConnect(api_key=api_key)
    login_url = kite.login_url()  # No redirect_uri argument
    return redirect(login_url)

@dashboard_bp.route('/zerodha_callback')
@dashboard_bp.route('/zerodha/callback')
@login_required
def zerodha_callback():
    api_key = current_user.kite_api_key
    api_secret = current_user.kite_api_secret
    request_token = request.args.get('request_token')
    if not request_token:
        flash('Zerodha login failed or cancelled.', 'danger')
        return redirect(url_for('dashboard.show_dashboard'))
    kite = KiteConnect(api_key=api_key)
    try:
        data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = data['access_token']
        # Store access_token in user profile
        current_user.kite_access_token = access_token
        db.session.commit()
        flash('Zerodha account connected successfully!', 'success')
    except Exception as e:
        flash(f'Failed to connect Zerodha: {e}', 'danger')
    return redirect(url_for('dashboard.show_dashboard'))

@dashboard_bp.route('/dashboard')
@login_required
def show_dashboard():
    kite = get_kite_client()
    stock_data = {}
    holdings = []
    zerodha_connected = False
    if kite:
        zerodha_connected = True
        try:
            holdings = kite.holdings()
            for h in holdings:
                stock_data[h['tradingsymbol']] = {
                    'current_price': h['last_price'],
                    'quantity': h['quantity'],
                    'avg_price': h['average_price']
                }
        except Exception as e:
            flash(f'Error fetching portfolio from Zerodha: {e}', 'danger')
    else:
        stock_data = {}
    market_indices = {
        'Nifty': {'value': 24000, 'change': 0.5},
        'Sensex': {'value': 80000, 'change': 0.3},
        'Bank Nifty': {'value': 52000, 'change': -0.2}
    }
    account_balance = 4200000
    weekly_profit = 27000
    return render_template('dashboard.html', 
                           stock_data=stock_data, 
                           account_balance=account_balance, 
                           weekly_profit=weekly_profit,
                           market_indices=market_indices,
                           zerodha_connected=zerodha_connected)