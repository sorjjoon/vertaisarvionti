

#from application import app, db
from flask import render_template, redirect, url_for, request, Response, send_file
from flask import current_app as app, session
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError
import io
import datetime
import pytz
from timeit import default_timer as timer
from application.domain.course import Course
from application import db

@app.route("/enlist", methods = ["GET", "POST"])
@login_required
def enlist_course():
    if current_user.role != "USER":
        return redirect(url_for("index"))
    
    if request.method == "GET":
        return render_template("/student/enlist.html")
    try:
        
        db.enlist_student(request.form.get("code"), current_user.get_id())
        
        return redirect(url_for("courses"))
    except ValueError:
        app.logger.info("invalid code")

        
        return render_template("/student/enlist.html", error="Koodillasi ei löytynyt kurssia")
    except IntegrityError:
        app.logger.info("duplicate signup")
        return render_template("/student/enlist.html", error="Olet jo ilmoittautunut tälle kurssille")

