from flask import render_template, request, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from datetime import datetime
# Account contains only relevant information for the application
import pytz

class Account:
    def __init__(self, id, name, role, first_name, last_name, failed_attempts, locked, timezone="utc"):
        self.id = id
        self.name = name
        self.role = role
        self.first_name=first_name
        self.last_name = last_name
        self.failed_attempts = failed_attempts
        
        if locked is not None:
            self.locked_until=pytz.timezone(timezone).localize(locked)
        else:
            self.locked_until = None

    def get_id(self):
        return self.id

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        if self.locked_until is None:
            return True

        return False

    def set_timezones(self, timezone_str):
        if self.locked_until is not None:
            self.locked_until=self.locked_until.astimezone(pytz.timezone(timezone_str))

    def get_role(self):
        return self.role

    def __str__(self):
        return self.last_name+", "+self.first_name
        
    def __repr__(self):
        return "id: "+str(self.id)+", username: "+self.name+ ", first name: "+self.first_name+", last name: "+self.last_name+", role:  "+self.role

    def __eq__(self, other):
        if isinstance(other, Account):
            if self.id == other.id and self.name==other.name and self.role==other.role and self.first_name==other.first_name and self.last_name==other.last_name and self.failed_attempts==other.failed_attempts and self.locked_until == other.locked_until:
                return True
        return False