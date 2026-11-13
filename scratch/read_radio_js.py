with open('.venv/Lib/site-packages/streamlit/static/static/js/Radio.BWQwdNIB.js', 'r', encoding='utf-8') as f:
    c = f.read()
    print("Length:", len(c))
    # Search for data-testid
    for m in [m.start() for m in __import__('re').finditer(r'data-testid', c)]:
        print(c[max(0, m-50):min(len(c), m+150)])
        print("="*40)

