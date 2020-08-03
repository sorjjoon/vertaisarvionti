from __future__ import annotations
from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, outerjoin, select, update)
from sqlalchemy.engine import Connection
from datetime import datetime
from sqlalchemy import func, or_

from werkzeug.utils import secure_filename
from application.domain.assignment import File
from typing import List, Tuple
import os
from typing import List, TYPE_CHECKING
from .data import utcnow
from .exceptions import LargeFileError

if TYPE_CHECKING:
    from .data import data


def check_user_delete_rights(self:data, conn: Connection,  user_id:int, file_id:int, is_teacher:bool=False) -> bool:
    """check if user has rights to delete a given file. is teacher argument doesn't do anything, but could be expanded to allow teachers to delete student files

    Arguments:
        user_id {int} -- [user id]
        file_id {int} -- [file id]

    Keyword Arguments:
        is_teacher {bool} -- [description] (default: {False})

    Returns:
        [bool] -- [true if user has rights]
    """
    self.logger.info("Checking if user %s has rights to delete file %s", user_id, file_id)
    sql = select([self.file.c.id]).where(self.file_id == file_id)        
    sql = sql.where(self.file.c.owner_id == user_id)
    with conn.begin():
        rs = conn.execute(sql)
        row = rs.first()
        if row is None:
            self.logger.warning("NO RIGHTS")
            return False
        self.logger.info("rights ok")
        return True

def check_user_view_rights(self:data, conn: Connection,  user_id:int, file_id:int, is_teacher=False) -> bool:
    """test if user has the rights to view selected file. Students can onlly access files for which have been revealed to them, teachers can access all belonging to their course

    Arguments:
        user_id {[int]} -- [user id]
        file_id {[int]} -- [file id]

    Keyword Arguments:
        is_teacher {bool} -- [if the given user is a teacher] (default: {False})

    Returns:
        [bool] -- [true if user has view rights]
    """
    self.logger.info("Checking if user %s has rights to view file %s", user_id, file_id)
    sql = select([self.file.c.owner_id,self.file.c.assignment_id, self.file.c.submit_id,self.file.c.comment_id, self.file.c.task_id, self.file.c.answer_id]).where(self.file.c.id == file_id)
    with conn.begin():
        rs = conn.execute(sql)
        row = rs.first()
        if row is None:
            self.logger.warning("NO RIGHTS, invalid file id")
            return False

        if row[self.file.c.owner_id] == user_id:
            self.logger.info("rights ok, user owns file")
            return True
        assig_id = row[self.file.c.assignment_id]
        submit_id = row[self.file.c.submit_id]
        task_id = row[self.file.c.task_id]
        answer_id = row[self.file.c.answer_id]
        comment_id = row[self.file.c.comment_id]

        if answer_id is not None:
            self.logger.info("File belongs to answer %s", answer_id)
            if is_teacher: #shouldn't happen (teacher owns the answer to his own course)
                self.logger.critical("This shouldn't happen (teacher doesn't own answer)")
                return False
                

            sql = select([self.answer.c.id]).where((self.answer.c.id == answer_id) & (self.answer.c.reveal < utcnow()) ) 
            rs = conn.execute(sql)
            row = rs.first()
            if row is None:
                self.logger.warning("NO RIGHTS, answer hasn't been revealed")
                return False

            j = self.course.outerjoin(self.course_student)
            sql = select([self.course_student.c.course_id]).select_from(j).where(self.course_student.c.student_id == user_id)
            rs = conn.execute(sql)
            row = rs.first()
            if row is None:
                self.logger.warning("NO RIGHTS, student hasn't signed up to this course")
                return False
            self.logger.info("rights ok")
            return True

        elif submit_id is not None:
            self.logger.info("File belongs to submit %s", submit_id)
            if is_teacher:
                j = self.submit.join(self.task).join(self.assignment).join(self.course)
                sql = select([self.course.c.teacher_id]).select_from(j).where((self.submit.c.id == submit_id) & (self.course.c.teacher_id == user_id))
                rs = conn.execute(sql)
                row = rs.first()
                if row is None:
                    self.logger.warning("NO RIGHTS, teacher doesn't own this course")
                    return False
                self.logger.info("rights ok")
                return True
            else:
                sql = select([self.peer.c.id]).where((self.peer.c.submit_id == submit_id) & (self.peer.c.reviewer_id == user_id) )
                rs = conn.execute(sql)
                row = rs.first()
                if row is None:
                    self.logger.warning("NO RIGHTS, user is student and this is not his peer review")
                    return False
                self.logger.info("rights ok")
                return True

        
        elif comment_id is not None:
            self.logger.info("File belongs to comment %s", comment_id)
            
            sql = select([self.comment.c.id]).where(or_(self.comment.c.reveal < utcnow(), self.comment.c.user_id==user_id))
            rs = conn.execute(sql)
            row = rs.first()
            if row is None:
                self.logger.warning("NO RIGHTS, user is student and this is not his peer review")
                return False
            self.logger.info("rights ok")
            return True


        elif assig_id or task_id:
            if is_teacher: #shouldn't happen (teacher owns the answer to his own course)
                self.logger.critical("This shouldn't happen (teacher doesn't own task/assignment)")
                return False
            if task_id is not None:
                self.logger.info("File belongs to task %s", task_id)
                j = self.task.join(self.assignment)
                sql = select([self.assignment.c.id]).select_from(j).where(self.task.c.id==task_id)
                rs = conn.execute(sql)
                row = rs.first()
                if row is None:
                    self.logger.critical("This shouldn't happen, wrong task id in file")
                    return False

                assig_id= row[self.assignment.c.id]

            else:
                self.logger.info("File belongs to assignment %s", assig_id)
            
            
            
            j = self.course.outerjoin(self.assignment).outerjoin(self.course_student)
            sql = select([self.assignment.c.id]).select_from(j).where((self.assignment.c.id == assig_id) & (self.course_student.c.student_id == user_id) & (self.assignment.c.reveal < utcnow()))
            rs = conn.execute(sql)
            row = rs.first()
            if row is None:
                self.logger.warning("NO RIGHTS, user hasn't signed up to this course or the assignment hasn't been revealed")
                return False
            self.logger.info("rights ok")
            return True
        else:
            self.logger.critical("This shouldn't happen, No foreign keys for file %s", file_id)
            return True
        




def update_file(self:data, conn: Connection,  user_id:int,files:list, submit_id:int=None, assignment_id:int=None, task_id:int=None, answer_id:int=None, comment_id:int=None, files_to_delete:list = None) -> int: 
    """deletes all files matching given parameters, then inserts new files with the same parameters. Doesn't delete files user doesn't own, but doesn't check if the user has rights
    to insert files for the activity he is inserting them for. At least one of the given arugments must not be null
    if assignment id is not given, doesn't check that the other ids provided are null (if multiple are checks that all non nulls match), if assignment id is given, checks that other non given fiels are null
    Doesn't check that the given parameters exsist (will fail with integrity error in this case) and that given parameters are possible (submit id belonging to same assignment for example)

    if files_to_delete is provided, doesn't delete all files, only the ones inside the list, 

    TODO log insertions
    Arguments:
        user_id {int} -- [user id]
        files {list} -- [list of files to be inserted]

    Keyword Arguments:
        submit_id {int} -- [submit id to delete] (default: {None})
        assignment_id {int} -- [assignment id to delete, if this param is given, checks that other non given params are null] (default: {None})
        task_id {int} -- [task id to delete] (default: {None})
        answer_id {int} -- [answer id to delete] (default: {None})
        files_to_delete {list} -- [list of file ids to be deleted, if not provided deletes everything matching parameters given before] (default: {[]})

    Raises:
        ValueError: [in case all given ids are null]
    Returns:
        count {int} -- number of deleted files
    """
    
    
        
    
    sql = self.file.delete().where(self.file.c.owner_id == user_id).returning(self.file.c.id)

    


    if submit_id is not None:
        
        self.logger.info("Updating file for user %s submit id: %s",user_id,submit_id)
        sql = sql.where(self.file.c.submit_id == submit_id)
    elif answer_id is not None:
        self.logger.info("Updating file for user %s answer id: %s",user_id,answer_id)
        sql = sql.where(self.file.c.answer_id == answer_id)
    elif task_id is not None:
        self.logger.info("Updating file for user %s task id: %s",user_id,task_id)
        
        sql = sql.where(self.file.c.task_id == task_id)
    elif comment_id is not None:
        self.logger.info("Updating file for user %s comment_id id: %s",user_id,comment_id)
        sql = sql.where(self.file.c.comment_id == comment_id)
    elif assignment_id is not None:
        self.logger.info("Updating file for user %s assignment id: %s",user_id,assignment_id)
        sql = sql.where(self.file.c.assignment_id == assignment_id)
    else:
        raise ValueError("all parameters null for file update")



    if files_to_delete is not None:
        self.logger.info("only deleting files: "+str(files_to_delete))
        sql = sql.where(self.file.c.id.in_(files_to_delete))
    
    
    with conn.begin():
        
        rs =conn.execute(sql)
        count = rs.rowcount
        
        self.logger.info("deletion complete, deleted "+str(count)+" files for user "+str(user_id))
        rows = rs.fetchall()
        if rows:
            deleted_ids = [r[0] for r in rows]
            self.insert_file_log(conn, deleted_ids, user_id, "delete")

        self.insert_files(conn, user_id, files, submit_id=submit_id, assignment_id=assignment_id, task_id=task_id, answer_id=answer_id, comment_id=comment_id)
        
        return count   


def insert_files(self:data, conn: Connection,  user_id:int,files:list, submit_id:int=None, assignment_id:int=None, task_id:int=None, answer_id:int=None, comment_id:int=None):
    """Insert given files. If you want to delete previous files, use update_file instead. 

    Args:
        user_id (int): [description]
        files (list): [description]
        submit_id (int, optional): [description]. Defaults to None.
        assignment_id (int, optional): [description]. Defaults to None.
        task_id (int, optional): [description]. Defaults to None.
        answer_id (int, optional): [description]. Defaults to None.
        comment_id (int, optional): [description]. Defaults to None.
    """
    with conn.begin():
        self.logger.info("inserting %s files for user %s",len(files) ,str(user_id))
        i=0
        for i in range(len(files)):
            file = files[i]
            file.seek(0, os.SEEK_END)        
            size = file.tell()
            file.seek(0)
            if size>50*1024*1024:
                self.logger.error("Attempted to insert too large a file")
                raise LargeFileError("Given file was too large (filename {0})".format(file.filename), file.filename, max_size="50 MB")

            if not file.filename.strip():
                if size < 2:
                    self.logger.info("Empty file, popping")
                    files.pop(i)
                    continue
                
                self.logger.warning("no filename found, using Untitled")
                file.filename="Untitled"
                
                self.logger.info("inserted file size "+str(size))
                
            
            i+=1
            
        insert_dics = [{self.file.c.binary_file: file.read(), self.file.c.owner_id: user_id, self.file.c.name: secure_filename(file.filename)} for file in files]
       
        if not insert_dics:
            return

        if submit_id is not None:
            self.logger.info("inserting for submit "+str(submit_id))
            for dic in insert_dics:
                dic[self.file.c.submit_id]=submit_id

        elif answer_id is not None:
            self.logger.info("inserting for answer "+str(answer_id))
            for dic in insert_dics:
                dic[self.file.c.answer_id]=answer_id

        elif task_id is not None:
            self.logger.info("inserting for task "+str(task_id))
            for dic in insert_dics:
                dic[self.file.c.task_id]=task_id

        elif assignment_id is not None:
            self.logger.info("inserting for assignment "+str(assignment_id))
            for dic in insert_dics:
                dic[self.file.c.assignment_id]=assignment_id
        elif comment_id is not None:
            self.logger.info("inserting for comment "+str(comment_id))
            for dic in insert_dics:
                dic[self.file.c.comment_id]=comment_id
        else:
            self.logger.error("Null ids for insert")
            raise ValueError("File null id insert")

        
        sql = self.file.insert().values(insert_dics)
        
        file_names=""
        for file in files:
            file_names+=file.filename+", "
        
        self.logger.info("Files to be inserted: %s", file_names)
        self.logger.info("attempting insert")
        rs = conn.execute(sql)
        self.logger.info("insert successful!")

    self.insert_file_log(conn, rs.inserted_primary_key, user_id, "upload")
            
    

def select_file_details(self:data, conn: Connection,  assignment_id:int=None, task_id:int=None, file_id:int = None, answer_id:int=None, submit_id:int=None, comment_id:int=None) -> List[File]:
    """Select file id, name and upload_date from the database fot the given params. params not given (or None values given ) are ignored

    Keyword Arguments:
        assignment_id {int} -- [assig id] (default: {None})
        task_id {int} -- [task id] (default: {None})
        file_id {int} -- [file id] (default: {None})
        answer_id {int} -- [answer id] (default: {None})

        submit_id {int} -- [answer id] (default: {None})
        comment_id {int} -- [answer id] (default: {None})

    Raises:
        ValueError: [in case all given params are null]

    Returns:
        List[File] -- [description]
    """

    sql = select([self.file.c.id, self.file.c.name, self.file.c.upload_date]).order_by(self.file.c.id)
    if file_id is not None:
        self.logger.info("Fetching information for file id: %s", file_id)
        sql = sql.where(self.file.c.id == file_id)
    elif submit_id is not None:
        self.logger.info("Fetching files for submit: %s", submit_id)
        sql = sql.where(self.file.c.submit_id == submit_id)
    elif answer_id is not None:
        self.logger.info("Fetching files for answer: %s", answer_id)
        sql = sql.where(self.file.c.answer_id == answer_id)
    elif task_id is not None:
        self.logger.info("Fetching files for task: %s", task_id)
        sql = sql.where(self.file.c.task_id == task_id)
    elif comment_id is not None:
        self.logger.info("Fetching files for comment  %s",comment_id)
        sql = sql.where(self.file.c.comment_id == comment_id)
    elif assignment_id is not None:
        self.logger.info("Fetching files for assignment: %s", assignment_id)
        sql = sql.where(self.file.c.assignment_id == assignment_id)
    
    else:
        #without this would return everything in case all None
        raise ValueError("all given params were None")


    with conn.begin():
        rs = conn.execute(sql)
        
        results = []
        i=0
        for row in rs:
            i+=1
            results.append(File(row[self.file.c.id], row[self.file.c.name], row[self.file.c.upload_date]))
        rs.close()
        self.logger.info("Select success! Found %s files",i)
    return results

def delete_file(self:data, conn: Connection,  file_id:int, owner_id) ->int:
    """Delete the given file, this is is a simpler version of the update_file function

    Arguments:
        file_id {[int]} -- [file id]
        owner_id {[int]} -- [owner id]

    """
    sql = self.file.delete().where(self.file.c.id == file_id & self.file.c.owner_id == owner_id)
    with conn.begin():
        self.logger.info("Deleting file %s for user %s",file_id, owner_id)
        conn.execute(sql)
        self.logger.info("Delete success!")
    self.insert_file_log(conn, [file_id], owner_id)
        
        

def get_file(self:data, conn: Connection,  file_id:int)-> Tuple[bytes, str]:
    """get the binary file for the given id. Doesn't check if user has rights to view the file or not

    Arguments:
        file_id {int} -- [file id]

    Returns:
        bytes, str -- [first value is the bytearray for the file, second the file name for the file]
    """
   
    sql = select([self.file.c.binary_file, self.file.c.name]).where(self.file.c.id == file_id)
    self.logger.info("Fetching binary for file %s", file_id)
    with conn.begin():
        rs = conn.execute(sql)
        row = rs.fetchone()
        if row is None:
            self.logger.warning("Invalid file id!")
            rs.close()
            return None, None

        file = row[self.file.c.binary_file]

        name = row[self.file.c.name]
        self.logger.info("Found file %s",name)
        rs.close()

        
    return file, name


def insert_file_log(self:data, conn: Connection,  file_ids:list, user_id:int, type:str):
    if not file_ids:
        return
    insert_dics = [{self.file_log.c.user_id: user_id, self.file_log.c.type:type, self.file_log.c.file_id: file_id} for file_id in file_ids if file_id is not None]
    if not insert_dics:
        return
    sql = self.file_log.insert().values(insert_dics)
    with conn.begin():
        self.logger.info("Inserting to file log ids: [%s] - (type) %s - (user) %s", ", ".join(str(x) for x in file_ids), type, user_id)
        conn.execute(sql)
        self.logger.info("Insert success!")