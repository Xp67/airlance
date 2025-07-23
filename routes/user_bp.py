from flask import Blueprint, redirect, request, session, url_for, render_template  # type: ignore


user_bp = Blueprint('user', __name__,url_prefix='/user')

@user_bp.route('/profilo')
def profilo():
    return render_template('profilo.html')