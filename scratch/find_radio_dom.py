import glob, re

for f in glob.glob('.venv/Lib/site-packages/streamlit/static/static/js/*.js'):
    with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
        c = fp.read()
        if 'stMarkdownContainer' in c and 'radiogroup' in c:
            print("Found in", f)
            # Find around radiogroup
            for m in re.finditer(r'role=[\"\']radiogroup[\"\']', c):
                idx = m.start()
                print("--- RADIOGROUP SNIPPET ---")
                print(c[max(0, idx-300):min(len(c), idx+500)])
                break
            break

