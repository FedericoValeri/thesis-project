import os
import time
import subprocess
import logging
import shutil
import datetime
from pluginbase import PluginBase


def run_external_applicaton(command, fail_if_result_not_zero=True):
    current_folder = os.getcwd()
    logging.debug(f"Executing {command} in {current_folder}.")
    result = os.system(command)
    if fail_if_result_not_zero and result != 0:
        logging.fatal(f"Could not execute {command}: {result}.")
        raise RuntimeError
    else:
        return result


def replace_values_in_file(file, replacements):
    for replacement in replacements:
        replace_value_in_file(
            file, replacement["search_for"], replacement["replace_with"])


def replace_value_in_file(file, search_for, replace_with):
    with open(file, "r") as f:
        content = f.read()
        content = content.replace(search_for, replace_with)
    with open(file, "w") as f:
        f.write(content)


global_plugin_state = {}


def run_plugins(configuration, section, output, test_id, func):
    result = []
    plugin_list = configuration[section]["enabled_plugins"].split()
    plugin_base = PluginBase(package='plugins')
    plugin_source = plugin_base.make_plugin_source(searchpath=['./plugins'])

    for plugin_name in plugin_list:
        logging.debug(f"Executing {func} of plugin {plugin_name}.")
        plugin = plugin_source.load_plugin(plugin_name)
        try:
            function_to_call = getattr(plugin, func, None)
            if function_to_call != None:
                plugin_state = ", ".join(global_plugin_state.keys())
                logging.debug(
                    f"Current plugin state contains [{plugin_state}]")

                call_result = function_to_call(
                    global_plugin_state, configuration[section], output, test_id)
                result.append(call_result)

        except Exception as e:
            logging.critical(f"Cannot invoke plugin {plugin_name}: {e}")

    return result


def create_output_directory(configuration, section):
    now = datetime.datetime.now()
    test_id_without_timestamp = configuration[section]["test_case_prefix"].lower(
    ) + "-" + section.lower()
    test_id = now.strftime("%Y%m%d%H%M") + "-" + test_id_without_timestamp

    all_outputs = os.path.abspath(os.path.join("./executed"))
    if not os.path.isdir(all_outputs):
        logging.debug(f"Creating {all_outputs}, since it does not exist.")
        os.makedirs(all_outputs)

    if any(x.endswith(test_id_without_timestamp) for x in os.listdir(all_outputs)):
        name_of_existing_folder = next(x for x in os.listdir(
            all_outputs) if x.endswith(test_id_without_timestamp))
        logging.warning(
            f"Deleting {name_of_existing_folder}, since it already exists.")
        shutil.rmtree(os.path.join(all_outputs, name_of_existing_folder))

    output = os.path.join(all_outputs, test_id)
    os.makedirs(output)

    return output, test_id, now
