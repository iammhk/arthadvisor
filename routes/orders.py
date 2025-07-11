from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from .dashboard import get_kite_client
from models import UserOrder

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/orders')
@login_required
def show_orders():
    kite = get_kite_client()
    orders = []
    today_completed = []
    user_orders = []
    if kite:
        try:
            all_orders = kite.orders()
            from datetime import datetime
            import pytz
            # Filter for active (open) orders
            active_statuses = {'OPEN', 'TRIGGER PENDING', 'AMO REQ RECEIVED', 'AMO REQ PROCESSING'}
            orders = [
                {
                    'order_id': o['order_id'],
                    'tradingsymbol': o['tradingsymbol'],
                    'transaction_type': o['transaction_type'],
                    'quantity': o['quantity'],
                    'order_type': o['order_type'],
                    'status': o['status'],
                    'order_timestamp': o['order_timestamp'] if 'order_timestamp' in o else o.get('exchange_timestamp', '')
                }
                for o in all_orders if o['status'] in active_statuses
            ]
            # Completed orders placed today
            ist = pytz.timezone('Asia/Kolkata')
            today = datetime.now(ist).date()
            today_completed = [
                {
                    'order_id': o['order_id'],
                    'tradingsymbol': o['tradingsymbol'],
                    'transaction_type': o['transaction_type'],
                    'quantity': o['quantity'],
                    'order_type': o['order_type'],
                    'status': o['status'],
                    'order_timestamp': o['order_timestamp'] if 'order_timestamp' in o else o.get('exchange_timestamp', '')
                }
                for o in all_orders
                if o['status'] == 'COMPLETE' and (
                    (
                        'order_timestamp' in o and 
                        isinstance(o['order_timestamp'], str) and 
                        o['order_timestamp'] and 
                        datetime.fromisoformat(o['order_timestamp']).astimezone(ist).date() == today
                    )
                    or (
                        'exchange_timestamp' in o and 
                        isinstance(o['exchange_timestamp'], str) and 
                        o['exchange_timestamp'] and 
                        datetime.fromisoformat(o['exchange_timestamp']).astimezone(ist).date() == today
                    )
                )
            ]
        except Exception as e:
            flash(f'Error fetching orders from Zerodha: {e}', 'danger')
    # Fetch all orders placed by the user from the database
    user_orders = UserOrder.query.filter_by(user_id=current_user.id).order_by(UserOrder.created_at.desc()).all()
    return render_template('orders.html', orders=orders, today_completed=today_completed, user_orders=user_orders)
