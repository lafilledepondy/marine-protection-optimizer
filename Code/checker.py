import subprocess  # for running shell commands
from projectUtils import *
from solutionValidator import *

# Create the parser
parser = argparse.ArgumentParser(description="Process command line arguments.")

# Add the arguments
parser.add_argument("-d", "--dataFolderPath", type=valid_folder, required=True, help="The path to the data folder.")
parser.add_argument("-f", "--solutionsFolderPath", type=str, required=True,
                    help="The path to the solutions folder.")
parser.add_argument("-v", "--versionsList", nargs='*', type=int,choices=[1, 2, 3], required=True,
                    help="The version(s) of the problem. Must be a subset of {1,2,3}.")
parser.add_argument("-p", "--print", action='store_true', help="Verbose output or not. Default is False.")
parser.add_argument("-z", "--nbZonesList", nargs='*', type=positive_int, required=True,
                    help="A list with the number of zones to consider.")

# Parse the arguments
args = parser.parse_args()
args.versionsList = list(dict.fromkeys(args.versionsList))
args.nbZonesList = list(dict.fromkeys(args.nbZonesList))

print("----------- ARGUMENTS -----------")
print("Data folder path:", args.dataFolderPath)
print("Solutions folder path:", args.solutionsFolderPath)
print("List of problem versions:", args.versionsList)
print("List of zones:", args.nbZonesList)
print("Verbose output:", args.print)
print("------------------------------------")

nb_solutions_feasible = 0
nb_solutions_infeasible = 0
nb_solutions_missing = 0
nb_solutions_error_checker = 0
nb_solutions_pb_infeasible = 0


failed_checks = []

# Loop over all .txt files in the input folder
for dataFile in os.listdir(args.dataFolderPath):
    if not dataFile.endswith('.txt'):
        continue
    dataFilePath = os.path.join(args.dataFolderPath, dataFile)
    dataFileName = os.path.splitext(os.path.basename(dataFile))[0]
    for version in args.versionsList:
        zonesList = args.nbZonesList if version != 1 else [1]
        for nbZones in zonesList:
            print(f'Check solution for instance {dataFileName} for problem version {version} with {nbZones} zones.')
            solutionFilePath = os.path.join(args.solutionsFolderPath, f"{dataFileName}_V{version}_Z{nbZones}.sol")
            print(f'Looking for: {solutionFilePath}')
            print(f'File exists: {os.path.exists(solutionFilePath)}')
            print(f'Is file: {os.path.isfile(solutionFilePath)}')
            if os.path.isfile(solutionFilePath):
                # Validation check
                is_valid, error_msg = checkSolution(solutionFilePath, version, nbZones, dataFilePath)
                if not is_valid:
                    nb_solutions_infeasible += 1
                    failed_checks.append((dataFileName, version, nbZones, f"Validation failed: {error_msg}"))
                    print(f'-> Infeasible: {error_msg}')
                else:
                    nb_solutions_feasible += 1
                    print('-> Feasible')
            else:
                print(f"Solution file {dataFileName}_V{version}_Z{nbZones}.sol is missing.")
                nb_solutions_missing += 1
                failed_checks.append((dataFileName, version, nbZones, "Missing"))

if failed_checks:
    print("----------- FAILED CHECKS -----------")
    from tabulate import tabulate
    print(tabulate(failed_checks, headers=["Data", "Version", "NbZones", "Issue"]))
    # print("Data\t\t Version\t NbZones\t Issue")
    # for check in failed_checks:
    #     print(f"{check[0]}\t\t{check[1]}\t {check[2]}\t {check[3]}")

print("----------- SUMMARY -----------")
print("Number of feasible solutions:", nb_solutions_feasible)
print("Number of infeasible solutions:", nb_solutions_infeasible)
print("Number of solution marked as problem infeasible:", nb_solutions_pb_infeasible)
print("Number of missing solutions:", nb_solutions_missing)
print("Number of error in checker:", nb_solutions_error_checker)
