import subprocess

# Define command
command ='Rscript'
script_path ='./R/dateRequestsOPAggregator.R'

# Build subprocess command
cmd = [command, script_path]

# check_output will run the command and store to result
x = subprocess.check_output(cmd, universal_newlines=True)

f = open("./R/output/out.txt", "w")
subprocess.call(cmd, universal_newlines=True, stdout=f)

print("---------- WORKLOADS SUCCESFULLY AGGREGATED! ----------")
