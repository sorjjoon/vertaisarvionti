from flask_wtf import FlaskForm
#from application import db, app
from wtforms import StringField, IntegerField, validators, ValidationError, BooleanField, FormField, FieldList, TextAreaField
from wtforms import MultipleFileField, FileField
from datetime import datetime, timezone
from flask import current_app as app
from wtforms.fields.html5 import DateTimeField
import pytz
import datetime
from flask import render_template, redirect, url_for, request
import os 
from flask_login import login_user, logout_user, login_required, current_user
from application import db
class TaskForm(FlaskForm):
    task_files = MultipleFileField(label="Tehtävän aineistoja") 
    brief = TextAreaField(label = "Tehtävänanto")
    points = IntegerField(label = "Max pisteet", default=12)

class AssignmentForm(FlaskForm):
    deadline = DateTimeField(
        "Deadline (jätä tyhjäksi ilman palautuspäivää)", format="%Y-%m-%dT%H",

        )
    name = StringField(label = "Nimi", validators=[validators.data_required()])
    reveal = DateTimeField(
        "Näkyy opiskelijoille (jätä tyhjäksi, jos haluat, että näkyy heti)", format="%Y-%m-%dT%H",
        default=datetime.datetime.today ## Now it will call it everytime.
    )
        

    files = MultipleFileField(label="Aineistoja (voit myös lisätä tiedostoja yksittäisiin tehtäviin), max 50 Mb")    
    tasks = FieldList(FormField(TaskForm),min_entries=1, label="Tehtävät")
    

    





@app.route("/view/<course_id>/new", methods = ["GET", "POST"])
@login_required
def new_assignment(course_id):
    if current_user.role =="USER":
        print("Student attempted to insert assignment")
        return redirect(url_for("course", course_id=course_id))
    

    if request.method == "GET":
        return render_template("/teacher/assignment/new.html", id = course_id, form = AssignmentForm())
    
    
    print("attempting assignemnt add")
    form = AssignmentForm(request.form)
    if request.form.get("more") is not None:
        form.tasks.append_entry()
        print("returning more tasks")
        return render_template("/teacher/assignment/new.html", id = course_id, form = form)
    if form.reveal.data is not None and form.deadline.data is not None and form.deadline.data < form.reveal.data:
        print("date validations failed")
        return render_template("/teacher/assignment/new.html", id = course_id, form = form, reveal_error = "Deadline ei voi olla ennen kuin tehtävä näkyy opiskelijoille!")
    files = request.files.getlist("files")
    print("Adding assignment")
    for file in files:
        if not check_file(file):  
            print("File max size reached")  
            return render_template("/teacher/assignment/new.html", id = course_id, form = form, reveal_error = "Yhden lataamasi tiedoston koko oli liian suuri (max 100 Mb)")

    deadline = None
    if form.deadline.data is not None:
        deadline = pytz.timezone("Europe/Helsinki").localize(form.deadline.data)
        
        

    reveal = None
    if form.reveal.data is not None:
        reveal = pytz.timezone("Europe/Helsinki").localize(form.reveal.data)
        
    i = 0
    for task in form.tasks.data:
        files = request.files.getlist("tasks-"+str(i)+"-task_files")
        for file in files:
            if not check_file(file):  
                print("File max size reached")    
                return render_template("/teacher/assignment/new.html", id = course_id, form = form, reveal_error = "Yhden lataamasi tiedoston koko oli liian suuri (max 100 Mb)")
        i+=1    
    print("attempting insert")
    assig_id = db.insert_assignment(current_user.get_id(), course_id,form.name.data ,deadline , reveal , files)
    print("insert successfull")
    i =0
    for task in form.tasks.data:
        
        files = request.files.getlist("tasks-"+str(i)+"-task_files")
        
        i+=1
        print("inserting tasks")
        db.insert_task(current_user.get_id(), assig_id, task.get("brief"), task.get("points"), files)
    print("Everthing inserted! Assignment inserted")
    return redirect(url_for("index"))


def check_file(file):    
    file.seek(0, os.SEEK_END)        
    size = file.tell()
    file.seek(0)
    if size > 100 * 1024 * 1024:
        return False

    return True
