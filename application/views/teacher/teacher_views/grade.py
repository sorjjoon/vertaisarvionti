
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

def find_next_student(id_list:list, current:int):
    
    for i in range(len(id_list)):
        
        if i!=len(id_list)-2 and str(id_list[i]) == str(current) :
            return id_list[i+1]

    return None





@app.route("/view/<course_id>/overview/<assignment_id>/task/<task_id>/grade/<student_id>",  methods=["GET", "POST"])
@login_required
def grade_student(course_id, assignment_id, task_id, student_id):
    print("grading student "+str(student_id))
    student_list = session.get("next_list")
    this_student = db.get_user_by_id(student_id)
    if not student_list:
        submits = db.get_all_submits(assignment_id, task_id=task.id, convert_to_timezone = "Europe/Helsinki")
        all_students = db.select_students(course_id, current_user.get_id())
        student_ids_with_submits = [s.id for s in all_students if submits.get(s.id)]
        student_ids_with_submits.append("id"+str(task_id))
        session["next_list"] = student_ids_with_submits
        student_list = student_ids_with_submits
    
        
    if int(student_list[len(student_list)-1][2:])==int(task_id):
        student_id = find_next_student(student_list, student_id)
        
        if student_id is not None:
            next_url = url_for("grade_student", course_id=course_id, assignment_id=assignment_id, task_id=task_id, student_id=student_id)
        else:
            next_url = url_for("task_overview",course_id=course_id, assignment_id=assignment_id, task_id=task_id)

    assignment = db.select_assignment(assignment_id,task_id=task_id, for_student=False, set_task_files=True)
    db.set_submits(assignment, student_id, task_id=task_id)

    return render_template("/teacher/grade/task.html", next_url = next_url, assignment=assignment, task=assignment.tasks[0], this_student=this_student)
