from plugins.xx.orm import DB, CourseDB, TeacherDB, ConfigDB

db = DB()


def get_course_db() -> CourseDB:
    return CourseDB(db.get_session())


def get_teacher_db() -> TeacherDB:
    return TeacherDB(db.get_session())


def get_config_db() -> ConfigDB:
    return ConfigDB(db.get_session())
