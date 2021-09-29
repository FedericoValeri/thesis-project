from lib import run_external_applicaton


def minikube_nodeport_access(global_plugin_state, current_configuration, output, test_id):
    service = current_configuration["minikube_tunnel_service"]
    cmd = f'minikube service --url {service}'
    run_external_applicaton(cmd)
    
