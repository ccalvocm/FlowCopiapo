import json
import numpy
import os

from core.language.converter import convert_file

def translate_resources():
    lang = os.environ.get('SCENARIO_LANG')
    if lang is None:
        lang = 'en-au'
    this_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isdir(os.path.join(this_dir, '../static/resources/js')):
        os.mkdir(os.path.join(this_dir, '../static/resources/js'))
    convert_file(os.path.join(this_dir, 'language/templates/temp_scenario.html'), os.path.join(this_dir, '../static/scenario.html'), os.path.join(this_dir, 'language/translations/lang_scenario_html.json'), lang)
    convert_file(os.path.join(this_dir, 'language/templates/temp_scenario.js'), os.path.join(this_dir, '../static/resources/js/scenario.js'), os.path.join(this_dir, 'language/translations/lang_scenario_js.json'), lang)

def convert_to_json(data):
    def basic_numpy_encoder(obj):
        if isinstance(obj, numpy.float32) or isinstance(obj, numpy.float64) or isinstance(obj, numpy.int16) or isinstance(obj, numpy.int32):
            return str(obj.item())
        raise TypeError(repr(obj) + " is not JSON serializable")
    return json.dumps(data, default=basic_numpy_encoder)