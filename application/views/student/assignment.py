from flask import render_template, redirect, url_for, request, Response, send_file
from flask import current_app as app, g, session
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError
import io
import datetime
import pytz
from timeit import default_timer as timer
from application.domain.course import Course
from application import db

@app.route("/view/<course_id>/assignment/<assignment_id>")
@login_required
def view_assig(course_id, assignment_id): #TODO rights validations (remember reveal)
    assignment = db.select_assignment(g.conn, assignment_id)
    db.set_submits(g.conn, assignment, current_user.get_id())
    for t in assignment.tasks:
        db.set_task_answer(g.conn, t, for_student=True)
    assignment.set_timezones("Europe/Helsinki")
    return render_template("/student/assignment/view.html", assignment=assignment)

