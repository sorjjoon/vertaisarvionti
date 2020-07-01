from datetime import date as pydate
from random import choice
import os
import sys
from sqlalchemy import (Boolean, Column, Date, DateTime, ForeignKey, Index,
                        Integer, LargeBinary, MetaData, String, Table,
                        UniqueConstraint, engine)
from sqlalchemy.engine import Engine
from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, select, update)
from sqlalchemy.sql import func
from sqlalchemy import CheckConstraint
import logging
class data():
    def __init__(self, used_engine: engine, create= True, log_format=None):
        """Initiliaze data class. If engine is not provided tables are not set (call set_tables later)

        Arguments:
            used_engine {engine} -- [sqlalchemy engine]

        Keyword Arguments:
            create {bool} -- [If given will also insure tables exists, as well attempt to insert user roles] (default: {True})
        """
        
        if not log_format:
            log_format = logging.Formatter("[%(asctime)s] %(levelname)s in %(funcName)-20s - %(thread)d: %(message)s")

        logger = logging.getLogger(__name__)
        logger.handlers.clear()
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(log_format)
        logger.addHandler(handler)
        logger.propagate = False
        self.logger=logger
        self.logger.debug("Logger set up")


        if used_engine is not None:
                    self.set_tables(used_engine, create=create)
        else:
            self.engine=None


    def set_tables(self, used_engine: engine, create= True):
        """set object tables

        Arguments:
            used_engine {engine} -- [sqlalchemy engine]

        Keyword Arguments:
            create {bool} -- [If given will also insure tables exists, as well attempt to insert user roles] (default: {True}] (default: {True})
        """
        self.logger.info("defining tables")
        
        if not os.environ.get("HEROKU"):
            # sqlite doesn't enforce foreign keys by default, turning them on to enforce cascade
            def _fk_pragma_on_connect(dbapi_con, con_record):
                dbapi_con.execute('pragma foreign_keys=ON')

            from sqlalchemy import event
            event.listen(used_engine, 'connect', _fk_pragma_on_connect)

        metadata = MetaData(bind=used_engine)
        self.account = Table('account', metadata,
                             Column("id", Integer, primary_key=True),
                             Column("role_id", Integer,  ForeignKey(
                                 "role.id", ondelete="CASCADE"), nullable=False),
                             Column("creation date", DateTime, nullable=False,
                                    server_default=func.now()),
                             Column("username", String(144), nullable=False),
                             Column("salt", String(144), nullable=False),
                             Column("password", String(144), nullable=False),
                             Column("first_name", String(144), nullable=False),
                             Column("last_name", String(144), nullable=False),
                             UniqueConstraint(
                                 'username', name='username_unique')
                             )
        self.role = Table("role", metadata,
                          Column("id", Integer, primary_key=True),
                          Column("name", String(20), nullable=False),
                          UniqueConstraint('name', name='role_unique'
                                           ))

        self.course = Table("course", metadata,
                            Column("id", Integer, primary_key=True),
                            Column("teacher_id", Integer, ForeignKey(
                                "account.id", ondelete="CASCADE"), index=True, nullable=False),
                            Column("name", String(144), nullable=False),
                            Column("description", String(144)),
                            Column("code", String(8), nullable=False),
                            Column("end_date", Date),
                            Column("creation_date", DateTime, nullable=False,
                                   server_default=func.now())
                            )
        self.course_student = Table("course_student", metadata,
                                    Column("student_id", Integer, ForeignKey(
                                        "account.id", ondelete="CASCADE"),nullable=False, primary_key=True),
                                    Column("course_id", Integer, ForeignKey(
                                        "course.id", ondelete="CASCADE"),nullable=False, primary_key=True)
                                    )

        self.assignment = Table("assignment", metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(500), nullable=False),
        Column("course_id", Integer, ForeignKey(
                                        "course.id", ondelete="CASCADE"), nullable=False),
        Column("reveal", DateTime,
                                   server_default=func.now(), nullable=False),
        Column("deadline", DateTime)
        )

        self.task = Table("task", metadata,
        Column("id", Integer, primary_key=True),
        Column("number", Integer, nullable=False),
        Column("points", Integer, nullable=False),
        Column("description", String(500)),
        Column("assignment_id", Integer, ForeignKey(
                                        "assignment.id", ondelete="CASCADE"), nullable=False)
                                    )

        self.file = Table("file", metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(), nullable=False),
        Column("owner_id", Integer,  ForeignKey("account.id", ondelete="CASCADE"),nullable=False),
        Column("upload_date", DateTime, nullable=False, server_default=func.now()),
        Column("binary_file", LargeBinary()),
        Column("submit_id", Integer, ForeignKey(
                                        "submit.id", ondelete="CASCADE"), index=True),
        Column("answer_id", Integer, ForeignKey(
                                        "answer.id", ondelete="CASCADE"), index=True),
        Column("task_id", Integer, ForeignKey(
                                        "task.id", ondelete="CASCADE"), index=True),
        Column("feedback_id", Integer, ForeignKey(
                                        "feedback.id", ondelete="CASCADE"), index=True),
        Column("assignment_id", Integer, ForeignKey(
                                        "assignment.id", ondelete="CASCADE"), index=True),
        CheckConstraint("""
        (CASE WHEN answer_id IS NULL THEN 0 ELSE 1 END + 
        CASE WHEN submit_id IS NULL THEN 0 ELSE 1 END + 
        CASE WHEN task_id IS NULL THEN 0 ELSE 1 END + 
        CASE WHEN feedback_id IS NULL THEN 0 ELSE 1 END +
        CASE WHEN assignment_id IS NULL THEN 0 ELSE 1 END) 
        = 1""", name='null file foreign keys')
                                        
                                        
                                        )
        

        self.answer = Table("answer", metadata,
        Column("id", Integer, primary_key=True),
        Column("reveal", DateTime,
                                   server_default=func.now(), nullable=False),
        Column("description", String(500)),                           
        Column("task_id", Integer, ForeignKey(
                                        "task.id", ondelete="CASCADE"), unique=True, nullable=False),
        Column("reveal", DateTime, nullable=False))

        self.submit = Table("submit", metadata,
        Column("id", Integer, primary_key=True),
        Column("description", String(500)),
        Column("task_id", Integer, ForeignKey("task.id", ondelete="CASCADE"), index=True,nullable=False),
        
        Column("last_update", DateTime, nullable=False, server_default=func.now()), 
        
        Column("owner_id", Integer, ForeignKey("account.id", ondelete="CASCADE"), index=True,nullable=False))

        self.feedback = Table("feedback", metadata,
        Column("id", Integer, primary_key=True),
        Column("points", Integer, nullable=False),
        Column("timestamp", DateTime, nullable=False, server_default=func.now()),
        Column("modified", DateTime),
        Column("description", String(500)),
        Column("owner_id", Integer, ForeignKey(
                                "account.id"), nullable=False),
        Column("visible", Boolean, nullable=False),
        Column("submit_id", Integer, ForeignKey("submit.id", ondelete="CASCADE"), index=True,nullable=False))
        

        self.comment = Table("comment", metadata,
        
        Column("id", Integer, primary_key=True),
        Column("text", String(500)),
        Column("modified", DateTime),
        Column("user_id", Integer, ForeignKey(
                                "account.id"), nullable=False),
        Column("visible", Boolean, nullable=False),
        Column("timestamp", DateTime, nullable=False, server_default=func.now()),
        Column("submit_id", Integer, ForeignKey(
                                        "submit.id", ondelete="CASCADE"), index=True),
        Column("answer_id", Integer, ForeignKey(
                                        "answer.id", ondelete="CASCADE"), index=True),
        Column("task_id", Integer, ForeignKey(
                                        "task.id", ondelete="CASCADE"), index=True),
        Column("assignment_id", Integer, ForeignKey(
                                        "assignment.id", ondelete="CASCADE"), index=True),
        Column("feedback_id", Integer, ForeignKey(
                                        "feedback.id", ondelete="CASCADE"), index=True),
        CheckConstraint("""
        (CASE WHEN answer_id IS NULL THEN 0 ELSE 1 END + 
        CASE WHEN submit_id IS NULL THEN 0 ELSE 1 END + 
        CASE WHEN task_id IS NULL THEN 0 ELSE 1 END + 
        CASE WHEN feedback_id IS NULL THEN 0 ELSE 1 END +
        CASE WHEN assignment_id IS NULL THEN 0 ELSE 1 END) 
        = 1""", name='null comment foreign keys')
        
        )

        self.peer = Table("peer", metadata,
        Column("submit_id", Integer, ForeignKey("submit.id", ondelete="CASCADE"), index=True,nullable=False),
        
        Column("reciever_id", Integer, ForeignKey("account.id", ondelete="CASCADE"), index=True,nullable=False),
        Column("reviewer_id", Integer, ForeignKey("account.id", ondelete="CASCADE"), index=True,nullable=False),
        Column("review", String(500), nullable=False),
        Column("deadline", DateTime, nullable=False),
        Column("teacher_check", Boolean, default = False)
        
        
        )
        self.file_log= Table("file_log", metadata,
        Column("type", String(50), nullable=False),
        Column("file_id", Integer, ForeignKey(
                                        "file.id", ondelete="CASCADE"),index=True, nullable=False),
        Column("user_id", Integer, ForeignKey(
                                "account.id"), nullable=False),
        Column("timestamp", DateTime, nullable=False, server_default=func.now()),
        

        
        )


        self.engine=used_engine
        if create:
            self.logger.info("attempting create all")
            metadata.create_all()  # checks if table exsists first

        # insert 1 admin user, and roles "USER" and "ADMIN to the database (if they don't exsist)"

            with self.engine.connect() as conn:
                sql=self.role.insert().values(name = "USER", id = 1)

                # catches unqiue contraint fail
                try:

                    conn.execute(sql)
                    self.logger.info("user role inserted")
                except:
                    pass
                sql=self.role.insert().values(name = "ADMIN", id = 2)
                try:
                    conn.execute(sql)
                    self.logger.info("admin role inserted")

                except:
                    pass

                sql=self.role.insert().values(name = "TEACHER", id = 3)
                try:
                    conn.execute(sql)
                    self.logger.info("admin role inserted")

                except:
                    pass


    @staticmethod
    def drop_all(engine, tables=None):
        print("DROPPING TABLES")
        meta = MetaData(bind=engine)
        meta.reflect(only=tables)
        if tables:
            raise NotImplementedError("TODO")
        meta.drop_all()


    from ._user_service import delete_user, get_user_by_id, check_user, update_username
    from ._user_auth import get_user, hash_password, insert_user, update_password, get_role_id
    from ._course_service import insert_course, select_courses_teacher, select_courses_student, enlist_student, select_students, select_course_details, set_assignments
    from ._assignment_service import insert_assignment, insert_task, select_assignment, set_submits
    from ._file_service import select_file_details, get_file, update_file, insert_file_log, insert_files, check_user_view_rights, check_user_delete_rights
    from ._submit_service import update_submit, select_submits
    from ._teacher_stats import count_students
    from ._task_service import set_task_answer, update_answer
    from ._overview_service import get_all_submits, get_course_task_stats, get_first_downloads
    from ._view_rights import check_access_rights
    from ._feedback_service import update_feedback, grade_submit, delete_feedback, insert_feedback, select_feedback
    from ._comment_service import insert_comment,select_comments, update_comment