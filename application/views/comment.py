
from flask import render_template, redirect, url_for, request, Response, send_file
from flask import current_app as app, g
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


@app.route("/comment", methods=["POST", "PATCH", "GET"])
@login_required
def new_comment():
    """Valid comment-targets s:submit_id, c:course_id, ts:submit_for_this_task_id 
    

    Returns:
        [Response]: [description]
    """

    try:
        if request.method == "POST" or request.method == "PATCH":
            json_dic = json.loads(request.data)
            comment_target = json_dic.pop("target", None)
    except Exception:
        app.logger.error("Error parsing user json ", exc_info=True)
        app.logger.error("json: \n, %s", request.data)
        return Response("", 400)
    try:
        if request.method == "PATCH":
            try:
                db.update_comment(g.conn, json_dic["comment_id"], current_user.get_id(
                ), json_dic.get("text"), json_dic.get("visible"))
                return Response("", 200)
            except Exception:
                app.logger.error(
                    "Error updating comment based on json", exc_info=True)
                return Response("", 400)

        elif request.method == "POST":
            id = int(comment_target[(comment_target.index(":")+1):])
            if "ts" in comment_target:
                submit = db.get_simple_submit(g.conn, current_user.get_id(),id)
                if submit:
                    json_dic["submit_id"] = int(submit.id)
                else:
                    app.logger.error("Tried to insert comment for invalid submit id %s comment_target: %s", id, comment_target)
                    return Response("", 409)
            elif "s" in comment_target:
                json_dic["submit_id"] = id
            elif "c" in comment_target:
                json_dic["course_id"] = id
            else:
                app.logger.error(
                    "Comment_target %s not found, or invalid format", comment_target)
                return Response("", 400)

            json_dic["user_id"] = current_user.get_id()

            db.insert_comment_dict(g.conn, json_dic)
            return Response("", 200)

        

        elif request.method == "GET":
            comment_target = request.headers.get("X-Comment-Target")
            id = int(comment_target[(comment_target.index(":")+1):])
            if "s" in comment_target:
                if "ts" in comment_target:
                    submit = db.get_simple_submit(g.conn, 
                        current_user.get_id(), id)
                    submit_id = int(submit.id)
                elif "s" in comment_target: #same as else
                    submit_id = id
                comments = db.select_comments(g.conn, 
                current_user.get_id(), submit_id=submit_id)
                
            elif "c" in comment_target:
                comments = db.select_comments(g.conn, current_user.get_id(),course_id=id)
            else:
                app.logger.error(
                    "Comment_target %s not found, or invalid format", comment_target)
                return Response("", 400)
            
            if request.headers.get("Content-Type")=="application/json":
                dict_list = [{"id": c.id, "owner_str":c.owner_str, "date_str":c.date_str, "text":c.text, "is_owner":c.owner_id==current_user.get_id()} for c in comments]
                data = json.dumps(dict_list)
                response = app.response_class(
                    response=data,
                    status=200,
                    mimetype='application/json'
                )
                return response
            elif request.headers.get("Content-Type")=="text/html":
                return render_template("comment/post_list_template.html", comments=comments)
            else:
                app.logger.warning("Content-Type header missing, guessing html!")
                return render_template("comment/post_list_template.html", comments=comments)

    except Exception:
        app.logger.error("Error saving user json for method %s ",request.method, exc_info=True)
        app.logger.error("json: \n, %s", request.data)
        return Response("", 500)