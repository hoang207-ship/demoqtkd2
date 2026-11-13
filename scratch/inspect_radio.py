import os

for root, dirs, files in os.walk('.venv/Lib/site-packages/streamlit'):
    for f in files:
        if f.endswith('.js') and 'static' in root:
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                c = fp.read()
                if 'data-testid="stRadio"' in c or 'data-testid=\\"stRadio\\"' in c or 'stRadio' in c:
                    pos = c.find('stRadio')
                    if pos != -1:
                        print("File:", p)
                        snippet = c[max(0, pos-200):min(len(c), pos+400)]
                        print("Snippet:\n", snippet)
                        exit(0)
print("Not found")

