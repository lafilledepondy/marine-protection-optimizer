import os

class Solution: # MarineAreasProtectionSolution
    def __init__(self, sectors, obj_value, solve_time, status):
        self.sectors = sectors
        self.obj_value = obj_value
        self.solve_time = solve_time
        self.status = status
    
    def value(self):
        return self.obj_value
    
    # def recordSolution(self, data, model, solution, solutionFileName):
    #     solutionFileName = solutionFileName + "_V" + model
    #     print("Saving solution to file ", solutionFileName)

    #     nrows, ncols = data.height(), data.width()

    #     solutions_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Solutions')
    #     os.makedirs(solutions_dir, exist_ok=True)
        
    #     full_path = os.path.join(solutions_dir, solutionFileName)
        
    #     outfile = open(full_path, 'w')

    #     if model == "1":
    #         sectorsStr = ""
    #         outfile.write(data.nbSpecies().__str__() + "\n" + "1\n")
    #         for i in range(nrows):
    #             for j in range(ncols):
    #                 if data.isLand(i * ncols + j):
    #                     pass                
    #                 else:
    #                     if (i, j) in solution['sectors'] :
    #                         secId = i * ncols + j
    #                         sectorsStr += secId.__str__() + ";"
    #         outfile.write(sectorsStr.rstrip(';') + "\n")

    #     elif model == "2_1" or model == "2_2":
    #         outfile.write(data.nbSpecies().__str__() + "\n")
    #         outfile.write(str(len(solution['zones'])) + "\n")
            
    #         for zone_sectors in solution['zones']:
    #             sectorsStr = ""
    #             for (i, j) in zone_sectors:
    #                 secId = i * ncols + j
    #                 sectorsStr += secId.__str__() + ";"
    #             outfile.write(sectorsStr.rstrip(';') + "\n")

    #     elif solution.status == "infeasible":
    #         outfile.write("-1\n0\n")

    #     outfile.close()

def recordSolution(data, solution, solutionFilePath):
    """
    Write solution to file following ProjetOptim format
    """
    with open(solutionFilePath, 'w') as outfile:
        # Cas infaisable
        if solution.obj_value == -1 or solution.obj_value < 0:
            outfile.write("-1\n")  
            outfile.write("0\n")
        return 

        # solution.sectors can be:
        # - list of sector ids (version 1)
        # - dict: zone_id -> list of sector ids (version 2/3)

        nrows, ncols = data.height(), data.width()

        # ---------- VERSION 1 ----------
        if isinstance(solution.sectors, list):
            # solution.sectors = list of (i, j)
            sectorsStr = ""

            for i in range(nrows):
                for j in range(ncols):
                    secId = i * ncols + j
                    if data.isLand(secId):
                        continue
                    if (i, j) in solution.sectors:
                        sectorsStr += str(secId) + ";"

            sectorsStr = sectorsStr.rstrip(";")

            outfile.write(str(len(sectorsStr.split(";"))) + "\n")
            outfile.write("1\n")
            outfile.write(sectorsStr + "\n")

        elif isinstance(solution.sectors, dict):
            # Version 2 / 3: multiple zones
            total_sectors = sum(len(v) for v in solution.sectors.values())
            outfile.write(str(total_sectors) + "\n")
            outfile.write(str(len(solution.sectors)) + "\n")

            for zone_id in sorted(solution.sectors.keys()):
                outfile.write(";".join(map(str, solution.sectors[zone_id])) + "\n")

                