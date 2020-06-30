#from application import app, db
from flask import render_template, redirect, url_for, request, Response, send_file
from flask import current_app as app
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError
import io
import datetime
import pytz
from timeit import default_timer as timer
from application.domain.course import Course
from application import db
        
def set_course_counts(courses:list, counts:list):
    for c in counts:
        id = c[0]
        for course in courses:
            if course.id == id:
                course.count = c[1]
                break


@app.route("/courses")
@login_required
def courses():
    if current_user.role =="TEACHER":
        courses = db.select_courses_teacher(current_user.get_id())
        set_course_counts(courses, db.count_students(current_user.get_id()))
        return render_template("/teacher/teacher_list.html", courses=courses)
    else:
        courses = db.select_courses_student(current_user.get_id())
        return render_template("/student/student_list.html", courses=courses)

@app.route("/new/comment", methods=["POST"])
@login_required
def new_comment():
    text = request.form.get("comment","")
    target_string = request.form.get("target_string")
    if not target_string:
        return redirect(url_for("index"))
    comment_target = target_string[0]
    target_id = int(target_string[1:])
    if comment_target=="s":
        db.insert_comment(current_user.get_id(), text, submit_id=target_id)
    elif comment_target=="t":
        db.insert_comment(current_user.get_id(), text, task_id=target_id)
    elif comment_target =="a":
        db.insert_comment(current_user.get_id(), text, assignment_id=target_id)
    elif comment_target =="n":
        db.insert_comment(current_user.get_id(), text, answer_id=target_id)

    return redirect(request.form.get("origin", url_for("index")))


@app.route("/update/comment")
def update_comment():
    text = request.form.get("comment")
    id = request.form.get("id")
    db.update_comment(id, current_user.get_id(),text=text)

    return redirect(request.form.get("origin", url_for("index")))


@app.route("/")
def index():

    if current_user.is_authenticated:
        return redirect(url_for("courses"))
    else:
        return redirect(url_for("login_auth"))

@app.route("/comment", methods = ["GET", "POST"])
@login_required
def comment():
    if request.method == "GET":
        return redirect(url_for("index"))
    
    text = request.form.get("text")
    next_url = request.form.get("next")
    try:
        c_id = request.form.get("id")
    except:
        return redirect(url_for("index"))
    visible = bool(request.form.get("vis"))
    if request.form.get("u"):
        db.update_comment(c_id, current_user.get_id(),text=text, visible=visible)
    
        
@app.route("/view/<course_id>")
@login_required
def view_course(course_id):
    app.logger.info("user "+str(current_user.get_id())+" accessing index for course "+str(course_id))
    if current_user.role =="USER":
        course = db.select_course_details(course_id, current_user.get_id())
        db.set_assignments(course)
        course.set_timezones("Europe/Helsinki")
        teacher = None
        if course is not None:
            teacher = db.get_user_by_id(course.teacher_id)

        return render_template("/student/course.html", course = course, teacher = teacher)
    elif request.args.get("s")=="1":
        course = db.select_course_details(course_id, current_user.get_id(), is_student=False)
        db.set_assignments(course)
        course.set_timezones("Europe/Helsinki")
        teacher = None
        if course is not None:
            teacher = db.get_user_by_id(course.teacher_id)
            
        return render_template("/student/course.html", course = course, teacher=teacher)
    else:
        course = db.select_course_details(course_id, current_user.get_id(), is_student=False)
        db.set_assignments(course)
        course.set_timezones("Europe/Helsinki")
        teacher = None
        if course is not None:
            teacher = db.get_user_by_id(course.teacher_id)

        return render_template("/teacher/course/course.html", id = course_id, teacher=teacher)