from flask import Blueprint, request, render_template, Flask, redirect

from mbot.core.plugins import plugin
from plugins.xx.base_config import ConfigType, get_base_config
from plugins.xx.db import get_course_db, get_teacher_db, get_config_db
from plugins.xx.exceptions import CloudFlareError
from plugins.xx.notify import Notify
from plugins.xx.utils import *
from plugins.xx.models import Result, Course, Teacher, Config

from mbot.openapi import mbot_api
from plugins.xx.common import get_crawler, download_once, sync_new_course, check_config
from mbot.register.controller_register import login_required
from plugins.xx.logger import Logger

bp = Blueprint('plugin_xx', __name__)
# static_bp = Blueprint('plugin_xx_static', __name__)
plugin.register_blueprint('xx', bp)

course_db = get_course_db()
teacher_db = get_teacher_db()
config_db = get_config_db()

app = Flask(__name__)


@app.after_request
def change_header(response):
    disposition = response.get_wsgi_headers('environ').get(
        'Content-Disposition') or ''
    if disposition.rfind('.js') == len(disposition) - 3:
        response.mimetype = 'application/javascript'
    return response


@bp.route('', methods=["GET"])
def index():
    return redirect('/api/plugins/xx/course')


@bp.route('/<view>', methods=["GET"])
def route_view(view):
    return render_template('xx/index.html')


@bp.route('/sites', methods=["GET"])
@login_required()
def exist_site_list():
    xx_site_list = ['mteam', 'exoticaz', 'nicept', 'pttime']
    site_list = mbot_api.site.list()
    filter_list = []
    for site in site_list:
        if site.site_id in xx_site_list:
            filter_list.append(site.site_id)
    return Result.success(filter_list)


@bp.route('/users', methods=["GET"])
@login_required()
def user():
    mr_user_list = mbot_api.user.list()
    mr_user_dict_list = [{'uid': mr_user.uid, 'nickname': mr_user.nickname} for mr_user in mr_user_list]
    return Result.success(mr_user_dict_list)


@bp.route('/download-client', methods=["GET"])
@login_required()
def download_client():
    download_clients = get_base_config(ConfigType.Download_Client)
    return Result.success(download_clients)


@bp.route('/channel', methods=["GET"])
@login_required()
def channel():
    channels = get_base_config(ConfigType.Notify_Channel)
    return Result.success(channels)


@bp.route('/media-path', methods=["GET"])
@login_required()
def media_path():
    media_paths = get_base_config(ConfigType.Media_Path)
    return Result.success(media_paths)


@bp.route('/config/get', methods=["GET"])
@login_required()
def get_config():
    config = config_db.get_config()
    if config:
        return Result.success(obj_trans_dict(config))
    else:
        return Result.success(None)


@bp.route('/config/set', methods=["POST"])
@login_required()
def set_config():
    data = request.json
    config = Config(data)
    config_db.update_config(config)
    return Result.success(None)


@bp.route('/course/list', methods=["GET"])
@login_required()
def list_course():
    page = request.args.get('page')
    keyword = request.args.get('keyword')
    status = request.args.get('status')
    if status:
        status = int(status)
    courses = course_db.filter_course(int(page), keyword, status)
    count = course_db.count_total(keyword, status)
    if not count:
        count = 0
    total_page = int(count / course_db.limit)
    if count % course_db.limit > 0:
        total_page = total_page + 1
    dict_arr = [obj_trans_dict(course) for course in courses]
    result = {
        'total': total_page,
        'data': dict_arr
    }
    return Result.success(result)


@bp.route('/teacher/list', methods=["GET"])
@login_required()
def list_teacher():
    keyword = request.args.get('keyword')
    teachers = teacher_db.filter_teacher(keyword)
    dict_arr = []
    for teacher in teachers:
        teacher_dict = obj_trans_dict(teacher)
        teacher_dict['status'] = 1
        dict_arr.append(teacher_dict)
    return Result.success(dict_arr)


@bp.route('/course/delete', methods=["GET"])
@login_required()
def delete_course():
    course_id = request.args.get('id')
    course_db.delete_course(int(course_id))
    return Result.success(None)


@bp.route('/teacher/delete', methods=["GET"])
@login_required()
def delete_teacher():
    teacher_id = request.args.get('id')
    teacher_db.delete_teacher(int(teacher_id))
    return Result.success(None)


@bp.route('/course/add', methods=["POST"])
@login_required()
def add_course():
    if not check_config():
        return Result.fail("检查配置没有通过")
    data = request.json
    course = Course(data)
    config = config_db.get_config()
    notify = Notify(config)
    course.status = 1
    course.sub_type = 1
    row = course_db.get_course_by_code(course.code)
    if row:
        if row.status == 0:
            row.status = 1
            row.sub_type = 1
            course_db.update_course(row)
            notify.push_subscribe_course(course)
            download_once(row)
            return Result.success(None)
        else:
            return Result.fail("已订阅的课程")
    course = course_db.add_course(course)
    notify.push_subscribe_course(course)
    download_once(course)
    return Result.success(None)


@bp.route('/course/download', methods=["GET"])
@login_required()
def manual_download():
    course_id = request.args.get('id')
    course = course_db.get_course_by_primary(int(course_id))
    if course and course.status == 1:
        download_once(course=course)
        return Result.success(None)
    else:
        return Result.fail("未订阅的课程,无法提交下载")


@bp.route('/teacher/add', methods=["POST"])
@login_required()
def add_teacher():
    data = request.json
    teacher = Teacher(data)
    if not teacher.limit_date:
        return Result.fail("请输入限制时间")
    config = config_db.get_config()
    notify = Notify(config)
    row = teacher_db.get_teacher_by_code(teacher.code)
    if row:
        row.limit_date = teacher.limit_date
        teacher_db.update_teacher(row)
        sync_new_course(row)
        return Result.success(None)
    teacher = teacher_db.add_teacher(teacher)
    notify.push_subscribe_teacher(teacher)
    sync_new_course(teacher)
    return Result.success(None)


@bp.route('/rank/list', methods=["GET"])
@login_required()
def list_rank():
    library, bus = get_crawler()
    try:
        page = request.args.get('page')
        top20_codes = library.crawling_top20(page)
        top20_course = []
        for code in top20_codes:
            course = course_db.get_course_by_code(code)
            if course:
                top20_course.append(obj_trans_dict(course))
            else:
                course = bus.search_code(code)
                if course:
                    course.status = 0
                    course.sub_type = 0
                    course_db.add_course(course)
                    top20_course.append(obj_trans_dict(course))
        return Result.success(top20_course)
    except CloudFlareError:
        return Result.fail("请求遭遇CloudFlare")


@bp.route('/complex/search', methods=["GET"])
@login_required()
def search():
    keyword = request.args.get('keyword')
    result_list = []
    if not keyword:
        return Result.fail("请输入关键字")
    library, bus = get_crawler()
    if len(keyword) == len(keyword.encode()) and has_number(keyword):
        true_code = get_true_code(keyword)
        row = course_db.get_course_by_code(true_code)
        if row:
            course_dict = obj_trans_dict(row)
            course_dict['type'] = 'course'
            result_list.append(course_dict)
        else:
            course = bus.search_code(true_code)
            if course:
                course_dict = obj_trans_dict(course)
                course_dict['status'] = 0
                course_dict['type'] = 'course'
                result_list.append(course_dict)

        teacher_code_list = bus.get_teachers(true_code)
        set_teacher(teacher_code_list, result_list)
    else:
        teacher_code_list = bus.search_all_by_name(keyword)
        if len(teacher_code_list) > 6:
            front_list = [
                teacher_code_list[0],
                teacher_code_list[1],
                teacher_code_list[2],
                teacher_code_list[3],
                teacher_code_list[4],
                teacher_code_list[5]
            ]
            set_teacher(front_list, result_list)
        else:
            set_teacher(teacher_code_list, result_list)
    return Result.success(result_list)


def set_teacher(teacher_code_list: [], result_list: []):
    library, bus = get_crawler()
    if teacher_code_list:
        for teacher_code in teacher_code_list:
            row = teacher_db.get_teacher_by_code(teacher_code)
            if row:
                teacher_dict = obj_trans_dict(row)
                teacher_dict['status'] = 1
                teacher_dict['type'] = 'teacher'
                result_list.append(teacher_dict)
            else:
                teacher = bus.crawling_teacher(teacher_code)
                if teacher:
                    teacher_dict = obj_trans_dict(teacher)
                    teacher_dict['status'] = 0
                    teacher_dict['type'] = 'teacher'
                    result_list.append(teacher_dict)

# if __name__ == '__main__':
#     app.register_blueprint(bp, url_prefix='/api/plugins/xx')
#     app.register_blueprint(static_bp, url_prefix='/static')
#     app.run()
