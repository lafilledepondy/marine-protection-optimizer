import sys
import csv
import os
import numpy as np
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt

class Species:
    def __init__(self, name, nbToProtect):
        self._name = name
        self._nbToProtect = nbToProtect

    def name(self):
        return self._name

    def nbToProtect(self):
        return self._nbToProtect


class Sector:
    def __init__(self, x, y, land=False):
        self._x = x
        self._y = y
        self._land = land
        self._population = []

    def __repr__(self):
        return '(' + str(self._x) + ',' + str(self._y) + ')'

    def addPopulation(self, population):
        self._population = population

    def populationForThisSpecies(self, species):
        if self._land:
            return 0
        else:
            return self._population[species]

    def population(self):
        return self._population

    def isLand(self):
        return self._land

    def x_coordinate(self):
        return self._x

    def y_coordinate(self):
        return self._y


class MarineAreasProtectionData:

    def __init__(self, name):
        self._name = name
        self._nbZonesMax = 0
        self._nbSectors = 0
        self._width = 0
        self._height = 0
        self._species = []
        self._grid = []

    def setGridDimensions(self, nbX, nbY):
        self._height = nbX
        self._width = nbY
        self._nbSectors = nbX * nbY

    def name(self):
        return self._name

    def height(self):
        return self._height

    def width(self):
        return self._width

    def addOneSpecies(self, oneSpecies):
        self._species.append(oneSpecies)

    def species(self):
        return self._species

    def nbSpecies(self):
        return len(self._species)

    def addSector(self, sector):
        self._grid.append(sector)

    def sectors(self):
        return self._grid

    def nbSectors(self):
        return self._nbSectors

    def isLand(self, sector):
        return self._grid[sector].isLand()

    def coordinates(self, sector):
        return self._grid[sector].x_coordinate(), self._grid[sector].y_coordinate()

    def addPopulationToSector(self, species, sector, value):
        if not self.isLand(sector):
            self._grid[sector]._population[species] += value

    def initEmptyPopulations(self, nbSpecies):
        for sect in self._grid:
            if not sect.isLand():
                sect.addPopulation([0] * nbSpecies)

    def population(self, species, sector):
        return self._grid[sector].populationForThisSpecies(species)

    def nbToProtect(self, oneSpecies):
        return self._species[oneSpecies].nbToProtect()

    def printSpecies(self):
        for species in self._species:
            print(species._name, species._nbToProtect)

    def printSectors(self):
        for sect in self._grid:
            if sect._land:
                print(sect)
            else:
                print(sect, sect.population())

    def setNbZonesMax(self, nbZonesMax):
        self._nbZonesMax = nbZonesMax

    def nbZonesMax(self):
        return self._nbZonesMax

def ens_R(data):
    H, W = data.height(), data.width()
    
    grid = []
    for i in range(H):
        row = []
        for j in range(W):
            idSector = i * W + j
            row.append(1 if data.isLand(idSector) else 0)
        grid.append(row)
    
    R = []  
    
    for x1 in range(H):
        for y1 in range(W):
            if grid[x1][y1] == 1:  # skip land
                continue

            for x2 in range(x1, H):
                for y2 in range(y1, W):
                    valid = True
                    for i in range(x1, x2+1):
                        for j in range(y1, y2+1):
                            if grid[i][j] == 1:
                                valid = False
                                break
                        if not valid:
                            break
                    if valid:
                        R.append(((x1,y1),(x2,y2)))
    return R

def ens_R_incomp(R):
    cell_sets = []
    for (x1, y1), (x2, y2) in R:
        cells = set(
            (i, j)
            for i in range(x1, x2 + 1)
            for j in range(y1, y2 + 1)
        )
        cell_sets.append(cells)

    n = len(R)
    R_incompatibles = [[] for _ in range(n)]

    for i in range(n):
        for j in range(i + 1, n):
            incompatible = False

            A = cell_sets[i]
            B = cell_sets[j]

            # 1) Overlap / inclusion (shared cell)
            if A & B:
                incompatible = True
            else:
                # 2) Edge adjacency
                for (x, y) in A:
                    if ((x+1, y) in B or (x-1, y) in B or
                        (x, y+1) in B or (x, y-1) in B):
                        incompatible = True
                        break

            if incompatible:
                R_incompatibles[i].append(j)
                R_incompatibles[j].append(i)

    return R_incompatibles

def drawGrid(data):
    nrows, ncols = data.height(), data.width()

    grid = []
    for i in range(nrows):
        oneLine = []
        for j in range(ncols):
            if data.isLand(i * ncols + j):
                oneLine.append(2)
            else:
                oneLine.append(0)
        grid.append(oneLine)

    image = np.matrix(grid)

    row_labels = range(nrows)
    col_labels = range(ncols)
    cmap = mcolors.ListedColormap(['blue', 'green', 'black'])  # white for 0, blue for 1, green for 2
    plt.matshow(image, cmap=cmap)
    plt.xticks(range(ncols), col_labels)
    plt.yticks(range(nrows), row_labels)
    plt.show()

def drawDistribution(data):
    nrows, ncols = data.height(), data.width()
    nb_species = data.nbSpecies()
    maxValue = 0
    nb_rows = nb_species // 4 + (nb_species % 4 > 0)  # Calculate the number of rows needed
    for idSpecies in range(nb_species):
        for i in range(nrows):
            for j in range(ncols):
                idSector = i * ncols + j
                if not data.isLand(i * ncols + j):
                    value = data.population(idSpecies, idSector)
                    if value > maxValue:
                        maxValue = value
    fig, axs = plt.subplots(nb_rows, 4, figsize=(20, 5 * nb_rows))  # Create a grid of subplots
    plt.subplots_adjust(wspace=0.1, hspace=0.3)
    fig.suptitle("Data "+ data.name())  # Set the title of the figure

    # Flatten the axs array for standard iteration
    axs = axs.flatten()
    images = []
    cmap = mcolors.ListedColormap(['black', 'white'] + [plt.cm.YlOrRd(i) for i in np.linspace(0, 1,                                                                                 maxValue + 1)])  # brown for -1, Blues colormap for other values
    norm = mcolors.BoundaryNorm([-1.5, -0.5] + list(np.linspace(0, maxValue, maxValue + 1)), cmap.N)

    for s in range(data.nbSpecies()):
        img = drawDistributionSpecies(data, s, axs[s], cmap, norm)
        images.append(img)


    #plt.tight_layout()
    cbar = fig.colorbar(images[0], ax=axs[:nb_species], orientation='vertical', fraction=.1, cmap=cmap, norm=norm)
    # Hide unused subplots
    for s in range(nb_species, len(axs)):
        axs[s].axis('off')

    plt.show()

def drawDistributionSpecies(data, idSpecies, ax, cmap, norm):
    nrows, ncols = data.height(), data.width()

    grid = []
    maxValue = 0
    for i in range(nrows):
        oneLine = []
        for j in range(ncols):
            idSector = i * ncols + j
            if data.isLand(i * ncols + j):
                oneLine.append(-1)
            else:
                value = data.population(idSpecies, idSector)
                if value > maxValue:
                    maxValue = value
                oneLine.append(value)
        grid.append(oneLine)

    image = np.matrix(grid)

    img = ax.matshow(image, cmap=cmap, norm=norm)
    ax.set_title(f'{data.species()[idSpecies].name()} [{idSpecies}]')
    # ax.xticks(range(ncols), col_labels)
    # ax.yticks(range(nrows), row_labels)
    # ax.colorbar()
    # plt.show()


def printData(data):
    print("Nb species : ", data.nbSpecies())
    print("Grid (", data.height(), ",", data.width(), ")")
    data.printSectors()
    print("Species")
    data.printSpecies()


def readDataFromFile(dataFilePath):
    try:
        with open(dataFilePath, 'r') as dataFile:
            reader = csv.reader(dataFile, delimiter=";")
            dataFileName = os.path.splitext(os.path.basename(dataFilePath))[0]

            data = MarineAreasProtectionData(dataFileName)

            nbSpecies = int(next(reader)[0])
            print("Reading", nbSpecies, "species")
            for s in range(nbSpecies):
                line = next(reader)
                data.addOneSpecies(Species(line[0], int(line[1])))

            line = next(reader)
            nbX = int(line[0])
            nbY = int(line[1])
            data.setGridDimensions(nbX, nbY)

            nbCells = nbX * nbY
            for i in range(nbCells):
                line = next(reader)
                currX = int(line[0])
                currY = int(line[1])
                isLand = int(line[2])
                if isLand == 1:
                    sect = Sector(currX, currY, True)
                else:
                    sect = Sector(currX, currY, False)
                    count = []
                    for s in range(nbSpecies):
                        count.append(int(line[3 + s]))
                    sect.addPopulation(count)
                data.addSector(sect)

            return data
    except IOError as e:
        print("I/O error({0}): {1}".format(e.errno, e.strerror), file=sys.stderr)
        sys.exit(1)
    except ValueError:
        print("Could not convert data to an integer.", file=sys.stderr)
        sys.exit(1)
    except:
        print("Unexpected error:", sys.exc_info()[0], file=sys.stderr)
        sys.exit(1)


def saveDataToFile(data, dataFileName):
    print("Saving to file ", dataFileName)

    outfile = open(dataFileName, 'w')
    writer = csv.writer(outfile, delimiter=";")

    writer.writerow([data.nbSpecies()])

    for species in data.species():
        writer.writerow([species.name(), species.nbToProtect()])

    writer.writerow([data.height(), data.width()])

    for sector in data.zones():
        val = 1 if sector.isLand() else 0
        line = [sector.x_coordinate(), sector.y_coordinate(), val]
        for s in range(data.nbSpecies()):
            line.append(sector.populationForThisSpecies(s))
        writer.writerow(line)

    outfile.close()

def drawSolution_V1(data, solution):
    nrows, ncols = data.height(), data.width()

    grid = []
    for i in range(nrows):
        oneLine = []
        for j in range(ncols):
            idSector = i * ncols + j
            if data.isLand(i * ncols + j):
                oneLine.append(2)
            else:
                if (i, j) in solution.sectors:
                    print((i,j))
                    oneLine.append(1)
                else:
                    oneLine.append(0)
        grid.append(oneLine)

    image = np.matrix(grid)

    row_labels = range(nrows)
    col_labels = range(ncols)
    cmap = mcolors.ListedColormap(["#0073A6", "#ffffff", 'black'])  # blue for 0, green for 1, black for 2
    fig, ax = plt.subplots(figsize=(ncols, nrows))
    ax.matshow(image, cmap=cmap)
    ax.set_xticks(range(ncols))
    ax.set_xticklabels(col_labels)
    ax.set_yticks(range(nrows))
    ax.set_yticklabels(row_labels)
    ax.set_title("Solution – Version 1 (secteurs individuels)")
    plt.show()


def drawSolution_V2_1(data, solution):
    nrows, ncols = data.height(), data.width()

    # Création de la grille
    grid = []
    for i in range(nrows):
        oneLine = []
        for j in range(ncols):
            s = i * ncols + j
            if data.isLand(s):
                oneLine.append(2)  # Terre
            else:
                # Vérifier si le secteur est protégé dans une zone
                protected = False
                for sec_list in solution.sectors.values():
                    if s in sec_list:
                        protected = True
                        break
                oneLine.append(1 if protected else 0)
        grid.append(oneLine)

    # Transformation en matrice numpy
    image = np.array(grid)

    # Couleurs : 0=mer non protégée, 1=mer protégée, 2=terre
    cmap = mcolors.ListedColormap(['#0080ff', '#37474f', 'green']) # terre => vert; gris => sol ; blue => mer non protégée

    fig, ax = plt.subplots(figsize=(ncols, nrows))
    ax.matshow(image, cmap=cmap)
    ax.set_xticks(range(ncols))
    ax.set_yticks(range(nrows))
    ax.set_title("Solution – Version 2_1 (zones rectangulaires)")
    plt.show()

def drawSolution_V3(data, solution):
    nrows, ncols = data.height(), data.width()

    # grille initiale : 0 = mer non protégée
    grid = [[0 for _ in range(ncols)] for _ in range(nrows)]

    # terre = -1
    for s in range(nrows * ncols):
        if data.isLand(s):
            i, j = divmod(s, ncols)
            grid[i][j] = -1

    # zones protégées : 1, 2, 3, ...
    for zone_id, sec_list in solution.sectors.items():
        for s in sec_list:
            i, j = divmod(s, ncols)
            grid[i][j] = zone_id + 1  # +1 pour éviter le 0

    image = np.array(grid)

    # colormap with distinct colors for each zone
    # 0=mer non protégée (blue), 1+=zones (grey), -1=terre (green)
    nb_zones = len(solution.sectors)
    colors = ['green']  # land (-1)
    colors.append('#0080ff')  # unprotected sea (0)
    colors += ['#37474f'] * nb_zones  # zones in grey
    cmap = mcolors.ListedColormap(colors)
    
    # Map: -1 -> 0, 0 -> 1, 1 -> 2, ..., nb_zones -> nb_zones+1
    boundaries = np.arange(-1.5, nb_zones + 1.5, 1)
    norm = mcolors.BoundaryNorm(boundaries, cmap.N)

    fig, ax = plt.subplots(figsize=(ncols, nrows))
    ax.matshow(image, cmap=cmap, norm=norm)
    ax.set_xticks(range(ncols))
    ax.set_yticks(range(nrows))
    ax.set_title("Solution – Version 3 (zones connexes)")
    plt.show()   


def drawSolution(data, solution, model_version):
    if model_version == "1":
        drawSolution_V1(data, solution)
    elif model_version == "2_1" or model_version == "21" or model_version == "2_2" or model_version == "22":
        drawSolution_V2_1(data, solution)
    elif model_version == "3":
        drawSolution_V3(data, solution)
    else:
        print("Drawing not implemented for model version", model_version)


                