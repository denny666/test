import re
from pathlib import Path
from html import escape

def extract_lines_and_definitions(file_path):
    line_map = {}
    defines = {}
    for i, line in enumerate(Path(file_path).read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        stripped = line.strip()
        line_map[i] = stripped
        if stripped.startswith("#define"):
            match = re.match(r"#define\s+(\w+)\s+(.+)", stripped)
            if match:
                key, value = match.groups()
                defines[key] = value.strip()
    return line_map, defines

def remove_comments(line):
    line = re.sub(r"//.*", "", line)                # 移除 // 註解
    line = re.sub(r"/\*.*?\*/", "", line)           # 移除 /* */ 註解（非跨行）
    return line.strip()

def is_meaningful_difference(line_a, line_b):
    return remove_comments(line_a) != remove_comments(line_b)

def compare_files(file_a, file_b, rel_path, label_a, label_b):
    lines_a, defines_a = extract_lines_and_definitions(file_a)
    lines_b, defines_b = extract_lines_and_definitions(file_b)

    all_lines = set(lines_a.keys()) | set(lines_b.keys())
    line_diffs = []

    for line_no in sorted(all_lines):
        line_text_a = lines_a.get(line_no, "")
        line_text_b = lines_b.get(line_no, "")
        if line_text_a != line_text_b and is_meaningful_difference(line_text_a, line_text_b):
            line_diffs.append(
                f"<tr><td>{line_no}</td><td><pre>{escape(line_text_a)}</pre></td><td><pre>{escape(line_text_b)}</pre></td></tr>"
            )

    define_diffs = []
    for key in defines_a:
        if key in defines_b and defines_a[key] != defines_b[key]:
            define_diffs.append(
                f"<tr><td>{escape(key)}</td><td>{escape(defines_a[key])}</td><td>{escape(defines_b[key])}</td></tr>"
            )

    if not line_diffs and not define_diffs:
        return None

    html = f"<h2>{escape(rel_path.name)}</h2>"
    if define_diffs:
        html += f"<h3>🔧 定義差異（#define）</h3>"
        html += f"<table border='1'><tr><th>參數</th><th>{escape(label_a)}</th><th>{escape(label_b)}</th></tr>"
        html += "".join(define_diffs)
        html += "</table>"

    if line_diffs:
        html += f"<h3>🔍 原始代碼差異（不含註解）</h3>"
        html += f"<table border='1'><tr><th>行號</th><th>{escape(label_a)}</th><th>{escape(label_b)}</th></tr>"
        html += "".join(line_diffs)
        html += "</table>"

    return html

def compare_projects():
    folder_a_str=input("Enter file 1:")
    folder_b_str=input("Enter file 2:")
    output_html_str=input("Enter output file name:")
    html_file=str(output_html_str)+'.html'

    folder_a = Path(str(folder_a_str)).resolve()
    folder_b = Path(str(folder_b_str)).resolve()
    output_html = Path(str(html_file)).resolve()

    label_a = folder_a.name
    label_b = folder_b.name

    results = []
    missing_files = []
    added_files = []

    # 找出 A 有但 B 沒有的檔案
    for file_a in folder_a.rglob("*.[ch]"):
        rel_path = file_a.relative_to(folder_a)
        file_b = folder_b / rel_path
        if file_b.exists():
            diff = compare_files(file_a, file_b, rel_path, label_a, label_b)
            if diff:
                results.append(diff)
        else:
            missing_files.append(rel_path.as_posix())

    # 找出 B 有但 A 沒有的檔案
    for file_b in folder_b.rglob("*.[ch]"):
        rel_path = file_b.relative_to(folder_b)
        file_a = folder_a / rel_path
        if not file_a.exists():
            added_files.append(rel_path.as_posix())

    html_output = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>版本差異報告</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 20px; }}
h2 {{ color: #003366; margin-top: 40px; }}
table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
th, td {{ border: 1px solid #999; padding: 6px; font-size: 14px; vertical-align: top; }}
pre {{ background: #f8f8f8; padding: 5px; border-radius: 4px; white-space: pre-wrap; word-wrap: break-word; }}
</style>
</head>
<body>
<h1>📊 差異報告總覽</h1>
"""

    if missing_files:
        html_output += f"<h2>🚫 {escape(label_b)} 缺少以下檔案（{escape(label_a)} 有但 {escape(label_b)} 沒有）</h2><ul>"
        for path in sorted(missing_files):
            html_output += f"<li>{escape(path)}</li>"
        html_output += "</ul><hr>"

    if added_files:
        html_output += f"<h2>➕ {escape(label_b)} 新增以下檔案（{escape(label_a)} 沒有）</h2><ul>"
        for path in sorted(added_files):
            html_output += f"<li>{escape(path)}</li>"
        html_output += "</ul><hr>"

    if results:
        html_output += "<hr>".join(results)
    else:
        html_output += "<p>🎉 沒有發現任何定義或原始代碼差異。</p>"

    html_output += "</body></html>"
    output_html.write_text(html_output, encoding='utf-8')
    print(f"✅ 差異報告已產出：{output_html}")

# 🏁 執行比對

compare_projects()
