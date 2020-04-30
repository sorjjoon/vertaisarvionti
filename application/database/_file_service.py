
from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, outerjoin, select, update)
from datetime import datetime
from sqlalchemy import func
from werkzeug.utils import secure_filename
from application.domain.assignment import File
from typing import List, Tuple

def check_user_delete_rights(self, user_id:int, file_id:int, is_teacher:bool=False) -> bool:
    """check if user has rights to delete a given file. is teacher argument doesn't do anything, but could be expanded to allow teachers to delete student files

    Arguments:
        user_id {int} -- [user id]
        file_id {int} -- [file id]

    Keyword Arguments:
        is_teacher {bool} -- [description] (default: {False})

    Returns:
        [bool] -- [true if user has rights]
    """
    sql = select([self.file.c.id]).where(self.file_id == file_id)        
    sql = sql.where(self.file.c.owner_id == user_id)
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        row = rs.first()
        if row is None:
            return False
        
        return True

def check_user_view_rights(self, user_id:int, file_id:int, is_teacher=False) -> bool:
    """test if user has the rights to view selected file. Students can onlly access files for which have been revealed to them, teachers can access all belonging to their course

    Arguments:
        user_id {[int]} -- [user id]
        file_id {[int]} -- [file id]

    Keyword Arguments:
        is_teacher {bool} -- [if the given user is a teacher] (default: {False})

    Returns:
        [bool] -- [true if user has view rights]
    """
    sql = select([self.file.c.owner_id,self.file.c.assignment_id, self.file.c.submit_id, self.file.c.task_id, self.file.c.answer_id]).where(self.file.c.id == file_id)
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        row = rs.first()
        if row is None:
            return False

        if row[self.file.c.owner_id] == user_id:
            return True
        assig_id = row[self.file.c.assignment_id]
        submit_id = row[self.file.c.submit_id]
        task_id = row[self.file.c.task_id]
        answer_id = row[self.file.c.answer_id]

        if answer_id is not None:
            if is_teacher: #shouldn't happen (teacher owns the answer to his own course)
                return False
                # j = self.course.join(self.assignment)
                # sql = select([self.course.c.teacher_id]).select_from(j).where(self.assignment.c.id == assig_id)
                # rs = conn.execute(sql)
                # row = rs.first()

                # if row is None:
                #     return False
                
                # return True

            sql = select([self.answer.c.id]).where((self.answer.c.id == answer_id) & (self.answer.c.reveal < func.now()) ) 
            rs = conn.execute(sql)
            row = rs.first()
            if row is None:
                return False

            j = self.course.outerjoin(self.assignment).outerjoin(self.course_student)
            sql = select([self.course_student.c.id]).select_from(j).where(self.course_student.c.id == user_id)
            rs = conn.execute(sql)
            row = rs.first()
            if row is None:
                return False
            return True

        elif submit_id is not None:
            if is_teacher:
                j = self.course.outerjoin(self.assignment)
                sql = select([self.course.c.teacher_id]).select_from(j).where(self.assignment.c.id == assig_id & self.course.c.teacher_id == user_id)
                rs = conn.execute(sql)
                row = rs.first()
                if row is None:
                    return False
                return True
            
            sql = select([self.peer.c.id]).where((self.peer.c.submit_id == submit_id) & (self.peer.c.reviewer_id == user_id) )
            rs = conn.execute(sql)
            row = rs.first()
            if row is None:
                return False
            return True

        else:
            if is_teacher:
                j = self.course.outerjoin(self.assignment)
                sql = select([self.course.c.teacher_id]).select_from(j).where(self.assignment.c.id == assig_id & self.course.c.teacher_id == user_id)
                rs = conn.execute(sql)
                row = rs.first()
                if row is None:
                    return False
                return True
            
            
            j = self.course.outerjoin(self.assignment).outerjoin(self.course_student)
            sql = select([self.assignment.c.id]).select_from(j).where(self.assignment.c.id == assig_id & self.course_student.student_id == user_id)
            rs = conn.execute(sql)
            row = rs.first()
            if row is None:
                return False
            return True
        




def update_file(self, user_id:int,files:list, submit_id:int=None, assignment_id:int=None, task_id:int=None, answer_id:int=None, files_to_delete:list = []) -> None: 
    """deletes all files matching given parameters, then inserts new files with the same parameters. Doesn't delete files user doesn't own, but doesn't check if the user has rights
    to insert files for the activity he is inserting them for. At least one of the given arugments must not be null
    if assignment id is not given, doesn't check that the other ids provided are null (if multiple are checks that all non nulls match), if assignment id is given, checks that other non given fiels are null
    Doesn't check that the given parameters exsist (will fail with integrity error in this case) and that given parameters are possible (submit id belonging to same assignment for example)

    if files_to_delete is provided, doesn't delete all files, only the ones inside the list, 
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
    """
    print("updating file for user: "+str(user_id))
    if submit_id is None and assignment_id is None and task_id is None and answer_id is None:
        
        raise ValueError("all parameters null for file update")

    sql = self.file.delete().where(self.file.c.owner_id == user_id)
    if submit_id is not None or assignment_id is not None:
        print("submit id: "+str(submit_id))
        sql = sql.where(self.file.c.submit_id == submit_id)
    if assignment_id is not None:
        print("assignment id; "+str(assignment_id))
        sql = sql.where(self.file.c.assignment_id == assignment_id)
    if task_id is not None or assignment_id is not None:
        print("task id: "+str(task_id))
        sql = sql.where(self.file.c.task_id == task_id)
    if answer_id is not None or assignment_id is not None:
        print("answer id: "+str(answer_id))
        sql = sql.where(self.file.c.answer_id == answer_id)
    if files_to_delete:
        print("only delete files: "+str(files_to_delete))
        sql = sql.where(self.file.c.id.in_(files_to_delete))

    with self.engine.connect() as conn:
        rs =conn.execute(sql)
        count = rs.rowcount
        print("deletion complete, deleted "+str(count)+" files for user "+str(user_id))
        insert_dics = [{self.file.c.binary_file: file.read(), self.file.c.owner_id: user_id, self.file.c.name: secure_filename(file.filename), self.file.c.answer_id: answer_id ,self.file.c.submit_id: submit_id, self.file.c.assignment_id: assignment_id, self.file.c.task_id: task_id} for file in files]
        sql = self.file.insert().values(insert_dics)
        print("inserted filenames: ")
        for file in files:
            print(file.filename)
            if "." not in file.filename:
                print("no file extension!!!")
        print("-----------------------------")
        conn.execute(sql)    

def select_file_details(self, assignment_id:int=None, task_id:int=None, file_id:int = None, answer_id:int=None, submit_id:int=None) -> List[File]:
    """Select file id, name and upload_date from the database fot the given params. params not given (or None values given ) are ignored, except if assignment id is given

    Keyword Arguments:
        assignment_id {int} -- [assig id] (default: {None})
        task_id {int} -- [task id] (default: {None})
        file_id {int} -- [file id] (default: {None})
        answer_id {int} -- [answer id] (default: {None})

        submit_id {int} -- [answer id] (default: {None})

    Raises:
        ValueError: [in case all given params are null]

    Returns:
        List[File] -- [description]
    """
 

    if assignment_id is None and task_id is None and file_id is None: #without this would return everything in case both None
        raise ValueError("all given params were None")

    sql = select([self.file.c.id, self.file.c.name, self.file.c.upload_date])
    if assignment_id is not None:
        sql = sql.where(self.file.c.assignment_id == assignment_id)

    if task_id is not None or assignment_id is not None:
        sql = sql.where(self.file.c.task_id == task_id)
    
    if file_id is not None:
        sql = sql.where(self.file.c.id == file_id)

    if answer_id is not None or assignment_id is not None:
        sql = sql.where(self.file.c.answer_id == answer_id)

    if submit_id is not None or assignment_id is not None:
        sql = sql.where(self.file.c.submit_id == submit_id)
        
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        results = []
        for row in rs:
            results.append(File(row[self.file.c.id], row[self.file.c.name], row[self.file.c.upload_date]))
        rs.close()
    return results

def delete_file(self, file_id:int, owner_id) ->int:
    """Delete the given file, this is is a simpler version of the update_file function

    Arguments:
        file_id {[int]} -- [file id]
        owner_id {[int]} -- [owner id]

    """
    sql = self.file.delete().where(self.file.c.id == file_id & self.file.c.owner_id == owner_id)
    with self.engine.connect() as conn:
        conn.execute(sql)
        
        

def get_file(self, file_id:int)-> Tuple[bytes, str]:
    """get the binary file for the given id. Doesn't check if user has rights to view the file or not

    Arguments:
        file_id {int} -- [file id]

    Returns:
        bytes, str -- [first value is the bytearray for the file, second the file name for the file]
    """
   
    sql = select([self.file.c.binary_file, self.file.c.name]).where(self.file.c.id == file_id)
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        row = rs.fetchone()
        if row is None:
            rs.close()
            return None, None

        file = row[self.file.c.binary_file]
        name = row[self.file.c.name]
        rs.close()

        
    return file, name