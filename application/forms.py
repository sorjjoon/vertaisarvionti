from flask import render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm
#from application import db, app
from wtforms import StringField, PasswordField, validators, ValidationError, BooleanField
from flask import current_app as app
import datetime
from flask_login import login_user, logout_user, login_required, current_user
from wtforms.fields.html5 import DateField
from application.auth import account
from application import db
from application.domain.course import Course


class CourseForm(FlaskForm):
    name = StringField("Nimi", validators=[validators.DataRequired("Kurssin nimi ei voi olla tyhjä")])
    description = StringField("Selite")
    end_date = DateField("Loppupäivä", validators=[validators.DataRequired("Kurssin loppupäivä ei voi olla tyhjä")])

    class Meta:
        csrf = False



@app.route("/new", methods=["GET", "POST"])
@login_required
def new_course():
    if current_user.role != "TEACHER":
        print("non-teacher attempted insert")
        return redirect(url_for("index"))

    if request.method == "GET":
        return render_template("/teacher/new_course.html", form = CourseForm())
    
    form = CourseForm(request.form)
    if not form.validate():
        print("validation failed")
        render_template("/teacher/new_course.html", form = form)

    date = form.end_date.data
    if not date:
        date = datetime.date.today()
    print("attempting course insert")
    id = db.insert_course(Course(form.name.data, form.description.data, form.end_date.data, time_zone="Europe/Helsinki"), current_user.get_id())
    print("course "+form.name.data+" added. id, code = "+str(id))
    return redirect(url_for("courses"))

    
    


