#!/bin/bash

export FLASK_DEBUG=1
export FLASK_ENV=development
export SCENARIO_LANG=en-au
export SCENARIO_PY=demo/scenario.py
export FLASK_APP=scenario_webapi.py
flask run --host 0.0.0.0 --port 5000 --with-threads