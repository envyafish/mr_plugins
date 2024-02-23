import datetime
import json
from typing import List

from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

from plugins.xx.utils import *

Base = declarative_base()


class JsonCustomEncoder(json.JSONEncoder):
    def default(self, value):
        if isinstance(value, datetime.datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(value, datetime.date):
            return value.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, value)


class Result:

    def __init__(self, code, data, msg):
        self.code = code
        self.data = data
        self.msg = msg

    @staticmethod
    def success(content):
        return json.dumps({'code': 200, 'data': content, 'msg': 'success'}, cls=JsonCustomEncoder, ensure_ascii=False)

    @staticmethod
    def fail(message):
        return json.dumps({'code': 204, 'data': None, 'msg': message}, ensure_ascii=False)


class Course(Base):
    __tablename__ = 'course'

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    code: str = Column(String(20), nullable=False)
    title: str = Column(String(255))
    poster: str = Column(String(255))
    banner: str = Column(String(255))
    duration: int = Column(Integer)
    release_date: str = Column(String(12))
    genres: str = Column(String(255))
    casts: str = Column(String(255))
    producer: str = Column(String(255))
    publisher: str = Column(String(255))
    series: str = Column(String(255))
    still_photo: str = Column(Text)
    sub_type: int = Column(Integer, nullable=False)  # 0:未订阅 1:手动订阅 2:教师订阅 3:榜单订阅
    status: int = Column(Integer, nullable=False)  # 0:未订阅 1:订阅中 2：订阅完成
    create_time: str = Column(String(32))
    update_time: str = Column(String(32))

    def __init__(self, data: Dict):
        dict_trans_obj(data, self)


class Teacher(Base):
    __tablename__ = 'teacher'

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    code: str = Column(String(20))
    name: str = Column(String(20), nullable=False)
    photo: str = Column(String(255))
    birth: str = Column(String(12))
    height: str = Column(String(6))
    cup: str = Column(String(6))
    bust: str = Column(String(6))
    waist: str = Column(String(6))
    hip: str = Column(String(6))
    limit_date: str = Column(String(12), nullable=False)
    create_time: str = Column(String(32))
    update_time: str = Column(String(32))

    def __init__(self, data: Dict):
        dict_trans_obj(data, self)


class Config(Base):
    __tablename__ = 'config'

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    proxy: str = Column(String(255))
    user_agent: str = Column(Text)
    library_cookie: str = Column(Text)
    bus_cookie: str = Column(Text)
    download_path: str = Column(String(255))
    category: str = Column(String(255))
    site_id: str = Column(Text)
    only_chinese: int = Column(Integer)
    max_size: int = Column(Integer)
    min_size: int = Column(Integer)
    download_client_name: str = Column(String(55))
    msg_uid: str = Column(String(255))
    msg_channel: str = Column(String(255))
    msg_img: str = Column(String(255))
    auto_sub: int = Column(Integer)
    emby_folders: str = Column(Text)
    plex_titles: str = Column(Text)
    fsm_token: str = Column(String(255))
    fsm_passkey: str = Column(String(255))
    fsm_salt: str = Column(String(255))

    def __init__(self, data: Dict):
        dict_trans_obj(data, self)
