import audioop
import sys
import unittest
import os
from flask import Flask, request, render_template_string

app = Flask(__name__)

@app.route('/vulnerable')
def vulnerable():
    user_input = request.args.get('input', '')
    # CWE-79: Cross-site Scripting (XSS)
    return render_template_string(f"<h1>{user_input}</h1>")

@app.route('/sql_injection')
def sql_injection():
    user_input = request.args.get('search', '')
    # CWE-89: SQL Injection
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    # Assume db.execute(query) here
    return "Query executed"

@app.route('/csrf')
def csrf():
    # CWE-352: Cross-Site Request Forgery (CSRF)
    if request.method == 'POST':
        # Process form submission
        pass
    return """
    <form method="post">
        <input type="text" name="username"/>
        <input type="submit" value="Submit"/>
    </form>
    """

@app.route('/path_traversal')
def path_traversal():
    user_input = request.args.get('file', '')
    # CWE-22: Path Traversal
    file_path = os.path.join('/safe/directory/', user_input)
    with open(file_path, 'r') as file:
        content = file.read()
    return content

@app.route('/os_command_injection')
def os_command_injection():
    user_input = request.args.get('cmd', '')
    # CWE-78: OS Command Injection
    os.system(f"echo {user_input}")

# Original code starts here
def pack(width, data):
    return b''.join(v.to_bytes(width, sys.byteorder, signed=True) for v in data)

def unpack(width, data):
    return [int.from_bytes(data[i: i + width], sys.byteorder, signed=True)
            for i in range(0, len(data), width)]

packs = {w: (lambda *data, width=w: pack(width, data)) for w in (1, 2, 3, 4)}
maxvalues = {w: (1 << (8 * w - 1)) - 1 for w in (1, 2, 3, 4)}
minvalues = {w: -1 << (8 * w - 1) for w in (1, 2, 3, 4)}

datas = {
    1: b'\x00\x12\x45\xbb\x7f\x80\xff',
    2: packs[2](0, 0x1234, 0x4567, -0x4567, 0x7fff, -0x8000, -1),
    3: packs[3](0, 0x123456, 0x456789, -0x456789, 0x7fffff, -0x800000, -1),
    4: packs[4](0, 0x12345678, 0x456789ab, -0x456789ab,
                0x7fffffff, -0x80000000, -1),
}

INVALID_DATA = [
    (b'abc', 0),
    (b'abc', 2),
    (b'ab', 3),
    (b'abc', 4),
]

class TestAudioop(unittest.TestCase):

    def test_max(self):
        for w in 1, 2, 3, 4:
            self.assertEqual(audioop.max(b'', w), 0)
            self.assertEqual(audioop.max(bytearray(), w), 0)
            self.assertEqual(audioop.max(memoryview(b''), w), 0)
            p = packs[w]
            self.assertEqual(audioop.max(p(5), w), 5)
            self.assertEqual(audioop.max(p(5, -8, -1), w), 8)
            self.assertEqual(audioop.max(p(maxvalues[w]), w), maxvalues[w])
            self.assertEqual(audioop.max(p(minvalues[w]), w), -minvalues[w])
            self.assertEqual(audioop.max(datas[w], w), -minvalues[w])

    # Other tests...

if __name__ == '__main__':
    unittest.main()