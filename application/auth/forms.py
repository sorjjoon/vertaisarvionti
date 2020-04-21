from flask import render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm
#from application import db, app
from application import db
from flask import current_app as app
from wtforms import StringField, PasswordField, validators, ValidationError, BooleanField

from flask_login import login_user, logout_user, login_required, current_user
from application.auth import account


def username_free(form, field):
    if not db.check_user(field.data):
        raise ValidationError('Käyttänimi on varattu')


class PasswordForm(FlaskForm):  # TODO add old password
    password1 = PasswordField("New Password", validators=[validators.DataRequired(message=None), validators.Length(
        min=5, max=50, message="Password must be between 5 and 50 characters"), validators.EqualTo("password2", message='Passwords must match')])
    # Only password1 needs to be validated
    password2 = PasswordField("Confirm Password")


class UsernameUpdateForm(FlaskForm):
    username = StringField("Username", validators=[validators.DataRequired(message=None), validators.Length(
        min=5, max=30, message="Username must be between 5 and 30 characters"), username_free])


class RegisterForm(FlaskForm):
    username = StringField("Käyttäjänimi", validators=[validators.DataRequired(message=None), validators.Length(
        min=5, max=30, message="Käyttäjänimen täytyy olla 5 - 30 merkkiä pitkä"), username_free])
    password = PasswordField("Salasana", validators=[validators.DataRequired(message=None), validators.Length(
        min=8, max=50, message="Salasanan täytyy olla 8 - 30 merkkiä pitkä")])  # TODO password strength
    password2 = PasswordField("Toista salasana", validators=[validators.DataRequired(message=None), validators.EqualTo("password", message='Salasanat eivät täsmää')])    
    first_name =  StringField("Etunimi", validators=[validators.DataRequired(message=None)])
    last_name =  StringField("Sukunimi", validators=[validators.DataRequired(message=None)])
    student = BooleanField("Olen opiskelija ", default="checked")

    class Meta:
        csrf = False


class LoginForm(FlaskForm):
    username = StringField("Käyttäjänimi", validators=[validators.DataRequired(message=None)])
    password = PasswordField("Salasana", validators=[validators.DataRequired(message=None)])  # TODO password strength


@app.route("/auth/update/username", methods=["GET", "POST"])
@login_required
def update_username():
    if request.method == "GET":
        return render_template("auth/newpass.html", form=PasswordForm(), username_form=UsernameUpdateForm())
    form = UsernameUpdateForm(request.form)

    if not form.validate():
        return render_template("auth/newpass.html", form=PasswordForm(), username_form=form)
    else:
        db.update_username(form.username.data, current_user.get_id())
        logout_user()
        return redirect(url_for("index"))


@app.route("/auth/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("auth/register.html", form=RegisterForm())
    form = RegisterForm(request.form)
    if not form.validate():  # form validation checks if username is free
        return render_template("auth/register.html", form=form), 409
    try:
        
        if form.student.data:
            db.insert_user(form.username.data, form.password.data, form.first_name.data, form.last_name.data)
        else: 
            db.insert_user(form.username.data, form.password.data, form.first_name.data, form.last_name.data, role="TEACHER")
        return redirect(url_for("index"))
    except ValueError:
        return render_template("auth/register.html", form=RegisterForm(), error="Username in use"), 422


@app.route("/auth/login", methods=["GET", "POST"])
def login_auth():
    if request.method == "GET":
        print(db.engine)
        
        return render_template("auth/login.html", form=LoginForm(), next = request.args.get("next"))

    form = LoginForm(request.form)

    user = db.get_user(form.username.data, form.password.data)
    if user is None:
        return render_template("auth/login.html", form=form, error="No such username or password"), 401

    login_user(user)
    print("User " + form.username.data + " validated")
    if request.form.get("next"):
        try:
            return redirect(request.form.get("next"))
        except:
            pass
    return redirect(url_for("index"))


@app.route("/user", methods=["GET", "POST"])
@login_required
def update_password():

    if request.method == "GET":
        return render_template("auth/newpass.html", form=PasswordForm(), username_form=UsernameUpdateForm())
    form = PasswordForm(request.form)
    if form.validate():
        # Doesn't matter if we use 1 or 2 (since we have validated them to be same)
        new_pass = request.form.get("password1")
        db.update_password(current_user.get_id(), new_pass)
        logout_user()
        return redirect(url_for("index"))

    else:
        return render_template("auth/newpass.html", form=form)
