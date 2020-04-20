
#from application import db, app

from datetime import datetime, timezone
from flask import current_app as app
from app import db
import pytz
import datetime
from flask import render_template, redirect, url_for, request
import os 
from flask_login import login_user, logout_user, login_required, current_user



@app.route("/view/<course_id>/overview")
@login_required
def course_overview(course_id):
    if current_user.role == "USER":
        return redirect(url_for("index"))

    course = db.select_course_details(course_id, current_user.get_id(), is_student=False)
    db.set_assignments(course, for_student=False)
