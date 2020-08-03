
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, validators, ValidationError, BooleanField, FormField, FieldList, TextAreaField
from datetime import datetime, timezone
from flask import current_app as app, g, session, Response
from database import db
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




@app.route("/view/<int:course_id>/overview/<int:assignment_id>/task/<int:task_id>/grade/<int:student_id>",  methods=["GET", "POST"])
@login_required
def grade_student(course_id, assignment_id, task_id, student_id):
    app.logger.info("grading student %s, task %s", student_id, task_id)
    assignment = db.select_assignment(g.conn, assignment_id, task_id=task_id)
    
    student_list = session.get("next_list")
    this_student = db.get_user_by_id(g.conn, student_id)
    student_dic = db.select_submits(g.conn, [student_id], [task_id], set_feedback=True).get(int(student_id))
    if student_dic:
        submit = student_dic.get(int(task_id))
    else:
        submit=None
    
    if not student_list:
        submits = db.get_all_submits(g.conn, assignment_id, task_id=task_id, convert_to_timezone = "Europe/Helsinki")
        all_students = db.select_students(g.conn, course_id, current_user.get_id())
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

    
    task = assignment.tasks[0]
    feedback = db.select_feedback(g.conn, current_user.get_id(), submit_id=submit.id)
    return render_template("/teacher/grade/task.html",feedback=feedback, assignment=assignment,task=task, next_url = next_url , submit=submit, this_student=this_student, comment_target="s:"+str(submit.id))
