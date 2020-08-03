import datetime
import io
import os
from datetime import datetime, timezone
from timeit import default_timer as timer

import pytz
from flask import Blueprint, Response
from flask import current_app as app
from flask import g, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required, login_user, logout_user
from flask_wtf import FlaskForm
from sqlalchemy.exc import IntegrityError
#from database import db, app
from wtforms import (BooleanField, FieldList, FileField, FormField,
                     IntegerField, MultipleFileField, StringField,
                     TextAreaField, ValidationError, validators)
from wtforms.fields.html5 import DateTimeField

from application.domain.assignment import Assignment, Task
from application.domain.course import Course
from database import db

course_bp = Blueprint(
    "course", __name__, template_folder="templates", static_folder="static", static_url_path="course")

@course_bp.url_value_preprocessor
def get_course_id(endpoint, values):
    g.course_id = values.pop('course_id')
    
    
@course_bp.before_request
def check_id_is_valid():
    course = db.select_course_details(g.conn, g.course_id, current_user.get_id())
    if course is None:
        app.logger.warning("Course id was invalid for request to %s", request.path)
        return redirect(url_for("index"))
    db.set_assignments(g.conn, course,for_student=current_user.get_id()=="USER")
    course.set_timezones("Europe/Helsinki")
    g.course = course


@course_bp.route("/")
@login_required
def view_course():
    app.logger.info("user "+str(current_user.get_id())+" accessing index for course "+str(g.course.id))
    course =g.course
    if request.args.get("overview"):
        return render_template("/course/overview.html", course = course, current="overview")
    else:
        comments = db.select_comments(g.conn, current_user.get_id(), course_id=g.course.id)
        
        return render_template("/course/index.html", course = course, current="index", comments=comments, comment_target="c:"+str(g.course.id))

@course_bp.route('/assignments')
def redirect_assignment():
    return redirect(url_for("course.view_assignments", course_id=g.course.id), 301)

 
@course_bp.route('/assignments/all')
@course_bp.route('/assignments/<int:assignment_id>')
def view_assignments(assignment_id="all"):
    course = g.course
    return render_template("/course/assignments.html", course = course, current="assignments")






class TaskForm(FlaskForm):
    task_files = MultipleFileField(label="Tehtävän aineistoja") 
    brief = TextAreaField(label = "Tehtävänanto")
    points = IntegerField(label = "Max pisteet", default=12)

class AssignmentForm(FlaskForm):
    deadline = DateTimeField(
        "Palautuspäivä", format="%Y-%m-%dT%H",

        )
    name = StringField(label = "Nimi", validators=[validators.data_required()])
    reveal = DateTimeField(
        "Näkyy opiskelijoille", format="%Y-%m-%dT%H", render_kw={"placeholder": "Heti"} ## Now it will call it everytime.
    )
        

    files = MultipleFileField(label="Kaikkien tehtävien aineistot")    
    tasks = FieldList(FormField(TaskForm),min_entries=1, label="Tehtävät")
    
def check_file(file):    
    file.seek(0, os.SEEK_END)        
    size = file.tell()
    file.seek(0)
    if size > 50 * 1024 * 1024:
        return False

    return True


@course_bp.route("/new", methods = ["GET", "POST"])
@login_required
def new_assignment():
    course=g.course
    if current_user.role =="USER":
        app.logger.info("Student attempted to insert assignment")
        return redirect(url_for("course", course_id=course.id))
    if request.method == "GET":
        return render_template("/course/new_assignment.html", course=course, form = AssignmentForm())
    app.logger.info("attempting assignemnt add")
    form = AssignmentForm(request.form)
    if request.form.get("more") is not None:
        form.tasks.append_entry()
        app.logger.info("returning more tasks")
        return render_template("/course/new_assignment.html", course=course, form = form)
    if form.reveal.data is not None and form.deadline.data is not None and form.deadline.data < form.reveal.data:
        app.logger.info("date validations failed")
        return render_template("/course/new_assignment.html", course=course, form = form, reveal_error = "Deadline ei voi olla ennen kuin tehtävä näkyy opiskelijoille!")
    files = request.files.getlist("files")
    app.logger.info("Adding assignment")
    for file in files:
        if not check_file(file):  
            app.logger.info("File max size reached")  
            return render_template("/course/new_assignment.html", course=course, form = form, reveal_error = "Ainakin yhden lataamasi tiedoston koko oli liian suuri (max 50 Mb)")

    deadline = None
    if form.deadline.data is not None:
        deadline = pytz.timezone("Europe/Helsinki").localize(form.deadline.data)
        
    reveal = None
    if form.reveal.data is not None:
        reveal = pytz.timezone("Europe/Helsinki").localize(form.reveal.data)
        
    i = 0
    for task in form.tasks.data:
        task_files = request.files.getlist("tasks-"+str(i)+"-task_files")
        for file in task_files:
            if not check_file(file):  
                app.logger.info("File max size reached")    
                return render_template("/course/new_assignment.html", course=course, form = form, reveal_error = "Ainakin yhden lataamasi tiedoston koko oli liian suuri (max 50 Mb)")
        i+=1
    tasks = []
    i=0
    for task in form.tasks.data:
        
        files = request.files.getlist("tasks-"+str(i)+"-task_files")
        
        
        app.logger.info("inserting tasks")
        tasks.append(Task(None, i+1, task.get("points"), task.get("brief"),files=files))
        
        i+=1
    app.logger.info("attempting insert")
    db.insert_assignment(g.conn, current_user.get_id(), course.id, form.name.data ,deadline , reveal , files, tasks=[])
    app.logger.info("insert successfull")
    
    
    app.logger.info("Everthing inserted! Assignment inserted")
    return redirect(url_for("index"))
