from functools import wraps
from flask import session, flash, redirect, url_for # type: ignore

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session or 'roles' not in session['user'] or 'admin' not in session['user']['roles']:
            flash("Accesso non autorizzato.", "danger")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function
