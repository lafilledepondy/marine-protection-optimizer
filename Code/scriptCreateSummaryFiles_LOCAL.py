from projectUtils import *

# Create the parser
parser = argparse.ArgumentParser(description="Process command line arguments.")

# Add the arguments
parser.add_argument("-l", "--logFolderPath", type=valid_folder, required=True, help="The path to the log folder.")

# Parse the arguments
args = parser.parse_args()
print("----------- ARGUMENTS -----------")
print("Log folder path:", args.logFolderPath)
print("------------------------------------")

# Define the list of keys to search for
keys = ['dataFileName', 'Problem version', 'Number of zones', 'solutionValue', 'isFeasible', 'solutionStatus', 'dualBound', 'cpuTime']
keyValueDelimiter = [' = ', '=', ' : ', ':']

# Combine all log files into a single CSV summary
summaryFilePath = os.path.join(args.logFolderPath,'result_summary.csv')
summaryFile = open(summaryFilePath, 'w')
for logFile in os.listdir(args.logFolderPath):
    if logFile.endswith('.log'):
        log_path = os.path.join(args.logFolderPath, logFile)
        values = {key: "missing" for key in keys}
        with open(log_path, 'r') as f:
            for line in f:
                for key in keys:
                    for delimiter in keyValueDelimiter:
                        if key + delimiter in line:
                            parts = line.strip().split(delimiter)
                            if len(parts) == 2:
                                _, value = parts
                                values[key] = value
                                break
                    else:
                        continue
                    break
        summaryFile.write(f'{logFile};{";".join(values.values())}\n')
summaryFile.close()

# Check if the file is empty and remove it if it is
if os.stat(summaryFilePath).st_size == 0:
    os.remove(summaryFilePath)
    print("No summary file created because no log files were found")
else:
    print("Summary of the experiments written in the following file:", summaryFilePath)