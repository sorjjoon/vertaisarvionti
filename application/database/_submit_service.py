
from sqlalchemy import func
from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, select, update)


from application.domain.assignment import Assignment, Submit, Task, File, Feedback



def select_submits(self, user_ids:list=None, task_ids:list = None, set_feedback=False):
    j = self.submit.outerjoin(self.file)
    if set_feedback:
        j=j.outerjoin(self.feedback)
        sql = select([ self.submit, self.file.c.id, self.file.c.name, self.file.c.upload_date, self.feedback, self.file.c.submit_id]).select_from(j)
    else:
        sql = select([ self.submit, self.file.c.id, self.file.c.name, self.file.c.upload_date, self.file.c.submit_id]).select_from(j)
    self.logger.info("Finding submits with parameters user_id %s (task: %s) ", user_ids, task_ids)
    if user_ids == task_ids == None:
        raise ValueError("all arguments null")

    if user_ids is not None:
        sql = sql.where(self.submit.c.owner_id.in_(user_ids))
    
    if task_ids is not None:
        
        sql = sql.where(self.submit.c.task_id.in_(task_ids))
    sql = sql.order_by(self.file.c.id) 
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        res = {}
        for row in rs:
            student_id = row[self.submit.c.owner_id]
            task_id = row[self.submit.c.task_id]
            if res.get(student_id) is None:
                res[student_id] = {}
            task_dict = res[student_id]
            if task_dict.get(task_id) is None:
                task_dict[task_id] = Submit(id=row[self.submit.c.id],date=row[self.submit.c.last_update],task_id=row[self.submit.c.task_id], files=[])

            if row[self.file.c.submit_id] is not None:
                task_dict[task_id].files.append(File(row[self.file.c.id],row[self.file.c.name], row[self.file.c.upload_date]))

            if not task_dict[task_id].feedback and set_feedback and row[self.feedback.c.id]:
                task_dict[task_id].feedback = Feedback(id=row[self.feedback.c.id], files=[], date=row[self.feedback.c.timestamp], modified=row[self.feedback.c.modified], owner_id=row[self.feedback.c.owner_id], description=row[self.feedback.c.description], visible=row[self.feedback.c.visible], submit_id=row[self.feedback.c.submit_id])
    
    return res

def update_submit(self,user_id:int, task_id:int, assignment_id:int, files:list) -> int:
    """Updates the given students return for the given task
    In case of no returns, creates a new one

    Arguments:
        user_id {int} -- [user_id]
        task_id {int} -- [task_id for the submit]
        assignment_id {int} -- [assignment the task belongs to. TODO delete this]
        files {list} -- [list of files to be insrted (insertion done with update_file)]


    Returns:
        int -- [inserted/updated submit_id]
    """
    sql = select([self.submit.c.id]).where((self.submit.c.task_id == task_id) & (self.submit.c.owner_id==user_id))
    self.logger.info("Updating submit %s for user %s", task_id, user_id)
    with self.engine.connect() as conn:
        row = conn.execute(sql).first()
        if row is None:
            
            sql = self.submit.insert().values(owner_id = user_id, task_id = task_id)
            submit_id = conn.execute(sql).inserted_primary_key[0]
            self.logger.info("No old submit found, inserted new id: %s", submit_id)
        else:
            
            submit_id = row[self.submit.c.id]
            self.logger.info("Found old submit id: %s", submit_id)
            sql = update(self.submit).values(last_update = func.now()).where(self.submit.c.id == submit_id)
            
            conn.execute(sql)
        
        self.update_file(user_id, files, submit_id=submit_id)
    return submit_id


    
