import logging
from yaspin import yaspin
from yaspin.spinners import Spinners
from lib import run_external_applicaton

def teardown(global_plugin_state, current_configuration, output, test_id):
    run_external_applicaton("minikube delete")