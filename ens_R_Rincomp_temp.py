# grid = [
#     [1,1,0,0],
#     [0,0,0,1],
#     [0,1,0,0],
#     [0,0,0,0]
# ]

grid = [ 
    [1, 0],
    [0, 0]
]

def ens_R (grid):
    H, W = len(grid), len(grid[0])
    R = []  
    
    for x1 in range(H):
        for y1 in range(W):
            if grid[x1][y1] == 1:  # skip terres
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
    # Precompute cell sets for each rectangle
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

def render_grid(grid):
    H, W = len(grid), len(grid[0])
    header = "    " + " ".join(f"{c:2d}" for c in range(W))
    lines = [header]
    for r in range(H):
        row = []
        for c in range(W):
            cell = "#" if grid[r][c] == 1 else "."
            row.append(f"{cell:2}")
        lines.append(f"{r:2d}  " + " ".join(row))
    return "\n".join(lines)

def main():                        
    R = ens_R(grid)
    R_incompatibles = ens_R_incomp(R)
    print("Grille (# = terre, . = eau):")
    print(render_grid(grid))
    print()
    print("Ensembles de zones possibles R:")
    for idx, zone in enumerate(R):
        print(f"Zone {idx}: {zone}")
    print("\nEnsembles de zones incompatibles:")
    for idx, incompatibles in enumerate(R_incompatibles):
        print(f"Zone {idx} incompatible avec zones: {incompatibles}")

if __name__ == "__main__":
    main()