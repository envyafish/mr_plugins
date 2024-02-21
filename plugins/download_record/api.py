from flask import Blueprint, request, jsonify, Flask
from plugins.download_record.db import page_record

app = Flask(__name__)

api = Blueprint('download_record', __name__)


@api.route('/page', methods=["GET"])
def page():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    keyword = request.args.get('keyword', None)
    data, total = page_record(page, limit, keyword)
    return jsonify({'code': 0, 'msg': 'success', 'data': data, 'total': total})


app.register_blueprint(api, url_prefix='/api/download_record')

if __name__ == '__main__':
    app.run(debug=True)
