

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, validators, ValidationError, BooleanField, FormField, FieldList, TextAreaField
from datetime import datetime, timezone
from flask import current_app as app, session
from application import db
import pytz
import datetime
from flask import render_template, redirect, url_for, request
import os 
from flask_login import login_user, logout_user, login_required, current_user
from wtforms import MultipleFileField, FileField
from wtforms.fields.html5 import DateTimeField
#TODO auths

@app.route("/view/<course_id>/overview")
@login_required
def course_overview(course_id):
    if current_user.role == "USER":
        return redirect(url_for("index"))
    course = db.select_course_details(course_id, current_user.get_id(), is_student=False)
    db.set_assignments(course, for_student=False) 
    course.set_timezones("Europe/Helsinki")
    course.divide_assignment()
    for a in course.assignments:
        for t in a.tasks:
            db.set_task_answer(t, for_student=False)
    return render_template("/teacher/overview/course.html", course = course)  


@app.route("/view/<course_id>/overview/<assignment_id>")
@login_required
def assignment_overview(course_id, assignment_id):
    if current_user.role == "USER":
        return redirect(url_for("index"))   
    assign = db.select_assignment(assignment_id)
    for t in assign.tasks:
        db.set_task_answer(t, for_student=False)
    assign.set_timezones("Europe/Helsinki")
    return render_template("/teacher/overview/assignment.html", assignment = assign) 



class AnswerForm(FlaskForm):
    
    description = TextAreaField(label = "Lisätietoja")
    reveal = DateTimeField(
        "Näkyy opiskelijoille", format="%Y-%d-%mT%H",
        default=datetime.datetime.today, validators=[validators.data_required()]
    )
    files = MultipleFileField(label="Aineistot, max 50 Mb")

@app.route("/view/<course_id>/overview/<assignment_id>/task/<task_id>",  methods=["GET", "POST"])
@login_required
def task_overview(course_id, assignment_id, task_id):
    if current_user.role == "USER":
        app.logger.info("student attempted access to task overview. id: "+str(current_user.get_id()))
        return redirect(url_for("index"))  
    form = None
    if request.method == "POST":
        app.logger.info("attempting answer update")
        form = AnswerForm(request.form)
        
        if not request.form.get("reveal_after") and not form.validate():
            app.logger.info("form validation failed")
            pass
        else:
            app.logger.info("updating answer for "+str(task_id))
            reveal = None
            if not request.form.get("reveal_after"):
                app.logger.info("custom date for reveal "+str(task_id))
                reveal = pytz.timezone("Europe/Helsinki").localize(form.reveal.data)

            db.update_answer(current_user.get_id(),   task_id, request.files.getlist("files"), form.description.data, reveal=reveal )
            app.logger.info("update success, redirecting")
            form = None
            return redirect(url_for("task_overview", course_id=course_id, assignment_id=assignment_id, task_id=task_id))
            

    app.logger.info("viewing task overview")
    assignment = db.select_assignment(assignment_id, task_id=task_id)
    if not assignment:
        return redirect(url_for("index"))
    if assignment.deadline is None:
        deadline_not_passed = True
    else:
        deadline_not_passed = assignment.deadline.astimezone(pytz.utc) > datetime.datetime.now(pytz.utc)
    
    try:
        task = assignment.tasks[0] #all assigs have at least 1 task, so will only happen for manual urls
    except:
        return redirect(url_for("index"))
    
    db.set_submits(assignment,current_user.get_id(), task_id=task.id)
    
    task.files = db.select_file_details(task_id=task_id)
    db.set_task_answer(task, for_student=False)
    assignment.set_timezones("Europe/Helsinki")
    
    if form is None:
        form = AnswerForm()
    submits = db.get_all_submits(assignment_id, task_id=task.id, convert_to_timezone = "Europe/Helsinki")
    all_students = db.select_students(course_id, current_user.get_id())
    student_ids_with_submits = [s.id for s in all_students if submits.get(s.id)]
    student_ids_with_submits.append("id"+str(task_id))
    
    session.pop("next_list", None)
    session["next_list"] = student_ids_with_submits
    
    return render_template("/teacher/overview/task.html",course_id=course_id, task = task, assignment=assignment, deadline_not_passed=deadline_not_passed, form = form, students = all_students, submits = submits) 