import os
import socket

from dojo.lib import constants
from pathlib import Path
import jsonpickle
import importlib.util


def configuration_json_serializer(obj):
    import cyst.core.environment.serialization
    return jsonpickle.encode(obj, make_refs=True, indent=2, keys=True)


def import_and_serialize_configs(file_name):
    python_config_path = constants.PATH_CONFIGURATIONS.joinpath(file_name, file_name + ".py")
    if not python_config_path.exists():
        raise RuntimeError(
            f"File '{file_name}' not found in configurations folder. Please check the path and try again.")

    try:
        spec = importlib.util.spec_from_file_location("module.name", python_config_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, 'all_configs'):
            all_configs = getattr(module, 'all_configs')
            serialized_data = configuration_json_serializer(all_configs)

            # Create JSON file with the same name as the Python file in the same folder
            json_file_path = constants.PATH_CONFIGURATIONS.joinpath(file_name, file_name + ".json")
            with open(json_file_path, 'w') as json_file:
                json_file.write(serialized_data)

        else:
            raise RuntimeError("The variable 'all_configs' is not found in the specified file.")
    except Exception as e:
        raise e

def ensure_json_configuration(file_name):
    path = constants.PATH_CONFIGURATIONS.joinpath(file_name, file_name + ".json")
    if not path.exists():
        import_and_serialize_configs(file_name)
    return path

def list_configuration_files() -> list[str]:
    return [f for f in os.listdir(constants.PATH_CONFIGURATIONS) if os.path.isdir(os.path.join(constants.PATH_CONFIGURATIONS, f))]


def read_configuration_file(file_name: str) -> str:
    path = constants.PATH_CONFIGURATIONS.joinpath(file_name, file_name + ".json")
    with open(path, 'r') as f:
        return f.read()


last_agent_env_port: int = 8282
async def set_first_available_env_manager_port(host='localhost') -> int:
    global last_agent_env_port
    while True:
        last_agent_env_port += 1
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex((host, last_agent_env_port))
            if result != 0:
                print("Found available port: " + str(last_agent_env_port))
                return last_agent_env_port
