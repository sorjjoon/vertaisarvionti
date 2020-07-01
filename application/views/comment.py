
from flask import render_template, redirect, url_for, request, Response, send_file
from flask import current_app as app
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError
import io
import datetime
import pytz
from timeit import default_timer as timer
from application.domain.comment import Comment, CommentJsonEncoder
from application import db
import io
import json

@app.route("/comment/new", methods=["POST"])
@login_required
def new_comment():
    text = request.form.get("comment","")
    target_string = request.form.get("target_string")
    if not target_string:
        return redirect(url_for("index"))
    comment_target = target_string[0]
    target_id = int(target_string[1:])
    if comment_target=="s":
        db.insert_comment(current_user.get_id(), text, submit_id=target_id)
    elif comment_target=="t":
        db.insert_comment(current_user.get_id(), text, task_id=target_id)
    elif comment_target =="a":
        db.insert_comment(current_user.get_id(), text, assignment_id=target_id)
    elif comment_target =="n":
        db.insert_comment(current_user.get_id(), text, answer_id=target_id)

    return redirect(request.form.get("origin", url_for("index")))


@app.route("/comment/get", methods=["GET"])
@login_required
def get_comments():
    comments = db.select_comments(current_user.get_id(),task_id=2)
    buffer = io.BytesIO()


@app.route("/update/comment")
def update_comment():
    text = request.form.get("comment")
    id = request.form.get("id")
    db.update_comment(id, current_user.get_id(),text=text)

    return redirect(request.form.get("origin", url_for("index")))

@app.route("/comment", methods = ["GET", "POST"])
@login_required
def comment():
    if request.method == "GET":
        return redirect(url_for("index"))
    
    text = request.form.get("text")
    next_url = request.form.get("next")
    try:
        c_id = request.form.get("id")
    except:
        return redirect(url_for("index"))
    visible = bool(request.form.get("vis"))
    if request.form.get("u"):
        db.update_comment(c_id, current_user.get_id(),text=text, visible=visible)