import os
import logging
import subprocess
import time
from lib import run_external_applicaton

def install_addons(global_plugin_state, current_configuration, output, test):
    addons_path = "istio-addons"
    run_external_applicaton(f'kubectl apply -f {addons_path}') 