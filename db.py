# db.py
import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',      # 请替换成你的 MySQL 用户名
        password='123456',  # 请替换成你的 MySQL 密码
        database='knowledge_base'
    )
