from flask import render_template, request, redirect, url_for
from flask_wtf import FlaskForm
#from application import db, app
from application import db
from flask import current_app as app, g
from wtforms import StringField, PasswordField, validators, ValidationError, BooleanField
from application.database._user_auth import AuthError, AccountLockedError

from flask_login import login_user, logout_user, login_required, current_user

import pytz



@app.route("/auth/logout")
@login_required
def logout_auth():
    app.logger.info("Logging out user %s", current_user.get_id())
    logout_user()
    return redirect(url_for("index"))





class LoginForm(FlaskForm):
    username = StringField("Käyttäjänimi", validators=[validators.DataRequired(message=None)])
    password = PasswordField("Salasana", validators=[validators.DataRequired(message=None)])  # TODO password strength

@app.route("/auth/login", methods=["GET", "POST"])
def login_auth():
    if request.method == "GET":
        
        return render_template("auth/login.html", form=LoginForm(), next = request.args.get("next"))
    error = None
    form = LoginForm(request.form)
    try:
        user = db.get_user(g.conn, form.username.data, form.password.data)
        if user is None:
            error = "Käyttäjänimi tai salasana on väärin"
    except AccountLockedError as r:
        
        app.logger.warning("Attempted login for locked username %s", form.username.data)
        locked_until = r.locked_until.astimezone(pytz.timezone("Europe/Helsinki"))
        print(locked_until)
        print(r.locked_until)
        error = "Tili on lukittu {} asti väärien salasanayritysten vuoksi".format(locked_until.strftime("%H:%M"))
    
    if error is not None:    
        return render_template("auth/login.html", form=form, error=error), 401

    login_user(user)
    app.logger.info("User " + form.username.data + " validated")
    if request.form.get("next"):
        try:
            return redirect(request.form.get("next"))
        except:
            pass
    return redirect(url_for("index"))





