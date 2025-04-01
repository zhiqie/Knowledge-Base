# faq_manager.py
import mysql.connector
from db import get_connection
from datetime import datetime

def create_question(title, content, tags):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        tag_str = ','.join(tags) if isinstance(tags, list) else tags
        sql = "INSERT INTO faq (title, content, tags, created_at) VALUES (%s, %s, %s, %s)"
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(sql, (title, content, tag_str, created_at))
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return {"id": new_id, "title": title, "content": content, "tags": tags, "created_at": created_at, "updated_at": None}
    except Exception as e:
        print("创建 FAQ 出错：", e)
        # 可选：重新抛出或返回错误信息
        return None

def get_question(qid):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    sql = "SELECT * FROM faq WHERE id = %s"
    cursor.execute(sql, (qid,))
    result = cursor.fetchone()
    if result and result['tags']:
        result['tags'] = result['tags'].split(',')  # 确保 tags 是列表格式
    cursor.close()
    conn.close()
    return result

def update_question(qid, title, content, tags):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    tag_str = ','.join(tags) if isinstance(tags, list) else tags
    updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sql = "UPDATE faq SET title=%s, content=%s, tags=%s, updated_at=%s WHERE id=%s"
    cursor.execute(sql, (title, content, tag_str, updated_at, qid))
    conn.commit()
    sql_select = "SELECT * FROM faq WHERE id = %s"
    cursor.execute(sql_select, (qid,))
    updated_q = cursor.fetchone()
    cursor.close()
    conn.close()
    return updated_q

def delete_question(qid):
    conn = get_connection()
    cursor = conn.cursor()
    sql = "DELETE FROM faq WHERE id = %s"
    cursor.execute(sql, (qid,))
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    conn.close()
    return affected > 0

def list_questions():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    sql = "SELECT * FROM faq"
    cursor.execute(sql)
    results = cursor.fetchall()
    for result in results:
        result['tags'] = result['tags'].split(',') if result['tags'] else []
    cursor.close()
    conn.close()
    return results

def list_files(city, base_type):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        sql = "SELECT * FROM file_metadata WHERE city = %s AND base_type = %s"
        cursor.execute(sql, (city, base_type))
        files = cursor.fetchall()
        cursor.close()
        conn.close()
        return files
    except Exception as e:
        print("获取文件列表失败:", e)
        return []
