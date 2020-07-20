from flask import render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm
#from application import db, app
from application import db
from flask import current_app as app, g
from wtforms import StringField, PasswordField, validators, ValidationError, BooleanField
from wtforms.widgets import PasswordInput
from flask_login import login_user, logout_user, login_required, current_user, fresh_login_required
from sqlalchemy.exc import IntegrityError


def username_free(form, field):
    print("checking usernmae")
    if not db.check_user(g.conn, field.data):
        
        raise ValidationError('Käyttänimi on varattu')





class RegisterForm(FlaskForm):
    username = StringField("Käyttäjänimi", validators=[validators.DataRequired(message="Käyttäjänimen täytyy olla 5 - 30 merkkiä pitkä"), validators.Length(
        min=5, max=30, message="Käyttäjänimen täytyy olla 5 - 30 merkkiä pitkä"), username_free])
    password = StringField("Salasana", widget=PasswordInput(hide_value=False), validators=[validators.DataRequired(message="Salasanan täytyy olla 8 - 50 merkkiä pitkä"), validators.Length(
        min=8, max=50, message="Salasanan täytyy olla 8 - 50 merkkiä pitkä")])  # TODO password strength
    
    password2 = StringField("Toista salasana", widget=PasswordInput(hide_value=False), validators=[validators.DataRequired(message=None), validators.EqualTo("password", message='Salasanat eivät täsmää')])    
    first_name =  StringField("Etunimi", validators=[validators.DataRequired(message="Etunimi ei voi olla tyhjä"), validators.Length(
        min=1, max=30, message="Etunimi voi olla enintään 30 merkkiä")])
    last_name =  StringField("Sukunimi", validators=[validators.DataRequired(message="Sukunimi ei voi olla tyhjä"), validators.Length(
        min=1, max=50, message="Sukunimi voi olla enintään 50 merkkiä")])
    student = BooleanField("Olen opiskelija ", default="checked")

    class Meta:
        csrf = False



@app.route("/auth/user/", methods = ["GET", "POST"])
@fresh_login_required
def user_details():
    if request.method == "GET":
        return render_template("auth/user_details.html", form=RegisterForm())
    else:
        form = RegisterForm(request.form)
        errors = []
        
        if request.form.get("details"):
            app.logger.info("updating details for user %s", current_user.get_id())
            

            new_username = form.username.data
            new_values = {}
            if new_username != current_user.name:
                app.logger.info("Updating username")
                if not form.username.validate(form):
                    errors+=form.username.errors
                else:
                    new_values["username"]=new_username
            
            if form.first_name.data != current_user.first_name:
                app.logger.info("Updating firstname")
                if not form.first_name.validate(form):
                    
                    errors+=form.first_name.errors
                else:
                    new_values["first_name"]=form.first_name.data

            if form.last_name.data != current_user.last_name:
                app.logger.info("Updating lastname")
                if not form.last_name.validate(form):
                    errors += form.last_name.errors
                else:
                    new_values["last_name"]=form.last_name.data

            if errors:
                app.logger.info("invalid user input, errors %s", errors)
                return render_template("auth/user_details.html", errors=errors, form=form)
            else:
                app.logger.info("attempting to update user details, new details %s", new_values)
                try:
                    db.update_user(g.conn, current_user.get_id(), **new_values)
                    app.logger.info("update success!")
                    
                except IntegrityError as _:
                    app.logger.warning("username taken, this shouldn't happen since we validate username to be free", exc_info=True)
                    errors.append("Käyttäjänimi on varattu")
                    return render_template("auth/user_details.html", errors=errors, form=form)
        elif request.form.get("update_password"):
            app.logger.info("updating password for user %s", current_user.get_id())

            if form.password.validate(form) and form.password2.validate(form):
                db.update_password(g.conn, current_user.get_id(), form.password.data)
                
                app.logger.info("password for user %s updated!", current_user.get_id())
                logout_user()
            else:
                errors+=form.password.errors
                errors+=form.password2.errors
                return render_template("auth/user_details.html", password_errors=errors, form=form)

        else: #this should only happen, if user took name tag from submit button for some reason
            app.logger.warning("submit name not found in request form")
    return redirect(url_for("user_details"))
        



@app.route("/auth/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("auth/register.html", form=RegisterForm())
    form = RegisterForm(request.form)
    app.logger.info("attempting new register")
    if not form.validate():  # form validation checks if username is free
        app.logger.info("Validatation failed")
        return render_template("auth/register.html", form=form), 409
    try:
        app.logger.info("Validatation success, attempting insert. New username %s", form.username.data)
        if form.student.data:
            db.insert_user(g.conn, form.username.data, form.password.data, form.first_name.data.capitalize, form.last_name.data)
        else: 
            db.insert_user(g.conn, form.username.data, form.password.data, form.first_name.data, form.last_name.data, role="TEACHER")
        app.logger.info("Insert success!")
        return redirect(url_for("index"))
    except ValueError:
        app.logger.info("Insert failed, this shouldn't happen, form should check if username is free")
        return render_template("auth/register.html", form=RegisterForm(), error="Username in use"), 422

