# faq_manager.py
import json
import os
from datetime import datetime

FAQ_FILE = "faq_data.json"

def load_faq():
    if not os.path.exists(FAQ_FILE):
        return []
    try:
        with open(FAQ_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_faq(data):
    with open(FAQ_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def create_question(title, content, tags):
    questions = load_faq()
    new_id = max(q['id'] for q in questions) + 1 if questions else 1
    new_q = {
        "id": new_id,
        "title": title,
        "content": content,
        "tags": [tags] if isinstance(tags, str) else tags,
        "created_at": datetime.now().isoformat(),
        "updated_at": None
    }
    questions.append(new_q)
    save_faq(questions)
    return new_q

def get_question(qid):
    questions = load_faq()
    return next((q for q in questions if q['id'] == qid), None)

def update_question(qid, title, content, tags):
    questions = load_faq()
    for q in questions:
        if q['id'] == qid:
            q.update({
                "title": title,
                "content": content,
                "tags": tags,
                "updated_at": datetime.now().isoformat()
            })
            save_faq(questions)
            return q
    return None

def delete_question(qid):
    questions = load_faq()
    new_list = [q for q in questions if q['id'] != qid]
    if len(new_list) == len(questions):
        return False
    save_faq(new_list)
    return True

def list_questions():
    return load_faq()
