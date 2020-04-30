from flask import render_template, request, redirect, url_for
from application import db
#from application import db, app
from flask import current_app as app
from flask_login import login_user, logout_user, login_required, current_user
from application.auth import account


@app.route("/auth/delete", methods=["POST", "GET"])
@login_required
def delete_user():
    if request.method == "GET":
        return redirect(url_for("index"))

    db.delete_user(current_user.get_id())
    logout_user()
    return redirect(url_for("index"))


@app.route("/auth/logout")
@login_required
def logout_auth():
    logout_user()
    return redirect(url_for("index"))
