
import numpy as np
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt


grid_V1 = [[1, 1, 1, 1, 1, 0],
           [1, 1, 1, 0, 0, 0],
           [0, 0, 0, 0, -1, 0],
           [0, 0, 0, 0, 0, 0],
           [-1, 0, -1, 1, 0, 0],
           [0, 0, 0, 0, 0, 0]]

grid_V2 = [[1, 1, 1, 1, 1, 0],
           [1, 1, 1, 0, 0, 0],
           [0, 0, 0, 0, -1, 0],
           [0, 0, 0, 0, 0, 0],
           [-1, -1, -1, 1, 0, 0],
           [-1, -1, -1, 0, 0, 0]]

grid_V3 = [[1, 1, 1, 1, 1, 0],
           [1, 1, 1, 0, 0, 0],
           [0, 0, 0, 0, -1, -1],
           [-1, -1, 0, 0, 0, -1],
           [0, -1, -1, 1, 0, -1],
           [0, -1, -1, 0, 0, 0]]

grid = [[1, 1, 1, 1, 1, 0],
           [1, 1, 1, 0, 0, 0],
           [0, 0, 0, 0, 0, 0],
           [0, 0, 0, 0, 0, 0],
           [0, 0, 0, 1, 0, 0],
           [0, 0, 0, 0, 0, 0]]

def showGrid(grid):
    image = np.array(grid)
    nrows, ncols = image.shape

    cmap = mcolors.ListedColormap(['green', 'white', 'black'])
    norm = mcolors.BoundaryNorm([-1.5, -0.5, 0.5, 1.5], cmap.N)

    fig, ax = plt.subplots(figsize=(ncols, nrows))
    ax.matshow(image, cmap=cmap, norm=norm)
    ax.set_xticks(range(ncols))
    ax.set_yticks(range(nrows))
    plt.show()


showGrid(grid)