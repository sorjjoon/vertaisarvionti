from flask import render_template, request, redirect, url_for
from flask_wtf import FlaskForm
#from application import db, app
from application import db
from flask import current_app as app, g
from wtforms import StringField, PasswordField, validators, ValidationError, BooleanField


from flask_login import login_user, logout_user, login_required, current_user
from application.auth import account


@app.route("/auth/delete", methods=["POST", "GET"])
@login_required
def delete_user():
    if request.method == "GET":
        return redirect(url_for("index"))

    db.delete_user(g.conn, current_user.get_id())
    logout_user()
    return redirect(url_for("index"))


@app.route("/auth/logout")
@login_required
def logout_auth():
    app.logger.info("Logging out user %s", current_user.get_id())
    logout_user()
    return redirect(url_for("index"))



def username_free(form, field):
    if not db.check_user(g.conn, field.data):
        raise ValidationError('Käyttänimi on varattu')


class PasswordForm(FlaskForm):  # TODO add old password
    password1 = PasswordField("Uusi salasana", validators=[validators.DataRequired(message=None), validators.Length(
        min=5, max=50, message="Salasanan täytyy olla 8 - 50 merkkiä pitkä"), validators.EqualTo("password2", message='Salasanat eivät täsmää')])
    # Only password1 needs to be validated
    password2 = PasswordField("Toista salasana")


class UsernameUpdateForm(FlaskForm):
    username = StringField("Uusi käyttäjänimi", validators=[validators.DataRequired(message=None), validators.Length(
        min=5, max=30, message="Käyttäjänimen täytyy olla 5 - 30 merkkiä pitkä"), username_free])


    





def update_password(form):
    if request.method == "GET":
        return render_template("auth/newpass.html", form=PasswordForm(), username_form=UsernameUpdateForm())
    form = PasswordForm(request.form)
    if form.validate():
        # Doesn't matter if we use 1 or 2 (since we have validated them to be same)
        new_pass = request.form.get("password1")
        db.update_password(g.conn, current_user.get_id(), new_pass)
        logout_user()
        return redirect(url_for("auth/user_details.html"))

    else:
        return render_template("auth/user_details.html", form=form)


def update_username(form):
    if request.method == "GET":
        return render_template("auth/user_details.html", form=PasswordForm(), username_form=UsernameUpdateForm())
    form = UsernameUpdateForm(request.form)

    if not form.validate():
        return render_template("auth/user_details.html", form=PasswordForm(), username_form=form)
    else:
        db.update_username(g.conn, form.username.data, current_user.get_id())
        logout_user()
        return redirect(url_for("index"))