from flask import render_template, redirect, url_for, request, Response, send_file
from flask import current_app as app, session
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError
import io
import datetime
import pytz
from timeit import default_timer as timer
from application.domain.course import Course
from application import db

@app.route("/view/<course_id>/assignment/<assignment_id>/task/<task_id>", methods=["GET", "POST"])
@login_required
def view_task(course_id, assignment_id, task_id):
    if request.method == "GET":
        assignment = db.select_assignment(assignment_id, task_id=task_id)
        
        if assignment.deadline is None:
            deadline_not_passed = True
        else:
            deadline_not_passed = assignment.deadline.astimezone(pytz.utc) > datetime.datetime.now(pytz.utc)
        
        try:
            task = assignment.tasks[0] #all assigs have at least 1 task, so will only happen for manual urls
        except:
            return redirect(url_for("index"))
        
        db.set_submits(assignment,current_user.get_id(), task_id=task.id)
        
        task.files = db.select_file_details(task_id=task.id)
        db.set_task_answer(task, for_student=True)
        assignment.set_timezones("Europe/Helsinki")
        submit = assignment.submits[0]
        points = ""
        if submit:
            feedback = db.select_feedback(current_user.get_id(), submit_id=submit.id)
            if feedback:
                points = feedback.points
        return render_template("/student/assignment/view_task.html" ,course_id=course_id, task = task, assignment=assignment, deadline_not_passed=deadline_not_passed, comment_target="ts:"+str(task_id), points=points)
    else:
        if current_user.role != "USER":
            return redirect(url_for("index"))
        files = request.files.getlist("files")
        db.update_submit(current_user.get_id(),task_id, assignment_id, files)
        return redirect(url_for("view_task", course_id=course_id, assignment_id=assignment_id, task_id=task_id))
