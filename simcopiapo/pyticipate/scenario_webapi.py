from flask import Flask, request, send_file, send_from_directory, session
from flask_headers import headers
import os

from core.scenario.scenario_manager import ScenarioManager
from core.util_api import translate_resources, convert_to_json

app = Flask(__name__)
app.static_folder = 'static'

app.secret_key = 'R0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

scnr_mngr = ScenarioManager()

def get_scenario():
    return scnr_mngr.get_scenario(session)

def to_json(data):
    return convert_to_json(data)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/resources/img'), 'favicon.ico')

@app.route('/')
def main_page():
    translate_resources()
    return app.send_static_file('scenario.html')

@app.route('/get_scenario_metadata/')
def get_scenario_metadata():
    active_scenario = get_scenario()
    return to_json(active_scenario.get_metadata())

@app.route('/get_simulation_dates/')
@headers({'Cache-Control':'public, max-age=-1'})
def get_simulation_dates():
    active_scenario = get_scenario()
    sim_dates = active_scenario.get_simulation_dates()
    sim_dates['now'] = active_scenario.get_current_date()
    return to_json(sim_dates)

@app.route('/export_results/', methods = ['POST'])
@headers({'Cache-Control':'public, max-age=-1'})
def export_results():
    active_scenario = get_scenario()
    return to_json(active_scenario.export_results())

@app.route('/get_layers/')
@headers({'Cache-Control':'public, max-age=-1'})
def get_layers():
    active_scenario = get_scenario()
    return to_json(active_scenario.get_all_layers_metadata())

@app.route('/get_inputs/')
@headers({'Cache-Control':'public, max-age=-1'})
def get_inputs():
    active_scenario = get_scenario()
    return to_json(active_scenario.get_all_inputs_metadata())

@app.route('/get_outputs/')
@headers({'Cache-Control':'public, max-age=-1'})
def get_outputs():
    active_scenario = get_scenario()
    return to_json(active_scenario.get_all_outputs_metadata())

@app.route('/reset_scenario', methods = ['POST'])
def reset_scenario():
    active_scenario = get_scenario()
    active_scenario.reset_scenario()
    return to_json({ 'now' : active_scenario.get_current_date() })

@app.route('/run_scenario', methods = ['POST'])
def run_scenario():
    active_scenario = get_scenario()
    run_args = request.get_json(force=True)
    num_timesteps = run_args['num_timesteps']
    inputs = run_args['input_values']
    active_scenario.set_all_inputs_values(inputs)
    active_scenario.run_scenario_time_step(num_timesteps)
    return to_json(
        { 'now' : active_scenario.get_current_date(),
          'end' : active_scenario.get_simulation_dates()['end'],
          'outputs' : active_scenario.get_all_outputs_values()
        }
    )

@app.route('/get_run_status/')
def get_run_status():
    active_scenario = get_scenario()
    run_status = active_scenario.get_run_status()
    return to_json(run_status)

@app.route('/get_all_layer_data/')
@headers({'Cache-Control':'public, max-age=-1'})
def get_all_layer_data():
    active_scenario = get_scenario()
    return to_json(active_scenario.get_all_layers_values())

@app.route('/get_all_input_data/')
@headers({'Cache-Control':'public, max-age=-1'})
def get_all_input_data():
    active_scenario = get_scenario()
    return to_json(active_scenario.get_all_inputs_values())

@app.route('/get_all_output_data/')
@headers({'Cache-Control':'public, max-age=-1'})
def get_all_output_data():
    active_scenario = get_scenario()
    return to_json(active_scenario.get_all_outputs_values())

@app.route('/get_layer_data_info/', methods = ['POST'])
def get_layer_data_info():
    active_scenario = get_scenario()
    ld_args = request.get_json(force=True)
    layer_id = ld_args['layer_id']
    type = ld_args['type']
    ident = ld_args['ident']
    return to_json(active_scenario.get_layer_data_metadata(layer_id, type, ident))

@app.route('/get_layer_data/', methods = ['POST'])
def get_layer_data():
    active_scenario = get_scenario()
    ld_args = request.get_json(force=True)
    layer_id = ld_args['layer_id']
    type = ld_args['type']
    ident = ld_args['ident']
    return to_json(active_scenario.get_layer_data(layer_id, type, ident))

@app.route('/get_image/')
def get_image():
    active_scenario = get_scenario()
    gi_args = request.args
    id = gi_args['id']
    image_data = active_scenario.get_image_data(id)
    image_buffer = image_data[0]
    mimetype = image_data[1]
    return send_file(image_buffer, mimetype=mimetype)

@app.route('/get_points_of_interest/')
def get_points_of_interest():
    active_scenario = get_scenario()
    return to_json(active_scenario.get_points_of_interest())

@app.route('/get_groupings/', methods = ['POST'])
def get_groupings():
    active_scenario = get_scenario()
    gg_args = request.get_json(force=True)
    input = gg_args['input']
    return to_json(active_scenario.get_groupings(input))

@app.route('/get_scenario_resource/<path:resource>')
def get_scenario_resources(resource):
    active_scenario = get_scenario()
    path = active_scenario.path_for_resource(resource)
    if os.path.exists(path):
        directory, file = os.path.split(path)
        return send_from_directory(directory, file)
    else:
        return ''

application = app
if __name__ == '__main__':
    application.run(host='0.0.0.0',port=5000)
