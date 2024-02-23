import threading

from sqlalchemy import create_engine, or_, func, text
from sqlalchemy.orm import sessionmaker, Session

from plugins.xx.exceptions import SqlError
from plugins.xx.logger import Logger
from plugins.xx.utils import *
from plugins.xx.models import Base, Course, Teacher, Config


class DB:
    engine: None

    def __init__(self):
        self.engine = create_engine('sqlite:////data/db/xx.db',
                                    connect_args={'check_same_thread': False, 'isolation_level': None})
        Base.metadata.create_all(self.engine, checkfirst=True)

    def get_session(self):
        return sessionmaker(bind=self.engine)()

    def sync_database(self):
        self.check_and_create_column('config', 'auto_sub', 'int default 0')
        self.check_and_create_column('config', 'emby_folders', 'text')
        self.check_and_create_column('config', 'plex_titles', 'text')
        self.check_and_create_column('config', 'fsm_token', 'varchar(255)')
        self.check_and_create_column('config', 'fsm_passkey', 'varchar(255)')
        self.check_and_create_column('config', 'fsm_salt', 'varchar(255)')

    def check_and_create_column(self, table_name, column_name, column_definition):
        # 连接到 SQLite 数据库
        session = self.get_session()

        sql = "PRAGMA table_info({})".format(table_name)
        # 查询表的 schema
        columns = session.execute(text(sql)).fetchall()

        # 检查列是否存在
        column_exists = any(column[1] == column_name for column in columns)
        if not column_exists:
            session.execute(text("ALTER TABLE {} ADD COLUMN {} {}".format(table_name, column_name, column_definition)))
        session.commit()
        session.flush()


class CourseDB:
    session: Session
    limit: int = 24

    def __init__(self, session: Session):
        self.session = session

    def get_course_by_primary(self, primary: int):
        return self.session.query(Course).filter_by(id=primary).first()

    def get_course_by_code(self, code: str):
        return self.session.query(Course).filter_by(code=code).first()

    def filter_course(self, page, keyword, status):
        offset = (page - 1) * self.limit
        query = self.session.query(Course)
        if keyword:
            keyword = keyword.upper()
            rule = or_(Course.code.like(f"%{keyword}%"), Course.casts.like(f"%{keyword}%"))
            query = query.filter(rule)
        if status:
            query = query.filter(Course.status == status)
        query = query.filter(Course.status > 0)
        return query.order_by(Course.create_time.desc()).offset(offset).limit(self.limit).all()

    def count_total(self, keyword, status):
        query = self.session.query(func.count(Course.id))
        if keyword:
            rule = or_(Course.code.like(f"%{keyword}%"), Course.casts.like(f"%{keyword}%"))
            query = query.filter(rule)
        if status:
            query = query.filter(Course.status == status)
        query = query.filter(Course.status > 0)
        return query.scalar()

    def list_course(self, **qry):
        return self.session.query(Course).filter_by(**qry).all()

    def add_course(self, data: Course):
        course = self.session.query(Course).filter_by(code=data.code).first()
        if course:
            return course
        try:
            data.create_time = get_current_datetime_str()
            self.session.add(data)
            self.session.commit()
            return data
        except Exception as e:
            Logger.error(repr(e))
            self.session.rollback()
            raise SqlError
        finally:
            self.session.flush()

    def update_course(self, data: Course):
        course = self.session.query(Course).filter_by(id=data.id).first()
        if not course:
            return None
        try:
            data.update_time = get_current_datetime_str()
            copy_properties(data, course)
            self.session.commit()
            return course
        except Exception as e:
            Logger.error(repr(e))
            self.session.rollback()
            raise SqlError
        finally:
            self.session.flush()

    def delete_course(self, primary: int):
        course = self.get_course_by_primary(primary)
        if course:
            try:
                self.session.delete(course)
                self.session.commit()
            except Exception as e:
                Logger.error(repr(e))
                self.session.rollback()
                raise SqlError
            finally:
                self.session.flush()


class TeacherDB:
    session: Session

    def __init__(self, session: Session):
        self.session = session

    def get_teacher_by_primary(self, primary: int):
        return self.session.query(Teacher).filter_by(id=primary).first()

    def get_teacher_by_code(self, code: str):
        return self.session.query(Teacher).filter_by(code=code).first()

    def filter_teacher(self, keyword):
        query = self.session.query(Teacher)
        if keyword:
            query = query.filter(Teacher.name.like(f"%{keyword}%"))
        return query.order_by(Teacher.create_time.desc()).all()

    def list_teacher(self, **qry):
        return self.session.query(Teacher).filter_by(**qry).all()

    def add_teacher(self, data: Teacher):
        teacher = self.session.query(Teacher).filter_by(code=data.code).first()
        if teacher:
            return teacher
        try:
            data.create_time = get_current_datetime_str()
            self.session.add(data)
            self.session.commit()
            return data
        except Exception as e:
            Logger.error(repr(e))
            self.session.rollback()
            raise SqlError
        finally:
            self.session.flush()

    def update_teacher(self, data: Teacher):
        teacher = self.session.query(Teacher).filter_by(id=data.id).first()
        if not teacher:
            return None
        try:
            data.update_time = get_current_datetime_str()
            copy_properties(data, teacher)
            self.session.commit()
            return teacher
        except Exception as e:
            Logger.error(repr(e))
            self.session.rollback()
            raise SqlError
        finally:
            self.session.flush()

    def delete_teacher(self, primary: int):
        teacher = self.get_teacher_by_primary(primary)
        if teacher:
            try:
                self.session.delete(teacher)
                self.session.commit()
            except Exception as e:
                Logger.error(repr(e))
                self.session.rollback()
                raise SqlError
            finally:
                self.session.flush()


class ConfigDB:
    session: Session

    def __init__(self, session: Session):
        self.session = session

    def get_config(self):
        return self.session.query(Config).first()

    def update_config(self, data):
        config = self.session.query(Config).first()
        try:
            if config:
                copy_properties(data, config)
                self.session.commit()
                return config
            else:
                self.session.add(data)
                self.session.commit()
        except Exception as e:
            Logger.error(repr(e))
            self.session.rollback()
            raise SqlError
        finally:
            self.session.flush()
