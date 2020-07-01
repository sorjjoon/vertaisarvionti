from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, select, update, func)

from werkzeug.utils import secure_filename
from sqlalchemy import func, cast, String
from application.domain.assignment import Assignment, Task, Submit, Feedback
from collections import namedtuple
import pytz
def get_course_task_stats(self, course_id:int) -> (dict,dict):
    """[Return all task feedback for users]

    Args:
        course_id (int): [course id]

    Returns:
        dict,dict: [user_points, acc_names]. Both dicts are ordered alphabetically by user lastname, then by taskname (assignment.name + task.number)
    """
    

    j = self.course.join(self.course_student, self.course.c.id == self.course_student.c.course_id).join(self.account, self.course_student.c.student_id == self.account.c.id)
    j = j.join(self.assignment).join(self.task, self.task.c.assignment_id == self.assignment.c.id)
    j = j.outerjoin(self.submit, (self.submit.c.task_id == self.task.c.id) & (self.submit.c.owner_id == self.account.c.id)).outerjoin(self.feedback, self.feedback.c.submit_id == self.submit.c.id)
    sql = select([(self.account.c.last_name+", "+self.account.c.first_name).label("account_name"), self.account.c.id, self.assignment.c.deadline, self.task.c.number, self.feedback.c.points, (self.assignment.c.name+" - "+cast(self.task.c.number, String)).label("task_name")])
    sql = sql.where(self.course.c.id == course_id).select_from(j).order_by("account_name", self.assignment.c.deadline, self.task.c.number)
    with self.engine.connect() as conn:
        rs= conn.execute(sql)
        user_points = {}
        acc_names = {}
        task_names = []
        for row in rs:
            
            
            user_id = row[self.account.c.id]
            points = row[self.feedback.c.points]
            task_name = row["task_name"]
            
            #dic retains insertion order
            if not user_points.get(user_id):
                user_points[user_id] = {}
                acc_names[user_id] = row["account_name"]
            
            if task_name not in task_names:
                task_names.append(task_name)   

            user_points[user_id][task_name]=points


    return user_points, acc_names, task_names


            

def get_all_submits(self, assignment_id:int, task_id:int=None, convert_to_timezone = None, join_feedback = False) -> dict:
    """get all submits involved in the given params. If task_ id is not given, gets all assignment tasks

    Arguments:
        
        assignment_id {int} -- [description]

    Keyword Arguments:
        task_id {int} -- [description] (default: {None})

    Returns:
        dict -- [key student_id, value list of submits]
    """

    with self.engine.connect() as conn:
        task_ids = []
        results = {}
        if task_id is not None:
            sql = select([self.task.c.id]).where(self.task.c.assignment_id == assignment_id)
            rs = conn.execute(sql)
            for row in rs:
                task_ids.append(row[self.task.c.id])
            rs.close()
        else:
            task_ids.append(task_id)
        self.logger.info("Fetching all submits for tasks %s", ", ".join(str(x) for x in task_ids))
        if not join_feedback:
            sql = select([self.submit]).where(self.submit.c.task_id.in_(task_ids))
        else:
            j = self.submit.outerjoin(self.feedback)
            sql = select([self.submit, self.feedback]).select_from(j).where(self.submit.c.task_id.in_(task_ids))
        rs = conn.execute(sql)
        self.logger.info("Success, found %s submits",rs.rowcount)
        for row in rs:
            student_id = row[self.submit.c.owner_id]
            submit_id = row[self.submit.c.id]
            submit_desc = row[self.submit.c.description]
            date = row[self.submit.c.last_update]
            task_id = row[self.submit.c.task_id]
            files = self.select_file_details(submit_id = submit_id)
            if not join_feedback:
                feedback = None
            else:
                feed_id = row[self.feedback.c.id]
                feed_timestamp = row[self.feedback.c.timestamp]
                feed_modified =  row[self.feedback.c.modified]
                feed_visible = row[self.feedback.c.visible]
                feed_points = row[self.feedback.c.points]
                feed_submit_id = row[self.feedback.c.submit_id]
                feed_owner_id = row[self.feedback.c.owner_id]
                feed_description = row[self.feedback.c.description]
                feedback = Feedback(id = feed_id, points=feed_points, description=feed_description, modified=feed_modified, date=feed_timestamp, submit_id=feed_submit_id, owner_id=feed_owner_id, visible=feed_visible)

            submit = Submit(id=submit_id, date=date, task_id=task_id, files=files, description=submit_desc, feedback=feedback)
            self.logger.info("Found submit %s for task %s", submit_id, task_id)
            if convert_to_timezone:
                submit.set_timezones(convert_to_timezone)
            if results.get(student_id):
                results[student_id].append(submit)
            else:
                results[student_id] = [submit]

        return results



def get_first_downloads(self, file_ids:list, user_ids:list = None) -> dict:
    """First downloads for the given ids
        Given times are UTC and not naive

    Args:
        file_ids ([list]): [list of file ids]
        user_id (list, optional): [Use Null for all users, otherwise list of ints]. Defaults to None.

    Returns:
        dict: [Dict {user_id: {file_id: min download}}]
    """
    self.logger.info("Geting first downloads times with params file_ids: %s, user_ids %s", file_ids, user_ids)
    sql = select([self.file_log.c.user_id, self.file_log.c.log_id, func.min(self.file_log.c.timestamp).label("time_min")]).where(self.file_log.c.file_id.in_(file_ids))
    sql = sql.where(self.file_log.c.type == "download")
    
    if user_id is not None:
        sql = sql.where(self.file_log.c.user_id.in_(user_ids))
    else:
        sql = sql.group_by(self.file_log.c.user_id, self.file_log.c.log_id)

    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        self.logger.info("Select success!")
        results = {}
        for row in rs:
            user_id = row[self.file_log.c.user_id]
            if not results.get(user_id):
                results[user_id] = {}
            file_id = row[self.file_log.c.file_id]

            results[user_id][file_id] = pytz.UTC.localize(row["time_min"])

    return results
