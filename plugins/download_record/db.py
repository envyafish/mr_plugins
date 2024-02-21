import sqlite3


def page_record(page, limit, keyword):
    # 连接到数据库
    conn = sqlite3.connect('main.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 分页查询download_record表
    offset = (page - 1) * limit
    sql = f"SELECT * FROM download_record order by gmt_create desc LIMIT {limit} OFFSET {offset}"
    if keyword:
        sql = f"SELECT * FROM download_record where movie_name like '%{keyword}%' order by gmt_create desc LIMIT {limit} OFFSET {offset}"
    # 执行查询
    cursor.execute(sql)
    rows = cursor.fetchall()

    # 将结果映射为字典列表
    result = []
    for row in rows:
        result.append(dict(row))
    sql = f"SELECT count(0) as count FROM download_record"
    if keyword:
        sql = f"SELECT count(0) FROM download_record where movie_name like '%{keyword}%'"
    cursor.execute(sql)
    row = cursor.fetchone()
    total = dict(row).get('count', 0)
    # 关闭连接
    conn.close()
    return result, total


def delete_record(id):
    conn = sqlite3.connect('main.db')
    cursor = conn.cursor()
    sql = f"delete from download_record where id = {id}"
    cursor.execute(sql)
    #
    conn.commit()
    conn.close()
