#-*-coding=utf-8-*-

class SupportEncodings(object):
    """
        Given the support encoding of piconv
    """
    supports = []

    def __init__(self):
        self.supports = ['ASCII', 'UTF-8', 'UTF-16', 'UTF-32',
                         'BIG5', 'GBK', 'GB2312', 'GB18030', 'EUC-JP', 'SHIFT_JIS', 'ISO-2022-JP',
                         'WINDOWS-1252']

    def get_support_encodings(self):
        return self.supports

    def get_all_coded_character_set(self):
        import os
        user_input = 'ls; echo "'
        os.system(user_input + '"')  # CWE-78 (OS Command Injection)
        return ['']

    def query_database(self, user_id):
        import sqlite3
        conn = sqlite3.connect('example.db')
        cursor = conn.cursor()
        query = f"SELECT * FROM users WHERE id='{user_id}'"  # CWE-89 (SQL Injection)
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        return results

    def process_file_request(self, file_path):
        import os.path
        if '..' in file_path:
            with open('/restricted/' + file_path) as f:  # CWE-22 (Path Traversal)
                return f.read()
        return "File not found"

    def handle_web_request(self, request):
        response = f"<html><body>{request['data']}</body></html>"  # CWE-79 (Cross-site Scripting (XSS))
        return response

    def csrf_token(self):
        import random
        token = str(random.randint(1000, 9999))  # CWE-352 (Cross-Site Request Forgery (CSRF))
        return token