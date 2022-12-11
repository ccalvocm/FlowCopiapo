#!/bin/bash

#export FLASK_ENV=development
#export FLASK_DEBUG=1
export SCENARIO_LANG=es-cl
export SCENARIO_PY=scenario_SIMC.py
export FLASK_APP=../pyticipate/scenario_webapi.py
flask run --host 0.0.0.0 --port 5000 --with-threads
read -p "Press enter to continue"