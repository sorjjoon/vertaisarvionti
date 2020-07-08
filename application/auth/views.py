from flask import render_template, request, redirect, url_for
from application import db

from flask import current_app as app, g
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


@app.route("/auth/")
@login_required
def user_details():
    return redirect(url_for("index"))