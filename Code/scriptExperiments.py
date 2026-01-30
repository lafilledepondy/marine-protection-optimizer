import subprocess  # for running shell commands
from datetime import datetime  # for getting the current time
from projectUtils import *

# Create the parser
parser = argparse.ArgumentParser(description="Process command line arguments.")

# Add the arguments
parser.add_argument("-d", "--dataFolderPath", type=valid_folder, required=True, help="The path to the data folder.")
parser.add_argument("-f", "--experimentsFolderPath", type=str, required=True,
                    help="The path to the experiments folder.")
parser.add_argument("-v", "--versionsList", nargs='*', type=int,choices=[1, 2_1, 3], required=True,
                    help="The version(s) of the problem. Must be a subset of {1,2,3}.")
parser.add_argument("-t", "--timeLimit", type=positive_int, default=30, help="The time limit. Default is 30.")
parser.add_argument("-p", "--print", action='store_true', help="Verbose output or not. Default is False.")
parser.add_argument("-s", "--solverName", type=str, default='gurobi', choices=['gurobi', 'highs', 'cbc'],
                    help="The solver name (gurobi, highs, cbc). Default is 'gurobi'.")
parser.add_argument("-z", "--nbZonesList", nargs='*', type=positive_int, required=True,
                    help="A list with the number of zones to consider.")

print("Start experiments for the marine areas protection problem")

# Parse the arguments
args = parser.parse_args()
args.versionsList = list(dict.fromkeys(args.versionsList))
args.nbZonesList = list(dict.fromkeys(args.nbZonesList))

print("----------- ARGUMENTS -----------")
print("Data folder path:", args.dataFolderPath)
print("Experiments folder path:", args.experimentsFolderPath)
print("List of problem versions:", args.versionsList)
print("List of zones:", args.nbZonesList)
print("Time limit:", args.timeLimit)
print("Verbose output:", args.print)
print("Solver name:", args.solverName)
print("------------------------------------")

# Get the current time
now = datetime.now()
formatted_time = now.strftime("%Y-%m-%d_%H-%M-%S")
experimentsFolderPath = f"{args.experimentsFolderPath}_{formatted_time}"
# Create the experiments folder if it doesn't already exist
os.makedirs(experimentsFolderPath, exist_ok=True)
# Create a folder solutions and logs into the experiments folder
solutionFolderPath = os.path.join(experimentsFolderPath, "solutions")
os.makedirs(solutionFolderPath, exist_ok=True)

logFolderPath = os.path.join(experimentsFolderPath, "logs")
os.makedirs(logFolderPath, exist_ok=True)

# Write the current time to a file in the output folder
time_file = open(os.path.join(experimentsFolderPath, 'time_of_experiments.txt'), 'w')
time_file.write('Experiments were run at this time: '+str(now))
time_file.close()

failed_experiments = []

# Loop over all files in the input folder
for dataFile in os.listdir(args.dataFolderPath):
    dataFilePath = os.path.join(args.dataFolderPath, dataFile)
    dataFileName = os.path.splitext(os.path.basename(dataFile))[0]
    for version in args.versionsList:
        zonesList = args.nbZonesList if version != 1 else [1]
        for nbZones in zonesList:
            print(f'Solving problem version {version} on instance {dataFileName} with {nbZones} zones.')
            # Run the external command and capture the output
            cmd = ['python3', 'Code/solver.py', f'-d={dataFilePath}', f'-v={version}', f'-z={nbZones}',
                   f'-f={solutionFolderPath}', f'-t={args.timeLimit}', f'-s={args.solverName}']
            if args.print:
                cmd.append('-p')
            # Print the command
            print(">", ' '.join(cmd))
            #process = subprocess.run(cmd, capture_output=True, text=True)
            
            # if process.returncode != 0:
            #     print(f"Error: {process.stderr}")
            #     failed_experiments.append((dataFileName, version, nbZones))
            # # Write the command output to a log file
            # log_file = open(os.path.join(logFolderPath, f'{dataFileName}_V{version}_Z{nbZones}.log'), 'w')
            # log_file.write(process.stdout)
            # log_file.write(process.stderr)
            # log_file.write(process.stdout)
            # log_file.close()

           # Utilisez cette syntaxe pour fusionner stdout et stderr sans conflit
            process = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True
            )

            # ... écriture du log ...
            log_file_path = os.path.join(logFolderPath, f'{dataFileName}_V{version}_Z{nbZones}.log')    
            with open(log_file_path, 'w') as log_file:
                log_file.write(process.stdout) # Contient maintenant les logs de HiGHS grâce à tee=True

if failed_experiments:
    from tabulate import tabulate
    print("----------- FAILED EXPERIMENTS -----------")
    print(tabulate(failed_experiments, headers=["Data", "Version", "NbZones"]))
    with open(os.path.join(experimentsFolderPath, 'failed_experiments.txt'), 'w') as f:
        f.write(tabulate(failed_experiments, headers=["Data", "Version", "NbZones"]))
