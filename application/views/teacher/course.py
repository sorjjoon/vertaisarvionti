from flask import render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm

from wtforms import StringField, PasswordField, validators, ValidationError, BooleanField, TextAreaField
from flask import current_app as app, g
import datetime
from flask_login import login_user, logout_user, login_required, current_user
from wtforms.fields.html5 import DateField

from application import db
from application.domain.course import Course
import json
class CourseForm(FlaskForm):
    name = StringField("Kurssin nimi", validators=[validators.DataRequired(message="Nimi ei voi olla tyhjä"), validators.Length(
        min=1, max=50, message="Kurssin nimi voi olla enintään 50 merkkiä")], id="course_name_input")
    abbreviation = StringField("Kurssin lyhenne", validators=[validators.DataRequired(message="Lyhenne ei voi olla tyhjä"), validators.Length(
        min=2, max=8, message="Kurssin lyhenteen täytyy olla 2-8 merkkiä")], id="course_short")
    description = TextAreaField("Kurssin selite", validators=[validators.Length(
        min=0, max=400, message= "Kurssin selite on enintään 400 merkkiä")])
    
    class Meta:
        csrf = False

@app.route("/new", methods=["GET", "POST"])
@login_required
def new_course():
    if current_user.role != "TEACHER":
        app.logger.info("non-teacher attempted insert")
        return redirect(url_for("index"))

    if request.method == "GET":
        form = CourseForm()
        return render_template("/teacher/new_course.html", form = form)
    app.logger.info("user %s attempting course insert", current_user.get_id())
    form = CourseForm(request.form)
    description = form.description.data.strip()
    course_abbreviation = form.abbreviation.data.strip()
    course_name = form.name.data.strip()
    
    
    if not form.validate():
        app.logger.info("validation failed too long")
        if len(description) > 400:
            app.logger.info("course_description too long")
            description_error = "Kurssin selite on "+str(len(description) - 400)+" merkkiä lian pitkä"
        
            return render_template("/teacher/new_course.html", description_error=description_error, form=form)
        else:
            return render_template("/teacher/new_course.html", form=form)
    app.logger.info("form validation success")


    id = db.insert_course(g.conn, Course(course_name, description, time_zone="Europe/Helsinki", abbreviation = course_abbreviation.upper()), current_user.get_id())
    app.logger.info("new course %s inserted", id)

    return redirect(url_for("courses"))

@app.route("/view/<course_id>/teacher/students")
@login_required
def view_course_students(course_id):
    students = db.select_students(g.conn, course_id, current_user.get_id())
    return render_template("/teacher/course/students.html", students = students)
    
@app.route("/view/<course_id>/teacher/update", methods=["PATCH"])
@login_required
def update_course(course_id):
    if request.method == "PATCH":
        try:
            json_dic = json.loads(request.data)
            
            
        except Exception as r:
            app.logger.error("Failed loading user json %s", request.data, exc_info=True)
            raise r

        db.update_course(g.conn, current_user.get_id(), course_id, json_dic)
        return app.response_class("", 200)