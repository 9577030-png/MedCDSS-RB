import os
import chardet

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw = f.read(10000)
    result = chardet.detect(raw)
    return result['encoding']

def convert_to_utf8(file_path):
    enc = detect_encoding(file_path)
    if enc is None or enc.lower() in ('utf-8', 'ascii'):
        return
    try:
        with open(file_path, 'r', encoding=enc) as f:
            content = f.read()
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Converted {file_path} from {enc} to UTF-8")
    except Exception as e:
        print(f"Failed {file_path}: {e}")

root = '.'
extensions = ('.yaml', '.yml', '.py', '.json', '.txt')
for dirpath, _, filenames in os.walk(root):
    for fname in filenames:
        if fname.endswith(extensions):
            path = os.path.join(dirpath, fname)
            convert_to_utf8(path)