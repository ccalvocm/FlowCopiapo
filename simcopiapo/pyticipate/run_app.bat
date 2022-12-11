set FLASK_DEBUG=1
set FLASK_ENV=development
set SCENARIO_LANG=en-au
set SCENARIO_PY=demo/scenario.py
set FLASK_APP=scenario_webapi.py
flask run --host 0.0.0.0 --port 5000 --with-threads