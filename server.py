# server.py
from flask import Flask, request, jsonify, send_file, Response
import io
from datetime import datetime
import mysql.connector
from db import get_connection
import faq_manager  # FAQ 部分保持不变

app = Flask(__name__, static_folder='.', static_url_path='')

@app.route('/')
def index():
    return send_file('index.html')

# ---------------- 城市管理（业务逻辑库）接口 ----------------

@app.route('/api/city/create', methods=['POST'])
def create_city():
    """
    创建一个新的业务逻辑库城市记录（不再创建本地文件夹）。
    前端提交 JSON 格式的数据，包含：city（必填）、type（可选，默认 business）
    """
    data = request.get_json() or {}
    city = data.get('city')
    base_type = data.get('type', 'business')
    if not city:
        return jsonify({"error": "城市名称不能为空"}), 400
    try:
        conn = get_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO cities (name, base_type, created_at) VALUES (%s, %s, %s)"
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(sql, (city.strip(), base_type, created_at))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": f"城市【{city}】创建成功。"})
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

@app.route('/api/city/delete', methods=['DELETE'])
def delete_city():
    """
    删除指定城市，同时删除该城市下所有的文件记录。
    前端提交 JSON 数据，包含 city 字段。
    """
    data = request.get_json() or {}
    city = data.get('city')
    if not city:
        return jsonify({"error": "城市名称不能为空"}), 400
    try:
        conn = get_connection()
        cursor = conn.cursor()
        sql = "DELETE FROM cities WHERE name = %s"
        cursor.execute(sql, (city.strip(),))
        # 同时删除该城市的文件记录
        sql_files = "DELETE FROM files WHERE city = %s"
        cursor.execute(sql_files, (city.strip(),))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": f"城市【{city}】及其文件已删除。"})
    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

# ---------------- 新增：获取城市列表接口 ----------------
@app.route('/getCities')
def get_cities():
    """
    获取已创建的城市列表，从 cities 表中读取城市名称
    """
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        sql = "SELECT name FROM cities"
        cursor.execute(sql)
        cities = [row['name'] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify(cities)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- 文件上传与管理（业务逻辑库）接口 ----------------

@app.route('/uploadFile', methods=['POST'])
def upload_file():
    """
    上传文件接口：前端以 multipart/form-data 格式提交数据，
    包括 city（业务逻辑库所属城市）、type（默认 business）和上传文件（字段名 file）。
    文件内容直接存储在数据库的 files 表中。
    """
    try:
        city = request.form.get('city')
        base_type = request.form.get('type', 'business')
        if not city or 'file' not in request.files:
            return jsonify({"error": "缺少必要参数"}), 400
        file = request.files['file']
        file_name = file.filename
        mime_type = file.mimetype
        file_data = file.read()
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
        INSERT INTO files (city, base_type, file_name, mime_type, file_data, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(sql, (city.strip(), base_type, file_name, mime_type, file_data, created_at))
        conn.commit()
        file_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({"message": "文件上传成功", "file_id": file_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/searchFiles', methods=['GET'])
def search_files():
    """
    文件查询接口：支持根据城市、类型和文件名关键词查询上传的文件记录。
    前端提交 query（关键词）、type（默认 business）和 city（可选）。
    """
    try:
        query = request.args.get('query', '')
        base_type = request.args.get('type', 'business')
        city = request.args.get('city', '')
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        sql = "SELECT * FROM files WHERE base_type = %s"
        params = [base_type]
        if city:
            sql += " AND city = %s"
            params.append(city)
        if query:
            sql += " AND file_name LIKE %s"
            params.append('%' + query + '%')
        cursor.execute(sql, tuple(params))
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/preview', methods=['GET'])
def preview_file():
    """
    文件预览接口：根据前端传入的 file_id 参数，从数据库中读取文件数据，
    返回文件内容供浏览器直接预览。
    """
    try:
        file_id = request.args.get('file_id')
        if not file_id:
            return jsonify({"error": "缺少文件ID参数"}), 400
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        sql = "SELECT file_name, mime_type, file_data FROM files WHERE id = %s"
        cursor.execute(sql, (file_id,))
        file_record = cursor.fetchone()
        cursor.close()
        conn.close()
        if not file_record:
            return jsonify({"error": "文件不存在"}), 404
        return Response(file_record['file_data'],
                        mimetype=file_record['mime_type'],
                        headers={"Content-Disposition": f"inline; filename={file_record['file_name']}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/moveFile', methods=['POST'])
def move_file():
    """
    文件移动接口：此处主要实现将文件的所属城市更改，
    前端提交 JSON 数据，包含 file_id 和 targetCity 参数。
    """
    try:
        data = request.get_json()
        file_id = data.get('file_id')
        target_city = data.get('targetCity')
        if not file_id or not target_city:
            return jsonify({"error": "缺少必要参数"}), 400
        conn = get_connection()
        cursor = conn.cursor()
        sql = "UPDATE files SET city = %s WHERE id = %s"
        cursor.execute(sql, (target_city.strip(), file_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "文件移动成功"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/deleteFile', methods=['DELETE'])
def delete_file():
    """
    文件删除接口：根据 file_id 参数删除数据库中的文件记录。
    """
    try:
        file_id = request.args.get('file_id')
        if not file_id:
            return jsonify({"error": "缺少文件ID参数"}), 400
        conn = get_connection()
        cursor = conn.cursor()
        sql = "DELETE FROM files WHERE id = %s"
        cursor.execute(sql, (file_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "文件删除成功"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- FAQ接口（保持不变） ----------------
@app.route('/faqPage')
def faq_page():
    return send_file('Common_question_bank.html')

@app.route('/faq', methods=['GET', 'POST'])
def faq_operations():
    if request.method == 'GET':
        search = request.args.get('search', '').lower()
        tag_filter = request.args.get('tag', '')
        questions = faq_manager.list_questions()
        results = []
        for q in questions:
            match_search = search in q['title'].lower() or search in q['content'].lower()
            match_tag = not tag_filter or tag_filter in (q.get('tags') or '')
            if match_search and match_tag:
                results.append(q)
        return jsonify(results)
    elif request.method == 'POST':
        data = request.json
        title = data.get('title')
        content = data.get('content')
        tags = data.get('tags', [])
        if not title or not content:
            return jsonify({"error": "标题和内容不能为空"}), 400
        new_q = faq_manager.create_question(title, content, tags)
        return jsonify(new_q), 201

@app.route('/faq/<int:qid>', methods=['GET', 'PUT', 'DELETE'])
def single_faq(qid):
    if request.method == 'GET':
        q = faq_manager.get_question(qid)
        return jsonify(q) if q else ('', 404)
    elif request.method == 'PUT':
        data = request.json
        updated_q = faq_manager.update_question(qid, 
            data.get('title'),
            data.get('content'),
            data.get('tags', []))
        return jsonify(updated_q) if updated_q else ('', 404)
    elif request.method == 'DELETE':
        success = faq_manager.delete_question(qid)
        return jsonify({"message": "删除成功"}) if success else ('', 404)

if __name__ == '__main__':
    app.run(debug=True)
