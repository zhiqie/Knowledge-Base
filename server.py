from flask import Flask, request, jsonify, send_file
import os
import shutil
import faq_manager

app = Flask(__name__, static_folder='.', static_url_path='')

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 使用相对路径，城市目录放在项目根目录下的 "city" 文件夹中
CITY_FOLDER = os.path.join(BASE_DIR, "city")
os.makedirs(CITY_FOLDER, exist_ok=True)

def get_base_folder(base_type):
    return "业务逻辑库" if base_type == "business" else "产品逻辑库"

def get_expected_root(city, base_type):
    safe_city = city.strip().replace('..', '')
    base_folder = get_base_folder(base_type)
    return os.path.abspath(os.path.join(CITY_FOLDER, safe_city, base_folder))

# 修改根路由，返回首页 index.html
@app.route('/')
def index():
    return send_file('index.html')

@app.route('/getCities')
def get_cities():
    try:
        cities = []
        for entry in os.listdir(CITY_FOLDER):
            if os.path.isdir(os.path.join(CITY_FOLDER, entry)):
                cities.append(entry)
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

        results = []
        if city:
            expected_root = get_expected_root(city, base_type)
            for root, dirs, files in os.walk(expected_root):
                for file in files:
                    if query.lower() in file.lower():
                        results.append({
                            "name": file,
                            "path": os.path.relpath(os.path.join(root, file), expected_root).replace("\\", "/"),
                            "city": city
                        })
        else:
            for entry in os.listdir(CITY_FOLDER):
                city_dir = os.path.join(CITY_FOLDER, entry)
                if os.path.isdir(city_dir):
                    expected_root = get_expected_root(entry, base_type)
                    if not os.path.exists(expected_root):
                        continue
                    for root, dirs, files in os.walk(expected_root):
                        for file in files:
                            if query.lower() in file.lower():
                                results.append({
                                    "name": file,
                                    "path": os.path.relpath(os.path.join(root, file), expected_root).replace("\\", "/"),
                                    "city": entry
                                })
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

        expected_root = get_expected_root(city, base_type)
        target_dir = os.path.abspath(os.path.join(expected_root, current_path.lstrip('/')))
        if not target_dir.startswith(expected_root):
            return jsonify({"error": "非法路径访问"}), 403

        if not os.path.exists(target_dir):
            return jsonify({"structure": []})

        def scan_directory(path, relative_path=""):
            structure = []
            try:
                for entry in os.listdir(path):
                    entry_path = os.path.join(path, entry)
                    item = {
                        "name": entry,
                        "path": os.path.join(relative_path, entry).replace("\\", "/")
                    }
                    if os.path.isdir(entry_path):
                        item["type"] = "directory"
                        item["children"] = scan_directory(entry_path, os.path.join(relative_path, entry))
                    else:
                        item["type"] = "file"
                    structure.append(item)
            except Exception as e:
                print(f"目录扫描错误: {str(e)}")
            return structure

        return jsonify({
            "current_path": current_path,
            "structure": scan_directory(target_dir, current_path)
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
        return jsonify({"message": "文件删除成功"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- 新增城市管理接口 ----------------

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
        return jsonify({"message": f"城市【{city}】目录创建成功。"})
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
            return jsonify({"message": f"城市【{city}】删除成功。"})
        else:
            return jsonify({"error": "指定的城市不存在。"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- FAQ相关接口 ----------------

@app.route('/faqPage')
def faq_page():
    return send_file('常用问题库.html')

@app.route('/faq', methods=['GET', 'POST'])
def faq_operations():
    if request.method == 'GET':
        search = request.args.get('search', '').lower()
        tag_filter = request.args.get('tag', '')
        
        questions = faq_manager.list_questions()
        results = []
        for q in questions:
            match_search = search in q['title'].lower() or search in q['content'].lower()
            match_tag = not tag_filter or tag_filter in q.get('tags', [])
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
