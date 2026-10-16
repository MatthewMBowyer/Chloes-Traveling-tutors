from pathlib import Path

p = Path('index.html')
raw = p.read_bytes().decode('utf-8')
crlf = '\r\n' in raw
s = raw.replace('\r\n', '\n') if crlf else raw


def fix(text):
    return text.replace('\n', '\r\n') if crlf else text


old1 = "Chloe started tutoring her younger brother and his friends in Grade 4, inspired by her own"
new1 = "Chloe started tutoring her younger brother and his friends when they were in Grade 4, inspired by her own"
assert old1 in s, "grade 4 sentence not found"
s = s.replace(old1, new1)

old2 = "No child is incapable, no child is \u201cnot smart enough\u201d, and no child should feel less than because"
new2 = "No child is incapable, no child is \u2018not smart enough\u2019, and no child should feel less than because"
assert old2 in s, "double curly quote sentence not found"
s = s.replace(old2, new2)

p.write_text(fix(s), encoding='utf-8')
print("how CTT started wording updated")
