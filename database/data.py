from datetime import date as pydate
from random import choice
import os
import sys
from sqlalchemy import (Boolean, Column, Date, DateTime, ForeignKey, Index,
                        Integer, LargeBinary, MetaData, String, Table,
                        UniqueConstraint, engine, Text)
from sqlalchemy.engine import Engine
from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, select, update)
from sqlalchemy.sql import func
from sqlalchemy import CheckConstraint, text
import logging
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import expression
from sqlalchemy.ext.compiler import compiles

class utcnow(expression.FunctionElement):
    type = DateTime()

@compiles(utcnow, 'postgresql')
def pg_utcnow(element, compiler, **kw):
    return "TIMEZONE('utc', CURRENT_TIMESTAMP)"

@compiles(utcnow, 'sqlite')
def sqlite_utcnow(element, compiler, **kw):
    return "CURRENT_TIMESTAMP"


class Data():
    def __init__(self, used_engine: engine, create=True, log_format=None, drop_first=False):
        """Initiliaze data class. If engine is not provided tables are not set (call set_tables later)

        Arguments:
            used_engine {engine} -- [sqlalchemy engine]

        Keyword Arguments:
            create {bool} -- [If given will also insure tables exists, as well as attempt  to insert user roles] (default: {True})
        """

        if not log_format:
            log_format = logging.Formatter(
                "[%(asctime)s] %(levelname)s in %(funcName)-20s - %(thread)d: %(message)s")

        logger = logging.getLogger(__name__)
        logger.handlers.clear()
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(log_format)
        logger.addHandler(handler)
        logger.propagate = False
        self.logger = logger
        self.logger.info("sql logger set up")

        if used_engine is not None:
            self.set_engine(used_engine, create=create, drop_first=drop_first)
        else:
            self.engine = None

    def set_engine(self, used_engine: Engine, create=True, drop_first=False):
        """set object tables

        Arguments:
            used_engine {engine} -- [sqlalchemy engine]

        Keyword Arguments:
            create {bool} -- [If given will also insure tables exists, as well attempt to insert user roles] (default: {True}] (default: {True})
        """
        self.logger.info("defining tables")
        
        if not os.environ.get("DATABASE_URL"):
            # sqlite doesn't enforce foreign keys by default, turning them on to enforce cascade
            def _fk_pragma_on_connect(dbapi_con, con_record):
                dbapi_con.execute('pragma foreign_keys=ON')

            from sqlalchemy import event
            event.listen(used_engine, 'connect', _fk_pragma_on_connect)
        
        metadata = MetaData(bind=used_engine)
        self.role = Table("role", metadata,
                          Column("id", Integer, primary_key=True),
                          Column("name", String(20), nullable=False),
                          UniqueConstraint('name', name='role_unique'
                                           ))
        self.account = Table('account', metadata,
                             Column("id", Integer, primary_key=True),
                             Column("role_id", Integer,  ForeignKey(
                                 self.role.c.id, ondelete="CASCADE"), nullable=False),
                             Column("creation_date", DateTime, nullable=False,
                                    server_default=utcnow()),
                             Column("username", String(144),
                                    nullable=False, unique=True),
                             Column("salt", String(144), nullable=False),
                             Column("password", String(144), nullable=False),
                             Column("first_name", String(144), nullable=False),
                             Column("last_name", String(144), nullable=False),
                             Column("locked_until", DateTime),
                             Column("failed_attempts", Integer, server_default=text("0"), nullable=False)
                             )

        

        self.course = Table("course", metadata,
                            Column("id", Integer, primary_key=True),
                            Column("abbreviation", String(
                                8), nullable=False),
                            Column("teacher_id", Integer, ForeignKey(
                                self.account.c.id, ondelete="CASCADE"), index=True, nullable=False),
                            Column("name", String(50), nullable=False),
                            Column("description", String(500)),
                            Column("code", String(8), nullable=False, unique=True),

                            Column("creation_date", DateTime, nullable=False,
                                   server_default=utcnow())
                            )
        self.course_student = Table("course_student", metadata,
                                    Column("student_id", Integer, ForeignKey(
                                        self.account.c.id, ondelete="CASCADE"), nullable=False, primary_key=True),
                                    Column("course_id", Integer, ForeignKey(
                                        self.course.c.id, ondelete="CASCADE"), nullable=False, primary_key=True),
                                    Column(
                                        "timestamp", DateTime, nullable=False, server_default=utcnow())
                                    )

        self.assignment = Table("assignment", metadata,
                                Column("id", Integer, primary_key=True),
                                Column("name", String(144), nullable=False),
                                Column("description", String(500) ),
                                Column("course_id", Integer, ForeignKey(
                                    self.course.c.id, ondelete="CASCADE"), nullable=False),
                                Column("reveal", DateTime,
                                       server_default=utcnow(), nullable=False),
                                Column("deadline", DateTime)
                                )

        self.task = Table("task", metadata,
                          Column("id", Integer, primary_key=True),
                          Column("number", Integer, nullable=False),
                          Column("points", Integer, nullable=False),
                          Column("description", String(500)),
                          Column("assignment_id", Integer, ForeignKey(
                              self.assignment.c.id, ondelete="CASCADE"), nullable=False)
                          )
        self.answer = Table("answer", metadata,
                            Column("id", Integer, primary_key=True),
                            Column("reveal", DateTime,
                                   server_default=utcnow(), nullable=False),
                            Column("description", String(500)),
                            Column("task_id", Integer, ForeignKey(
                                self.task.c.id, ondelete="CASCADE"), unique=True, nullable=False),
                            Column("reveal", DateTime, nullable=False))
                            
        self.submit = Table("submit", metadata,
                            Column("id", Integer, primary_key=True),
                            Column("description", String(500)),
                            Column("task_id", Integer, ForeignKey(
                                self.task.c.id, ondelete="CASCADE"), index=True, nullable=False),

                            Column("last_update", DateTime, nullable=False,
                                   server_default=utcnow()),

                            Column("owner_id", Integer, ForeignKey(self.account.c.id, ondelete="CASCADE"), index=True, nullable=False))

        self.feedback = Table("feedback", metadata,
                              Column("id", Integer, primary_key=True),
                              Column("points", Integer, nullable=False),
                              Column("timestamp", DateTime, nullable=False,
                                     server_default=utcnow()),
                              Column("modified", DateTime),
                              Column("description", String(500)),
                              Column("owner_id", Integer, ForeignKey(
                                  self.account.c.id), nullable=False),
                              Column("reveal", DateTime, nullable=False),
                              Column("submit_id", Integer, ForeignKey(self.submit.c.id, ondelete="CASCADE"), index=True, nullable=False))

        self.comment = Table("comment", metadata,

                             Column("id", Integer, primary_key=True),
                             Column("text", Text),
                             Column("modified", DateTime),
                             Column("user_id", Integer, ForeignKey(
                                 self.account.c.id), nullable=False),
                             Column("reveal", DateTime, nullable=False,
                                    server_default=utcnow()),
                             Column("timestamp", DateTime, nullable=False,
                                    server_default=utcnow()),
                             Column("submit_id", Integer, ForeignKey(
                                 self.submit.c.id, ondelete="CASCADE")),
                                 Column("course_id", Integer, ForeignKey(
                                 self.course.c.id, ondelete="CASCADE")),
                             Column("answer_id", Integer, ForeignKey(
                                 self.answer.c.id, ondelete="CASCADE")),
                             Column("task_id", Integer, ForeignKey(
                                 self.task.c.id, ondelete="CASCADE")),
                            
                             Column("assignment_id", Integer, ForeignKey(
                                 self.assignment.c.id, ondelete="CASCADE")),
                             Column("feedback_id", Integer, ForeignKey(
                                 self.feedback.c.id, ondelete="CASCADE")),
                             CheckConstraint(text("""
        (CASE WHEN answer_id IS NULL THEN 0 ELSE 1 END + 
        CASE WHEN submit_id IS NULL THEN 0 ELSE 1 END + 
        CASE WHEN task_id IS NULL THEN 0 ELSE 1 END + 
        CASE WHEN course_id IS NULL THEN 0 ELSE 1 END +
        CASE WHEN feedback_id IS NULL THEN 0 ELSE 1 END +
        CASE WHEN assignment_id IS NULL THEN 0 ELSE 1 END) 
        = 1"""), name='null_comment_foreign_keys'),
        CheckConstraint(text("id > 0"), name="comment_id_must_be_positive")
                             )
                             
        self.file = Table("file", metadata,
                          Column("id", Integer, primary_key=True),
                          Column("name", String(), nullable=False),
                          Column("owner_id", Integer,  ForeignKey(
                              self.account.c.id, ondelete="CASCADE"), nullable=False),
                          Column("upload_date", DateTime, nullable=False,
                                 server_default=utcnow()),
                          Column("binary_file", LargeBinary()),
                          Column("submit_id", Integer, ForeignKey(
                              self.submit.c.id, ondelete="CASCADE")),
                          Column("answer_id", Integer, ForeignKey(
                              self.answer.c.id, ondelete="CASCADE")),
                          Column("task_id", Integer, ForeignKey(
                              self.task.c.id, ondelete="CASCADE")),
                          Column("feedback_id", Integer, ForeignKey(
                              self.feedback.c.id, ondelete="CASCADE")),
                          Column("assignment_id", Integer, ForeignKey(
                              self.assignment.c.id, ondelete="CASCADE")),
                          Column("comment_id", Integer, ForeignKey(
                              self.comment.c.id, ondelete="CASCADE")),
                          CheckConstraint(text("""
        (CASE WHEN answer_id IS NULL THEN 0 ELSE 1 END + 
        CASE WHEN submit_id IS NULL THEN 0 ELSE 1 END + 
        CASE WHEN task_id IS NULL THEN 0 ELSE 1 END + 
        CASE WHEN feedback_id IS NULL THEN 0 ELSE 1 END +
        CASE WHEN comment_id IS NULL THEN 0 ELSE 1 END +
        CASE WHEN assignment_id IS NULL THEN 0 ELSE 1 END) 
        = 1"""), name='null_file_foreign_keys')
                          )

        
        
        

        self.peer = Table("peer", metadata,
                          Column("submit_id", Integer, ForeignKey(
                              self.submit.c.id, ondelete="CASCADE"), index=True, nullable=False),

                          Column("reciever_id", Integer, ForeignKey(
                              self.account.c.id, ondelete="CASCADE"), index=True, nullable=False),
                          Column("reviewer_id", Integer, ForeignKey(self.account.c.id,
                                                                    ondelete="CASCADE"), index=True, nullable=False),
                          Column("review", String(500), nullable=False),
                          Column("deadline", DateTime, nullable=False),
                          Column("teacher_check", Boolean, default=False)
                          )


        self.file_log = Table("file_log", metadata,
                              Column("type", String(50), nullable=False),
                              Column("file_id", Integer,
                                     index=True, nullable=False),
                              Column("user_id", Integer, ForeignKey(
                                  self.account.c.id), nullable=False),
                              Column("timestamp", DateTime, nullable=False,
                                     server_default=utcnow())
                              )

        self.engine = used_engine
        
          
            
# checks if table exsists first
        
        
        with self.engine.connect() as conn:
            if create:
                trans = conn.begin()
                self.logger.info("attempting create all")
                if drop_first:
                    self.logger.info("Dropping first")
                    metadata.drop_all()
                    trans.commit()
                    trans = conn.begin()
                try:
                    metadata.create_all(bind=conn)
                    trans.commit()
                except Exception as r:
                    
                    self.logger.error("Create all failed", exc_info=True)
                    trans.rollback()
                    raise r
                    
                self.logger.info("Create all success!")

            else:
                self.logger.info("Not creating tables")
           
            with conn.begin():
                from sqlalchemy.dialects.postgresql import insert
                self.logger.info("Inserting Account roles")
                # insert user roles (if they don't exsist)"
                dics=[dict(name="USER"), dict(name="TEACHER"), dict(name="ADMIN")]
                sql = insert(self.role).values(dics).returning(self.role.c.name).on_conflict_do_nothing(constraint="role_unique")
                rs = conn.execute(sql)
                rows = rs.fetchall()
            
            names = [i[0] for i in rows]
            self.logger.info("%s roles inserted", names)
                
                
                

    
   

    from ._user_service import delete_user, get_user_by_id, check_user, update_user
    from ._user_auth import get_user, hash_password, insert_user, update_password, get_role_id
    from ._course_service import insert_course, select_courses_teacher, select_courses_student, enlist_student, select_students, select_course_details, set_assignments, update_course
    from ._assignment_service import insert_assignment, _insert_task, select_assignment, set_submits, get_assignments_in_time
    from ._file_service import select_file_details, get_file, update_file, insert_file_log, insert_files, check_user_view_rights, check_user_delete_rights
    from ._submit_service import update_submit, select_submits, get_simple_submit
    from ._teacher_stats import count_students
    from ._task_service import set_task_answer, update_answer
    from ._overview_service import get_all_submits, get_course_task_stats, get_first_downloads
    from ._view_rights import check_access_rights
    from ._feedback_service import update_feedback, grade_submit, delete_feedback, insert_feedback, select_feedback
    from ._comment_service import insert_comment, select_comments, update_comment, insert_comment_dict, delete_comment
