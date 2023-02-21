import datetime
from typing import Dict


def dict_trans_obj(source: Dict, target: object):
    if not source:
        return
    if not target or not target.__annotations__:
        return
    for name in target.__annotations__:
        setattr(target, name, source.get(name))


def obj_trans_dict(source: object):
    if not source or not source.__annotations__:
        return
    data = {}
    for name in source.__annotations__:
        data[name] = getattr(source, name)
    return data


def copy_properties(source: object, target: object) -> None:
    if not source:
        return
    if not target or not target.__annotations__:
        return
    for name in target.__annotations__:
        setattr(target, name, getattr(source, name))


def str_cookies_to_dict(cookies: str):
    dict_cookie = {}
    if not cookies:
        return dict_cookie
    str_cookie_list = cookies.split(';')
    for cookie in str_cookie_list:
        if cookie.strip(' '):
            cookie_key_value = cookie.split('=')
            if len(cookie_key_value) < 2:
                continue
            key = cookie_key_value[0]
            value = cookie_key_value[1]
            dict_cookie[key] = value
    return dict_cookie


def has_number(keyword):
    for s in keyword:
        if s.isdigit():
            return True
    else:
        return False


def get_true_code(input_code: str):
    code_list = input_code.split('-')
    code = ''.join(code_list)
    length = len(code)
    index = length - 1
    num = ''
    all_number = '0123456789'
    while index > -1:
        s = code[index]
        if s not in all_number:
            break
        num = s + num
        index = index - 1
    prefix = code[0:index + 1]
    return (prefix + '-' + num).upper()


def get_current_datetime_str():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def get_datetime_str(dt: datetime.datetime):
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def get_date_str(d: datetime.date):
    return d.strftime('%Y-%m-%d')


def date_str_to_timestamp(date_str):
    try:
        date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        timestamp = date.strftime('%Y%m%d')
        return int(timestamp)
    except Exception as e:
        print(e)
        return None
