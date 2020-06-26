
from sqlalchemy import func
from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, select, update)


from application.domain.assignment import Assignment, Submit, Task





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


    
