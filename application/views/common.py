#from application import app, db
from flask import render_template, redirect, url_for, request, Response, send_file
from flask import current_app as app, g
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
        courses = db.select_courses_teacher(g.conn, current_user.get_id())
        set_course_counts(courses, db.count_students(g.conn, current_user.get_id()))
        
    else:
        courses = db.select_courses_student(g.conn, current_user.get_id())
    incoming_assignments = db.get_assignments_in_time(g.conn, current_user.get_id(), [c.id for c in courses])
    for a in incoming_assignments:
        a.set_timezones("Europe/Helsinki")
    return render_template("/index.html", courses=courses, incoming_assignments=incoming_assignments )



@app.route("/")
def index():
    
    if current_user.is_authenticated:
        return redirect(url_for("courses"))
    else:
        return redirect(url_for("login_auth"))


    
        
@app.route("/view/<course_id>")
@login_required
def view_course(course_id):
    app.logger.info("user "+str(current_user.get_id())+" accessing index for course "+str(course_id))
    course = db.select_course_details(g.conn, course_id, current_user.get_id())
    db.set_assignments(g.conn, course)
    course.set_timezones("Europe/Helsinki")
    return render_template("/course/index.html", course = course)

    # if current_user.role =="USER":
    #     course = db.select_course_details(course_id, current_user.get_id())
    #     db.set_assignments(course)
    #     course.set_timezones("Europe/Helsinki")
    #     teacher = None
    #     if course is not None:
    #         teacher = db.get_user_by_id(course.teacher_id)

    #     return render_template("/student/course.html", course = course, teacher = teacher)
    # elif request.args.get("s")=="1":
    #     course = db.select_course_details(course_id, current_user.get_id(), is_student=False)
    #     db.set_assignments(course)
    #     course.set_timezones("Europe/Helsinki")
    #     teacher = None
    #     if course is not None:
    #         teacher = db.get_user_by_id(course.teacher_id)
            
    #     return render_template("/student/course.html", course = course, teacher=teacher)
    # else:
    #     course = db.select_course_details(course_id, current_user.get_id(), is_student=False)
    #     db.set_assignments(course)
    #     course.set_timezones("Europe/Helsinki")
    #     teacher = None
    #     if course is not None:
    #         teacher = db.get_user_by_id(course.teacher_id)

    #     return render_template("/teacher/course/course.html", id = course_id, teacher=teacher)