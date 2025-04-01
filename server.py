# server.py
from flask import Flask, request, jsonify, send_file
import os
import shutil
import faq_manager
from db import get_connection

app = Flask(__name__, static_folder='.', static_url_path='')

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 文件实际存储位置（仍使用本地文件夹存储文件内容）
CITY_FOLDER = os.path.join(BASE_DIR, "city")

def get_base_folder(base_type):
    return "业务逻辑库" if base_type == "business" else "产品逻辑库"

def get_expected_root(city, base_type):
    safe_city = city.strip().replace('..', '')
    base_folder = get_base_folder(base_type)
    return os.path.abspath(os.path.join(CITY_FOLDER, safe_city, base_folder))

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/getCities')
def get_cities():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        sql = "SELECT DISTINCT city FROM file_metadata"
        cursor.execute(sql)
        cities = [row['city'] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify(cities)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/searchFiles', methods=['GET'])
def search_files():
    try:
        query = request.args.get('query')
        base_type = request.args.get('type')
        city = request.args.get('city')
        if not query or not base_type:
            return jsonify({"error": "缺少必要参数"}), 400
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        if city:
            sql = "SELECT * FROM file_metadata WHERE city = %s AND base_type = %s AND file_name LIKE %s"
            cursor.execute(sql, (city, base_type, '%' + query + '%'))
        else:
            sql = "SELECT * FROM file_metadata WHERE base_type = %s AND file_name LIKE %s"
            cursor.execute(sql, (base_type, '%' + query + '%'))
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/getSubDirectories', methods=['GET'])
def get_sub_directories():
    try:
        city = request.args.get('city')
        base_type = request.args.get('type')
        current_path = request.args.get('path', '')
        if not all([city, base_type]):
            return jsonify({"error": "必要参数缺失"}), 400
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        # 假设 file_path 存储的是从 expected_root 开始的相对路径
        like_pattern = current_path.rstrip('/') + '/%'
        sql = "SELECT * FROM file_metadata WHERE city = %s AND base_type = %s AND file_path LIKE %s"
        cursor.execute(sql, (city, base_type, like_pattern))
        structure = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({
            "current_path": current_path,
            "structure": structure
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/preview', methods=['GET'])
def preview_file():
    try:
        city = request.args.get('city')
        base_type = request.args.get('type', 'business')
        file_path = request.args.get('file')
        if not all([city, file_path]):
            return jsonify({"error": "缺少必要参数"}), 400
        expected_root = get_expected_root(city, base_type)
        abs_path = os.path.abspath(os.path.join(expected_root, file_path.strip().replace('..', '')))
        if not abs_path.startswith(expected_root) or not os.path.exists(abs_path):
            return jsonify({"error": "非法路径或文件不存在"}), 403
        return send_file(abs_path)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/moveFile', methods=['POST'])
def move_file():
    try:
        data = request.get_json()
        source_city = data.get('sourceCity')
        target_city = data.get('targetCity')
        base_type = data.get('type', 'business')
        old_path = data.get('oldPath')
        new_path = data.get('newPath')
        if not all([source_city, target_city, old_path, new_path]):
            return jsonify({"error": "缺少必要参数"}), 400
        source_expected_root = get_expected_root(source_city, base_type)
        target_expected_root = get_expected_root(target_city, base_type)
        abs_old_path = os.path.abspath(os.path.join(source_expected_root, old_path.strip().replace('..', '')))
        abs_new_path = os.path.abspath(os.path.join(target_expected_root, new_path.strip().replace('..', '')))
        if not abs_old_path.startswith(source_expected_root) or not os.path.exists(abs_old_path):
            return jsonify({"error": "非法旧路径或文件不存在"}), 403
        if not abs_new_path.startswith(target_expected_root):
            return jsonify({"error": "非法新路径"}), 403
        os.makedirs(os.path.dirname(abs_new_path), exist_ok=True)
        shutil.move(abs_old_path, abs_new_path)
        # 同步更新数据库中的文件元数据
        conn = get_connection()
        cursor = conn.cursor()
        new_file_name = os.path.basename(new_path)
        sql = "UPDATE file_metadata SET city = %s, file_path = %s, file_name = %s WHERE city = %s AND file_path = %s"
        cursor.execute(sql, (target_city, new_path, new_file_name, source_city, old_path))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "文件移动成功"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/deleteFile', methods=['DELETE'])
def delete_file():
    try:
        city = request.args.get('city')
        base_type = request.args.get('type', 'business')
        file_path = request.args.get('file')
        if not city or not file_path:
            return jsonify({"error": "缺少必要参数"}), 400
        expected_root = get_expected_root(city, base_type)
        abs_path = os.path.abspath(os.path.join(expected_root, file_path.strip().replace('..', '')))
        if not abs_path.startswith(expected_root):
            return jsonify({"error": "非法路径"}), 403
        if not os.path.exists(abs_path):
            return jsonify({"error": "文件不存在"}), 404
        os.remove(abs_path)
        # 删除数据库中的记录
        conn = get_connection()
        cursor = conn.cursor()
        sql = "DELETE FROM file_metadata WHERE city = %s AND file_path = %s"
        cursor.execute(sql, (city, file_path))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "文件删除成功"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/city/create', methods=['POST'])
def create_city():
    data = request.get_json() or {}
    city = data.get('city')
    base_type = data.get('type', 'business')
    if not city:
        return jsonify({"error": "城市名称不能为空"}), 400
    safe_city = city.strip().replace('..', '')
    base_folder = get_base_folder(base_type)
    city_path = os.path.join(CITY_FOLDER, safe_city)
    business_path = os.path.join(city_path, base_folder)
    subdirs = ["合同库", "文档库", "视频库"]
    try:
        os.makedirs(business_path, exist_ok=True)
        for subdir in subdirs:
            os.makedirs(os.path.join(business_path, subdir), exist_ok=True)
        # 如有需要，可将城市信息写入数据库（本示例中文件元数据表主要记录文件信息）
        return jsonify({"message": f"城市〖{city}〗目录创建成功。"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/city/delete', methods=['DELETE'])
def delete_city():
    data = request.get_json() or {}
    city = data.get('city')
    base_type = data.get('type', 'business')
    if not city:
        return jsonify({"error": "城市名称不能为空"}), 400
    safe_city = city.strip().replace('..', '')
    city_path = os.path.join(CITY_FOLDER, safe_city)
    try:
        if os.path.exists(city_path):
            shutil.rmtree(city_path)
        # 删除数据库中该城市的文件记录
        conn = get_connection()
        cursor = conn.cursor()
        sql = "DELETE FROM file_metadata WHERE city = %s"
        cursor.execute(sql, (city,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": f"城市〖{city}〗删除成功。"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
