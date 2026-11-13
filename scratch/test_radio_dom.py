import glob, re

for f in glob.glob('.venv/Lib/site-packages/streamlit/static/static/js/*.js'):
    with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
        c = fp.read()
        if 'stRadio' in c:
            matches = re.findall(r'data-testid=[\"\']([a-zA-Z0-9_-]+)[\"\']', c)
            r_matches = [x for x in matches if 'radio' in x.lower()]
            if r_matches:
                print(f, set(r_matches))
                # Print a small snippet around stRadio
                idx = c.find('stRadio')
                print(c[max(0, idx-100):min(len(c), idx+300)])
                break

