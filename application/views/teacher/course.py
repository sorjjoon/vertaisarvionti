from flask import render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm
#from application import db, app
from wtforms import StringField, PasswordField, validators, ValidationError, BooleanField
from flask import current_app as app, g
import datetime
from flask_login import login_user, logout_user, login_required, current_user
from wtforms.fields.html5 import DateField
from application.auth import account
from application import db
from application.domain.course import Course



@app.route("/new", methods=["GET", "POST"])
@login_required
def new_course():
    if current_user.role != "TEACHER":
        app.logger.info("non-teacher attempted insert")
        return redirect(url_for("index"))

    if request.method == "GET":
        return render_template("/teacher/new_course.html")
    
    course_abbreviation = request.form.get("course_short")
    course_name = request.form.get("course_name")
    
    if len(course_abbreviation) > 7:
        app.logger.info("course_abbreviation too long")
        render_template("/teacher/new_course.html", short_error = "Kurssin lyhenne voi olla enintään 7 merkkiä")

    if len(course_name) > 30:
        app.logger.info("course_name too long")
        render_template("/teacher/new_course.html", short_error = "Kurssin nimi voi olla enintään 30 merkkiä")
    
    id = db.insert_course(g.conn, Course(course_name, None, None, time_zone="Europe/Helsinki", abbreviation = course_abbreviation), current_user.get_id())
    app.logger.info("new course %s inserted", id)

    return redirect(url_for("courses"))

@app.route("/view/<course_id>/students")
@login_required
def view_course_students(course_id):
    students = db.select_students(g.conn, course_id, current_user.get_id())
    return render_template("/teacher/course/students.html", students = students)
    
