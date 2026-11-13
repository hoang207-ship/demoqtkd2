with open('.venv/Lib/site-packages/streamlit/static/static/js/Radio.BWQwdNIB.js', 'r', encoding='utf-8') as f:
    c = f.read()
    idx = c.find('stRadioOption')
    print(c[max(0, idx-100):min(len(c), idx+1000)])

