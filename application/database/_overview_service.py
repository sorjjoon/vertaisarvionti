from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, select, update, func)

from werkzeug.utils import secure_filename
from sqlalchemy import func
from application.domain.assignment import Assignment, Task, Submit

import pytz

def get_all_submits(self, assignment_id:int, task_id:int=None, convert_to_timezone = None) -> dict:
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
        
        sql = select([self.submit]).where(self.submit.c.task_id.in_(task_ids))

        rs = conn.execute(sql)
        self.logger.info("Success, found %s submits",rs.rowcount)
        for row in rs:
            student_id = row[self.submit.c.owner_id]
            submit_id = row[self.submit.c.id]
            submit_desc = row[self.submit.c.description]
            date = row[self.submit.c.last_update]
            task_id = row[self.submit.c.task_id]
            files = self.select_file_details(submit_id = submit_id)
            
            submit = Submit(id=submit_id, date=date, task_id=task_id, files=files, description=submit_desc)
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
