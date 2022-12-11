import importlib
import os
from threading import Semaphore
import uuid


class ScenarioManager():

    def __init__(self):
        self._lock = Semaphore(value=1)

        self._scenarios = {}

        filepath = os.environ.get('SCENARIO_PY')
        if filepath is None:
            filepath = os.path.join(os.getcwd(), 'demo/scenario.py')
        filename = os.path.split(filepath)[1]
        self._module = self._load_plugin_module(filename, filepath)

    def _load_plugin_module(self, name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def _create_working_directory(self, root_dir):
        while True:
            proposed_directory = os.path.join(root_dir, str(uuid.uuid4()))
            if not os.path.exists(proposed_directory):
                os.makedirs(proposed_directory)
                break
        return proposed_directory

    def _create_new_scenario_instance(self, id):
        global_working_dir = os.path.join(os.getcwd(), 'working')
        instance_working_dir = self._create_working_directory(global_working_dir)
        return self._module.Scenario(instance_working_dir)

    def get_scenario(self, session):
        self._lock.acquire()
        if 'id' not in session:
            id = uuid.uuid4()
            session['id'] = id
            self._scenarios[id] = self._create_new_scenario_instance(id)
        else:
            id = session['id']
            if id not in self._scenarios:
                self._scenarios[id] = self._create_new_scenario_instance(id)
        self._lock.release()
        return self._scenarios[id]