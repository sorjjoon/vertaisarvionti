from flask import render_template, request, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField

# Account contains only relevant information for the application


class account:
    def __init__(self, id, name, role, first_name, last_name):
        self.id = id
        self.name = name
        self.role = role
        self.first_name=first_name
        self.last_name = last_name

    def get_id(self):
        return self.id

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

    def __str__(self):
        return str(self.id)+" "+self.name

    def get_role(self):
        return self.role


    def __str__(self):
        return "id: "+str(self.id)+", username: "+self.name+ ", first name: "+self.first_name+", last name: "+self.last_name+", role:  "+self.role