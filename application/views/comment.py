
from flask import render_template, redirect, url_for, request, Response, send_file, abort, jsonify
from flask import current_app as app, g
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError
import io
from datetime import datetime
import pytz
from timeit import default_timer as timer
from application.domain.comment import Comment

from database import db
import io
import json
import os
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, validators, ValidationError, BooleanField
from wtforms.widgets import PasswordInput
import html
from application.views.utils import get_file_download_link

# data = json.dumps(comments, cls=DomainJsonEncoder)
            
            # response = app.response_class(
            #     response=data,
            #     status=200,
            #     mimetype='application/json'
            # )
            # return response
# class CommentForm(FlaskForm):
#     text = StringField("text", validators=[validators.DataRequired()])
#     comment_target = StringField("comment_target", validators=[validators.DataRequired()])
#     class Meta:
#         csrf = False
@app.route("/comment", methods=["GET","DELETE", "POST"])
@login_required
def comment():
    if request.method =="GET":
        return get_comments()
    elif request.method =="DELETE":
        return delete_comment()
    elif request.method == "POST":
        if request.form.get("comment_id") and int(request.form.get("comment_id")):
            return update_comment()
        elif request.form.get("comment_target"):
            return new_comment()
        else:
            app.logger.error("POST request to comment without correct arguments")
            app.logger.error(request.form)
            return Response("", 400)
    else:
        raise ValueError("This shouldn't happen, flask allowed unallowed method")
        


def delete_comment():
    db.delete_comment(g.conn, request.args.get("id"), current_user.get_id())
    return Response("", 200)


def get_comments():
    try:
        comment_target = request.headers.get("X-Comment-Target")
        id = int(comment_target[(comment_target.index(":")+1):])
        if "s" in comment_target:
            if "ts" in comment_target:
                submit = db.get_simple_submit(g.conn,
                                                current_user.get_id(), id)
                submit_id = int(submit.id)
            elif "s" in comment_target:  
                submit_id = id
            else:
                raise ValueError("invalid comment target "+comment_target)
            comments = db.select_comments(g.conn,
                                            current_user.get_id(), submit_id=submit_id)

        elif "c" in comment_target:
            comments = db.select_comments(
                g.conn, current_user.get_id(), course_id=id)
        else:
            app.logger.error(
                "Comment_target %s not found, or invalid format", comment_target)
            return Response("", 400)
        for c in comments:
            
            c.is_owner = current_user.get_id()==c.owner_id
            for f in c.files:
                f.link=get_file_download_link(f, target="_blank", icon_size="md")
            c.set_timezones("Europe/Helsinki")
        if request.headers.get("Accept") == "application/json":
            return jsonify(comments)
            
        elif request.headers.get("Accept") == "text/html":
            return render_template("comment/post_list_template.html", comments=comments)
        else:
            app.logger.warning("Accept header missing, guessing html!")
            return render_template("comment/post_list_template.html", comments=comments)
    except Exception as _:
        app.logger.error("Failed geting comments from header %s", comment_target, exc_info=True)
        return Response("", 400)


def update_comment():
    deleted_files = request.form.getlist("del_files")
    id = request.form["comment_id"]
    new_text = request.form.get("text")
    new_files = request.files.getlist("files")
    fails =[]
    for file in new_files:
        file.seek(0, os.SEEK_END)        
        size = file.tell()
        file.seek(0)
        if size > 1024*1024*30:
            fails.append(file.filename)
            app.logger.warning("User attempted to upload too large a file %s", file.filename)
    if not fails:
        db.update_comment(g.conn, id, current_user.get_id(), text=new_text, reveal=None, new_files=new_files, delete_old_files=deleted_files)

        return Response("", 200)
    else: 
        return Response(",".join(fails), 403)
    



def new_comment():
    """Valid comment-targets s:submit_id, c:course_id, ts:submit_for_this_task_id 


    Returns:
        [Response]: [description]
    """
    try:
        comment_target = request.form["comment_target"]
        insert_dic = {}
        insert_dic["text"] = html.escape(request.form["text"], quote=False)
        id = int(comment_target[(comment_target.index(":")+1):])
        if request.form.get("reveal_after"):
            pass
        else:
            raw_date = request.form["reveal_date"]
            raw_time = request.form.get("reveal_time")
            if not raw_time:
                raw_time="23:59"
            raw_time = raw_time.replace(".", ":")
            
            try:
                insert_dic["reveal"] = (pytz.timezone("Europe/Helsinki").localize(datetime.strptime(raw_date+" "+raw_time, '%Y-%m-%d %H:%M'))).astimezone(pytz.UTC)
            except ValueError as _:
                app.logger.error("Given date %s info or time info %s was invalid format", raw_date, raw_time, exc_info=True)
                return Response("Invalid date/time", 400)
                
        if "ts" in comment_target:
            submit = db.get_simple_submit(
                g.conn, current_user.get_id(), id)
            if submit:
                insert_dic["submit_id"] = int(submit.id)
            else:
                app.logger.error(
                    "Tried to insert comment for invalid submit id %s comment_target: %s", id, comment_target)
                return Response("", 409)
        elif "s" in comment_target:
            insert_dic["submit_id"] = id
        elif "c" in comment_target:
            insert_dic["course_id"] = id
        else:
            app.logger.error(
                "Comment_target %s not found, or invalid format", comment_target)
            return Response("Comment_target not found", 400)

        insert_dic["user_id"] = current_user.get_id()

        db.insert_comment_dict(
            g.conn, insert_dic, files=request.files.getlist("files"))
        return Response("", 200)

    except Exception:
        app.logger.error("Error saving user json for method %s ",
                         request.method, exc_info=True)
        app.logger.error("json: \n, %s", request.data)
        return Response("", 500)
