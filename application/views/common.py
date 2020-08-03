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
from database import db
        
def set_course_counts(courses:list, counts:list):
    for c in counts:
        id = c[0]
        for course in courses:
            if course.id == id:
                course.count = c[1]
                break


@app.route("/courses", methods=["GET", "POST"])
@login_required
def courses():
    signup_error = None
    if request.method == "POST":
        try:
            db.enlist_student(g.conn, request.form.get("code"), current_user.get_id())
        except ValueError:
            app.logger.info("invalid code")
            signup_error="Koodillasi ei löytynyt kurssia"
            pass
        except IntegrityError:
            app.logger.info("duplicate signup")
            signup_error="Olet jo ilmoittautunut tälle kurssille"
            pass
    if current_user.role =="TEACHER":
        courses = db.select_courses_teacher(g.conn, current_user.get_id())
        set_course_counts(courses, db.count_students(g.conn, current_user.get_id()))
        
    else:
        courses = db.select_courses_student(g.conn, current_user.get_id())
    incoming_assignments = db.get_assignments_in_time(g.conn, current_user.get_id(), [c.id for c in courses])
    for a in incoming_assignments:
        a.set_timezones("Europe/Helsinki")
    return render_template("/index.html", courses=courses, incoming_assignments=incoming_assignments, signup_error=signup_error)



@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("courses"))
    else:
        return redirect(url_for("auth.login_auth"))


    

