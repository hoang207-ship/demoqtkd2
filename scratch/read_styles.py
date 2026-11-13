with open('.venv/Lib/site-packages/streamlit/static/static/js/Radio.BWQwdNIB.js', 'r', encoding='utf-8') as f:
    c = f.read()
    # find where ge = or _e = or he =
    for var in ['ge=', 'he=', 'me=', '_e=', 'fe=', 'pe=']:
        idx = c.find(var)
        if idx != -1:
            print(var, c[idx:idx+250])
            print("="*40)

