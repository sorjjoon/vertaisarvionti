

from flask import render_template, redirect, url_for, request, Response, send_file, abort
from flask import current_app as app, g, g
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError
import io
import datetime
import pytz
import json
from timeit import default_timer as timer
from timeit import default_timer as timer
from application.domain.course import Course
from application.domain.assignment import File
from database import db
from application.domain.utils import get_file_extension



def get_file_download_link(file:File, **kwargs):
    """Valid kwargs are url, target, extension, icon_size, name, id and force_download

        Args:
            time_zone (str): [description]
        """
    if "force_download" not in kwargs:
        kwargs["force_download"]=0
    if "url" not in kwargs:
        kwargs["url"]=url_for("get_file", filename=file.name, id=file.id, force_download=kwargs["force_download"])
    if "target" not in kwargs:
        kwargs["target"]="_blank"
    if "extension" not in kwargs:
        kwargs["extension"]=get_file_extension(file.name)
    if "icon_size" not in kwargs:
        kwargs["target"]="md"
    if "name" not in kwargs:
        kwargs["name"]=file.name
    if "id" not in kwargs:
        kwargs["id"]="file"+str(file.id)

    return """<a id="{id}" href="{url}" target="{target}" class="slightly_smaller_font"><span class="fiv-cla fiv-icon-{extension} fiv-size-{icon_size}"></span>{name}</a>""".format(**kwargs)

@app.context_processor
def utility_processor():

    def get_deadline_string(deadline, now = datetime.datetime.now(pytz.utc), after=" sitten", before=" jäljellä"):
        if deadline is None:
            return "Ei palautuspäivää"
        
        if now is None:
            app.logger.error("get_deadline_string was called with null now parameter")
            return ""
        if not isinstance(deadline, datetime.datetime) or not isinstance(now, datetime.datetime):
            app.logger.error("get_deadline_string was called with without datetime, deadline %s, now: %s", deadline, now)
            return ""
        try:
            deadline_adjusted = deadline.astimezone(pytz.utc)
            if deadline_adjusted > now:
                diff = deadline_adjusted - now
            else:
                diff = now - deadline_adjusted
            hours = diff.seconds // 3600
            
            minutes = (diff.seconds - 3600*hours)//60
            seconds = (diff.seconds -3600*hours - 60*minutes)
            print(diff)
            print(diff.days)
            if diff.days > 1:
                first = str(diff.days)+" päivää ja "

                if hours > 1:
                    second = str(hours) + " tuntia"
                elif minutes > 1:
                    second = str(minutes)+" minuuttia "
                elif seconds > 1:
                    second = str(seconds) +" sekuntia"
            elif hours > 1:
                first = str(hours) + " tuntia ja "
                if minutes > 1:
                    second = str(minutes)+" minuuttia "
                elif seconds > 1:
                    second = str(seconds) +" sekuntia"
            else:
                first = str(minutes)+" minuuttia ja "
                second = str(seconds) +" sekuntia"

            if now > deadline_adjusted:
                if after[0]!=" ":
                    after = " "+after
                return first + second+after

            else:
                if before[0]!= " ":
                    before = " "+before
                return first + second+before
        except Exception as _:
            app.logger.error("Error geting deadline string", exc_info=True)
            return ""

        
    def previous_url(current_url):
        try:
            current_url = current_url[:current_url.rindex("/")]
            done = False
            while not done:
                last = current_url[current_url.rindex("/")+1:]
                if last=="overview":
                    done=True
                    continue
                try:
                    int(last)
                    done=True
                    continue
                except:
                    pass
                if "." in last:
                    return "/"
                current_url = current_url[:current_url.rindex("/")]

            return current_url
        except Exception as _:          
            return "/"

        
            
    return dict(get_file_extension=get_file_extension, previous_url=previous_url, get_deadline_string=get_deadline_string)


@app.before_request
def validate_user_access():
    g.start = timer()
    url = request.path
    if "/auth" in url:
        g.conn = db.engine.connect()
    else:
        g.conn = db.engine.connect()
    
    if not current_user.is_authenticated:
        return None

    if "static" in url:
        return None
    


    user_id = current_user.get_id()
    role = current_user.role
    app.logger.info("User %s attempted access to %s", user_id, url)
    if "/overview" in url:
        if role != "TEACHER":
            app.logger.warning("User %s attempted to access view without privilages", current_user)
            return redirect(url_for("index"))
    parts = url.split("/")
    assignment_id = None
    task_id = None
    course_id = None
    
    try:
        for i in range(len(parts)):
            part = parts[i]
            if part =="view":
                course_id = int(parts[i+1])
            elif part=="assignment":
                assignment_id = int(parts[i+1])
            elif part == "task":
                task_id = int(parts[i+1])
    except:
        app.logger.error("Error validating user access (trying to deterime assignment and task ids)", exc_info=True)
        return None
    if not db.check_access_rights(g.conn, user_id, current_user.role, course_id=course_id, assignment_id=assignment_id, task_id=task_id):    
        app.logger.warning("User %s attempted to access view without privilages", current_user)  
        return redirect(url_for("index"))
        
@app.teardown_request 
def cleanup(f):
    try:
        g.conn.close()
    except Exception as _:
        app.logger.error("Error in closing connection", exc_info = True)
    try:
        if "static" not in request.url:
            end = timer()
            if g.start:
                duration = (end - g.start)*1000
                app.logger.info("Request to %s (%s) took %s ms", request.path, request.method, duration)
            else:
                app.logger.warning("g.start not set for some reason, url: %s", request.path)
    except Exception as _:
        app.logger.error("Error in request teardown", exc_info = True)

@app.route("/update", methods=["PATCH"])
@login_required
def update_element():
    try:
        json_dic = json.loads(request.data)
        
        target = json_dic.get("target")
        if target=="feedback":
            app.logger.info("Updating feedback for user: %s with values: %s",current_user.get_id(), json_dic)
            submit_id = int(json_dic["submit_id"])
            points = int(json_dic["points"])
            visible = json_dic["visible"]
            if visible =="false":
                visible=False
            elif visible == "true":
                visible=True
            else:
                visible = bool(visible)
            db.grade_submit(g.conn, current_user.get_id(), submit_id,points, visible=visible)

            return Response("", 200)
        else:
            return Response("", 400)
    except (KeyError, ValueError) as r:
        app.logger.error(r, exc_info=True)
        return Response("", 400)

@app.route("/get/<string:filename>")
@login_required
def get_file(filename):
    file_id = request.args.get("id")
    if file_id is None:
        app.logger.error("Requested file without id ")
        return app.response_class("id arg missing", 400)

    if not db.check_user_view_rights(g.conn, current_user.get_id(), file_id):
        abort(403)     
    bin_file, name = db.get_file(g.conn, file_id)
    if bin_file is None:
        abort(404)
    buffer = io.BytesIO()
    buffer.write(bin_file)
    buffer.seek(0)
    db.insert_file_log(g.conn, [file_id], current_user.get_id(),"download")
    if str(request.args.get("force_download"))=="1" or ".html" in name or ".css" in name or ".js" in name:
        return send_file(buffer, as_attachment=True, attachment_filename=name)
    else:
        response = send_file(buffer, attachment_filename=name)
        response.headers["Content-Disposition"]='inline; filename="{}"'.format(name)
        return response


