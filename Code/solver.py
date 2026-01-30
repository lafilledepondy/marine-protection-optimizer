from models import *
import sys
import time
import argparse
import os
import platform

import pyomo.environ as pe
import pyomo.opt as po

from projectUtils import *
from data import *
from solutionValidator import checkSolution

# -----------------------------
# Argument parser
# -----------------------------
parser = argparse.ArgumentParser(description="Process command line arguments.")

parser.add_argument("-d", "--dataFilePath", type=valid_file, required=True,
                    help="The path to the data file.")
parser.add_argument("-v", "--version", type=int, required=True, choices=[1, 2_1, 2_2, 3],
                    help="The version of the problem.")
parser.add_argument("-z", "--nbZones", type=positive_int, required=True,
                    help="The number of zones.")
parser.add_argument("-t", "--timeLimit", type=positive_int, default=30,
                    help="The time limit. Default is 30.")
parser.add_argument("-p", "--print", action="store_true",
                    help="Verbose output or not.")
parser.add_argument("-s", "--solverName", type=str, default="gurobi",
                    choices=["gurobi", "highs", "cbc"],
                    help="The solver name (gurobi, highs, cbc).")
parser.add_argument("-f", "--solutionFolderPath", type=valid_folder, required=True,
                    help="The path to the solution folder.")

args = parser.parse_args()

print("----------- ARGUMENTS -----------")
print("Data file path =", args.dataFilePath)
print("Problem version =", args.version)
print("Number of zones =", args.nbZones)
print("Time limit =", args.timeLimit)
print("Verbose output =", args.print)
print("Solver name =", args.solverName)
print("Solution folder path =", args.solutionFolderPath)
print("------------------------------------")


# -----------------------------
# Solver name normalization
# -----------------------------
if args.solverName == "highs":
    args.solverName = "appsi_highs"


# -----------------------------
# Read data
# -----------------------------
dataFileName = os.path.splitext(os.path.basename(args.dataFilePath))[0]
data = readDataFromFile(args.dataFilePath)
data.setNbZonesMax(args.nbZones)

# -----------------------------
# Draw data
# -----------------------------
# drawGrid(data)

# -----------------------------
# Draw Distribution
# -----------------------------
# drawDistribution(data)

# -----------------------------
# Draw DistributionSpecies
# -----------------------------
# num_species = data.nbSpecies()
# cols = 3
# rows = (num_species + cols - 1) // cols
# fig, axes = plt.subplots(rows, cols, figsize=(15, 5*rows))
# axes = axes.flatten()

# import matplotlib
# from matplotlib.colors import Normalize

# cmap = matplotlib.colormaps.get_cmap('viridis')
# norm = Normalize(vmin=0, vmax=1)

# for species_id in range(num_species):
#     drawDistributionSpecies(data, species_id, axes[species_id], cmap, norm)

# for idx in range(num_species, len(axes)):
#     axes[idx].axis('off')

# plt.tight_layout()
# plt.show()

# -----------------------------
# Solver availability check
# -----------------------------
solver = po.SolverFactory(args.solverName)

if solver.available():
    print("Solver", args.solverName, "is available.")
else:
    print("Solver", args.solverName, "is NOT available.")
    sys.exit(1)


# -----------------------------
# Solve
# -----------------------------
begin = time.time()

if args.version == 1:
    if args.print:
        print("Considering version 1 of the problem")
    solution = runMILPModelForVersion1(
        data, args.print, args.timeLimit, args.solverName
    )

elif args.version == 2_1:
    if args.print:
        print("Considering version 2 of the problem")
    solution = runMILPModelForVersion2_1(
        data, args.print, args.timeLimit, args.solverName
    )

elif args.version == 2_2:
    if args.print:
        print("Considering version 2 of the problem")
    solution = runMILPModelForVersion2_2(
        data, args.print, args.timeLimit, args.solverName
    )


elif args.version == 3:
    if args.print:
        print("Considering version 3 of the problem")
    solution = runMILPModelForVersion3(
        data, args.print, args.timeLimit, args.solverName
    )

else:
    print("Unknown version of the problem")
    sys.exit(1)

end = time.time()

# -----------------------------
# Prepare solution dict for downstream functions expecting a mapping
# -----------------------------
solution_dict = vars(solution) if solution is not None else None

# -----------------------------
# Output
# -----------------------------
print("\ndataFileName =", dataFileName)
print("solutionValue =", solution.value())
print("cpuTime =", end - begin)

# -----------------------------
# Draw Distribution
# -----------------------------
# drawDistribution(data)

# -----------------------------
# Draw Solution
# -----------------------------
# if solution is not None:
#     drawSolution(data, solution, model_version=str(args.version))
# else:
#     print("No solution found")

# -----------------------------
# Save data to file
# -----------------------------
# if solution is not None and solution_dict is not None:
#     solution.recordSolution(data, str(args.version), solution_dict, dataFileName)
# else:
#     print("No solution found; nothing saved.")

if solution is not None:
    # Check the solution
    isFeasible = checkSolution(data, solution, args.version, args.print)
    print("isFeasible =", isFeasible)

    # Write the solution to the file
    path_separator = '\\' if platform.system() == 'Windows' else '/'
    solutionFilePath = dataFileName + "_V" + str(args.version) + "_Z" + str(args.nbZones) + ".sol"
    # solutionFilePath = dataFileName + ".sol"
    if args.solutionFolderPath != "":
        solutionFilePath = args.solutionFolderPath + path_separator + solutionFilePath
    print("Solution is written in the following file: ", solutionFilePath)
    recordSolution(data, solution, solutionFilePath)
else:
    print("isFeasible =", False)

# print("\nRESULT;", dataFileName, ";", solution.value(), ";", isFeasible, ";", end - begin)
sys.exit(0)
