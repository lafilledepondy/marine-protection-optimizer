import time
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition
from solution import *
from data import ens_R, ens_R_incomp

################################################################
#######################  VERSION 1  ############################
################################################################

def runMILPModelForVersion1(data, toPrint, timeLimit, solverName):
    # ======= VARIABLES =======
    H = data.height()
    W = data.width()
    E = range(data.nbSpecies())

    model = pyo.ConcreteModel()
    model.x = pyo.Var([(i, j) for i in range(H) for j in range(W)], within=pyo.Binary)

    # ======= OBJECTIVE =======
    model.obj = pyo.Objective(
        expr=pyo.summation(model.x),
        sense=pyo.minimize
    )

    # ======= CONSTRAINTS =======
    model.constraints = pyo.ConstraintList()
    
    for i in range(H):
        for j in range(W):
            s = i * W + j
            if data.isLand(s):
                model.constraints.add(model.x[i, j] == 0)

    for e in E:
        model.constraints.add(
            sum(
                data.population(e, i * W + j) * model.x[i, j]
                for i in range(H) for j in range(W)
            ) >= data.nbToProtect(e)
        )

    # ======= MODEL =======
    solver = pyo.SolverFactory(solverName)
    
    # Réglage spécifique pour HiGHS (via appsi)
    if solverName == "appsi_highs":
        solver.options['time_limit'] = timeLimit
    else:
        solver.options['time_limit'] = timeLimit
    
    start_time = time.time()

    # tee=True est la CLÉ pour que le log contienne les bornes
    results = solver.solve(model, tee=True) 
    solve_time = time.time() - start_time

    status = results.solver.status
    
    # ===== EXTRACT SOLUTION =====
    sectors = []
    # On vérifie si une solution existe (Optimal ou Feasible)
    if status == SolverStatus.ok or status == SolverStatus.warning:
        for i in range(H):
            for j in range(W):
                try:
                    if pyo.value(model.x[i, j]) > 0.5:
                        sectors.append((i, j))
                except ValueError: # Au cas où la variable n'a pas de valeur
                    continue
        obj_value = pyo.value(model.obj)
    else:
        obj_value = -1

    # On retourne UNIQUEMENT les 4 arguments de votre classe
    return Solution(sectors, obj_value, solve_time, status)

################################################
################### VERSION 2 ##################
################################################

# ==============================================
# Version 2.1
# ==============================================
# def runMILPModelForVersion2_1(data, toPrint, timeLimit, solverName):
#    # ======= VARIABLES =======
#     H = data.height()
#     W = data.width()
#     E = range(data.nbSpecies())
#     R = ens_R(data)
#     R_incomp = ens_R_incomp(R)
#     R_len = len(R)

#     model = pyo.ConcreteModel()
#     model.x = pyo.Var([(i, j, k) for i in range(H) for j in range(W) for k in range(R_len)],within=pyo.Binary)
#     model.z = pyo.Var([r for r in range(R_len)], within=pyo.Binary)
  

#     # ======= OBJECTIVE =======
#     model.obj = pyo.Objective(
#         expr=pyo.summation(model.x),
#         sense=pyo.minimize
#     )

#     # ======= CONSTRAINTS =======  
#     model.constraints = pyo.ConstraintList()
#     for e in E:
#         model.constraints.add(
#             sum(
#                 data.population(e, i * W + j) * model.x[i, j, k]
#                 for i in range(H)
#                 for j in range(W)
#                 for k in range(R_len)
#             ) >= data.nbToProtect(e)
#         )
    
#     model.constraints.add(sum(model.z[r] for r in range(R_len)) <= data.nbZonesMax())

#     for i in range(R_len):
#         for j in R_incomp[i]:
#             if i < j:
#                 model.constraints.add(model.z[i] + model.z[j] <= 1)
    
#     for r in range(R_len):
#         for i in range(H):
#             for j in range(W):
#                 s = i * W + j
#                 if not data.isLand(s):
#                     model.constraints.add(model.x[i, j, r] <= model.z[r])
    
#     for i in range(H):
#         for j in range(W):
#             model.constraints.add(sum(model.x[i,j, k] for k in range(R_len)) <= 1)
    
#     # ======= MODEL =======
#     solver = pyo.SolverFactory(solverName)
#     if solver is None or not solver.available():
#         raise ValueError(f"Solver '{solverName}' is not available.")

#     solver.options['time_limit'] = timeLimit

#     if toPrint:
#         print("Solving Version 2.1 model with solver:", solverName)

#     start_time = time.time()
#     results = solver.solve(model, tee=toPrint)
#     solve_time = time.time() - start_time

#     status = results.solver.status

#     # ===== EXTRACT SOLUTION =====
#     sectors = {}   # dictionnaire : zone -> liste de secteurs

#     if status == SolverStatus.ok and results.solver.termination_condition == TerminationCondition.optimal:

#         for k in range(R_len):
#             if pyo.value(model.z[k]) > 0.5:
#                 sectors[k] = []
#                 for i in range(H):
#                     for j in range(W):
#                         if pyo.value(model.x[i, j, k]) > 0.5:
#                             sectors[k].append(i * W + j)

#         obj_value = pyo.value(model.obj)

#     else:
#         obj_value = -1
    
#     if toPrint:
#         print(f"Status: {status}")
#         print(f"Solve time: {solve_time:.2f}s")
#         print(f"Objective value: {obj_value}")

#         total_sectors = sum(len(v) for v in sectors.values())
#         print(f"Number of protected sectors: {total_sectors}")

#     for k, sec_list in sectors.items():
#         if sec_list:
#             print(";".join(str(s) for s in sec_list))
    
#     return Solution(sectors, obj_value, solve_time, status)



def runMILPModelForVersion2_1(data, toPrint, timeLimit, solverName):
    """
    Version 2.1 : protection par zones (max K zones), sans contrainte de forme rectangulaire
    """
    H = data.height()
    W = data.width()
    E = range(data.nbSpecies())

    #  Définir l'ensemble des zones
    R = list(range(data.nbZonesMax()))       
    R_incomp = []                             # pas d'incompatibilités pour le test

    #  Définir le modèle Pyomo
    model = pyo.ConcreteModel()
    model.x = pyo.Var([(i,j,k) for i in range(H) for j in range(W) for k in R], within=pyo.Binary)
    model.z = pyo.Var(R, within=pyo.Binary)

    # Objectif : minimiser le nombre total de secteurs protégés
    model.obj = pyo.Objective(expr=pyo.summation(model.x), sense=pyo.minimize)

    # Contraintes
    model.constraints = pyo.ConstraintList()

    # 4a. Couvrir le nombre minimal d'individus pour chaque espèce
    for e in E:
        model.constraints.add(
            sum(data.population(e,i*W+j) * model.x[i,j,k] for i in range(H) for j in range(W) for k in R) 
            >= data.nbToProtect(e)
        )

    # 4b. Limiter le nombre de zones utilisées
    model.constraints.add(sum(model.z[r] for r in R) <= data.nbZonesMax())

    # 4c. Chaque secteur ne peut appartenir qu'à une zone
    for i in range(H):
        for j in range(W):
            model.constraints.add(sum(model.x[i,j,k] for k in R) <= 1)

    # 4d. Un secteur ne peut être protégé que si la zone correspondante est utilisée
    for k in R:
        for i in range(H):
            for j in range(W):
                s = i*W + j
                if not data.isLand(s):
                    model.constraints.add(model.x[i,j,k] <= model.z[k])
                else:
                    # secteur terrestre, jamais protégé
                    model.constraints.add(model.x[i,j,k] == 0)

    # Résolution
    solver = pyo.SolverFactory(solverName)
    if solver is None or not solver.available():
        raise ValueError(f"Solver '{solverName}' non disponible")

    solver.options['time_limit'] = timeLimit
    if toPrint:
        print("Solving Version 2.1 with solver:", solverName)

    start_time = time.time()
    results = solver.solve(model, tee=toPrint)
    solve_time = time.time() - start_time
    status = results.solver.status

    # 6️⃣ Extraction de la solution
    sectors = {}
    if status == SolverStatus.ok and results.solver.termination_condition == TerminationCondition.optimal:
        for k in R:
            if pyo.value(model.z[k]) > 0.5:
                sectors[k] = []
                for i in range(H):
                    for j in range(W):
                        if pyo.value(model.x[i,j,k]) > 0.5:
                            sectors[k].append(i*W + j)
        obj_value = pyo.value(model.obj)
    else:
        obj_value = -1

    # Affichage 
    if toPrint:
        print(f"Status: {status}")
        print(f"Solve time: {solve_time:.2f}s")
        print(f"Objective value: {obj_value}")
        total_sectors = sum(len(v) for v in sectors.values())
        print(f"Number of protected sectors: {total_sectors}")
        for k, sec_list in sectors.items():
            if sec_list:
                coords = [(s//W, s%W) for s in sec_list]
                print(f"Zone {k}: {coords}")

    return Solution(sectors, obj_value, solve_time, status)

# ==============================================
# Version 2.2
# ==============================================
def runMILPModelForVersion2_2(data, toPrint, timeLimit, solverName):
 
    # ======= ENSEMBLES =======
    H = data.height()
    W = data.width()
    S = range(H * W)  
    E = range(data.nbSpecies())  
    K_max = data.nbZonesMax()
    K = range(K_max)  
    
    # T: ensemble des secteurs terrestres
    T = set(s for s in S if data.isLand(s))
    
    # V(s): ensemble des voisins du secteur s (4-connectivité)
    def get_neighbors(s):
        """Retourne les voisins (4-connectivité) du secteur s"""
        i = s // W  # ligne
        j = s % W   # colonne
        neighbors = []
        if i > 0:
            neighbors.append((i - 1) * W + j)  # Haut
        if i < H - 1:
            neighbors.append((i + 1) * W + j)  # Bas
        if j > 0:
            neighbors.append(i * W + (j - 1))  # Gauche
        if j < W - 1:
            neighbors.append(i * W + (j + 1))  # Droite
        return neighbors
    
    V = {s: get_neighbors(s) for s in S}
    
    # Fonction pour obtenir les coordonnées (i, j) d'un secteur s
    def coords(s):
        return (s // W, s % W)
    
    # ======= MODÈLE =======
    model = pyo.ConcreteModel()
    
    # ======= VARIABLES DE DÉCISION =======
    
    # r^k : 1 si le rectangle k est utilisé (1.28)
    model.r = pyo.Var(K, within=pyo.Binary)
    
    # z_s^k : 1 si le secteur s appartient au rectangle k (1.28)
    model.z = pyo.Var([(s, k) for s in S for k in K], within=pyo.Binary)
    
    # x_1^k, y_1^k : coin supérieur gauche du rectangle k (1.29)
    model.x1 = pyo.Var(K, within=pyo.NonNegativeIntegers, bounds=(0, H - 1))
    model.y1 = pyo.Var(K, within=pyo.NonNegativeIntegers, bounds=(0, W - 1))
    
    # x_2^k, y_2^k : coin inférieur droit du rectangle k (1.29)
    model.x2 = pyo.Var(K, within=pyo.NonNegativeIntegers, bounds=(0, H - 1))
    model.y2 = pyo.Var(K, within=pyo.NonNegativeIntegers, bounds=(0, W - 1))
    
    # ======= OBJECTIF (1.13) =======
    # Minimiser le nombre total de secteurs protégés
    model.obj = pyo.Objective(
        expr=sum(model.z[s, k] for k in K for s in S),
        sense=pyo.minimize
    )
    
    # ======= CONTRAINTES =======
    model.constraints = pyo.ConstraintList()
    
    # (1.14) Protection minimale de chaque espèce
    # sum_{k in K} sum_{s in S} η_es * z_s^k >= p_e pour chaque espèce e
    for e in E:
        model.constraints.add(
            sum(
                data.population(e, s) * model.z[s, k]
                for k in K
                for s in S
            ) >= data.nbToProtect(e)
        )
    
    # (1.15) Nombre max de rectangles utilisés <= K_max
    model.constraints.add(
        sum(model.r[k] for k in K) <= K_max
    )
    
    # (1.16) x_1^k <= x_2^k : cohérence des coordonnées ligne
    for k in K:
        model.constraints.add(model.x1[k] <= model.x2[k])
    
    # (1.17) y_1^k <= y_2^k : cohérence des coordonnées colonne
    for k in K:
        model.constraints.add(model.y1[k] <= model.y2[k])
    
    # (1.18) x_2^k - x_1^k + 1 <= H * r^k : active le rectangle si utilisé (lignes)
    for k in K:
        model.constraints.add(model.x2[k] - model.x1[k] + 1 <= H * model.r[k])
    
    # (1.19) y_2^k - y_1^k + 1 <= W * r^k : active le rectangle si utilisé (colonnes)
    for k in K:
        model.constraints.add(model.y2[k] - model.y1[k] + 1 <= W * model.r[k])
    
    # (1.20) z_s^k <= r^k : un secteur ne peut appartenir qu'à un rectangle utilisé
    for s in S:
        for k in K:
            model.constraints.add(model.z[s, k] <= model.r[k])
    
    # (1.21) x_1^k - i <= (1 - z_s^k) * H : si z_s^k = 1, alors x_1^k <= i
    for s in S:
        i, j = coords(s)
        for k in K:
            model.constraints.add(model.x1[k] - i <= (1 - model.z[s, k]) * H)
    
    # (1.22) i - x_2^k <= (1 - z_s^k) * H : si z_s^k = 1, alors i <= x_2^k
    for s in S:
        i, j = coords(s)
        for k in K:
            model.constraints.add(i - model.x2[k] <= (1 - model.z[s, k]) * H)
    
    # (1.23) y_1^k - j <= (1 - z_s^k) * W : si z_s^k = 1, alors y_1^k <= j
    for s in S:
        i, j = coords(s)
        for k in K:
            model.constraints.add(model.y1[k] - j <= (1 - model.z[s, k]) * W)
    
    # (1.24) j - y_2^k <= (1 - z_s^k) * W : si z_s^k = 1, alors j <= y_2^k
    for s in S:
        i, j = coords(s)
        for k in K:
            model.constraints.add(j - model.y2[k] <= (1 - model.z[s, k]) * W)
    
    # (1.25) sum_{k in K} z_s^k <= 1 : chaque secteur appartient à au plus un rectangle
    for s in S:
        model.constraints.add(sum(model.z[s, k] for k in K) <= 1)
    
    # (1.26) z_s^k = 0 pour s in T : interdiction de protéger les secteurs terrestres
    for s in T:
        for k in K:
            model.constraints.add(model.z[s, k] == 0)
    
    # (1.27) z_{s1}^{k1} + z_{s2}^{k2} <= 1 pour k1 < k2, s2 in V(s1)
    # Deux rectangles différents ne peuvent pas avoir de secteurs adjacents
    for s1 in S:
        for s2 in V[s1]:
            if s1 < s2:  # Pour éviter les doublons
                for k1 in K:
                    for k2 in K:
                        if k1 < k2:
                            model.constraints.add(
                                model.z[s1, k1] + model.z[s2, k2] <= 1
                            )
                            model.constraints.add(
                                model.z[s1, k2] + model.z[s2, k1] <= 1
                            )
    
    # utilisation des rectangles dans l'ordre
    for k in range(K_max - 1):
        model.constraints.add(model.r[k + 1] <= model.r[k])
    
    # ======= RÉSOLUTION =======
    solver = pyo.SolverFactory(solverName)
    if solver is None or not solver.available():
        raise ValueError(f"Solver '{solverName}' is not available.")
    
    # Configuration du time limit selon le solveur
    if 'highs' in solverName.lower() or 'appsi_highs' in solverName:
        solver.options['time_limit'] = float(timeLimit)
    elif 'gurobi' in solverName.lower():
        solver.options['TimeLimit'] = timeLimit
    elif 'cbc' in solverName.lower():
        solver.options['seconds'] = timeLimit
    else:
        solver.options['time_limit'] = timeLimit
    
    if toPrint:
        print("=" * 60)
        print("Solving Version 2.2 (Rectangle formulation) with solver:", solverName)
        print(f"  - Grid: {H} x {W} = {H*W} sectors")
        print(f"  - Species: {len(E)}")
        print(f"  - Max rectangles: {K_max}")
        print(f"  - Land sectors: {len(T)}")
        print("=" * 60)
    
    start_time = time.time()
    
    # Résolution avec gestion des erreurs
    try:
        if 'highs' in solverName.lower() or 'appsi_highs' in solverName:
            results = solver.solve(model, tee=toPrint, load_solutions=False)
        else:
            results = solver.solve(model, tee=toPrint)
    except Exception as e:
        if toPrint:
            print(f"Solver error: {e}")
        return Solution({}, -1, time.time() - start_time, "error")
    
    solve_time = time.time() - start_time
    
    status = results.solver.status
    termination = results.solver.termination_condition
    
    # ======= EXTRACTION DE LA SOLUTION =======
    sectors = {}
    
    if status == SolverStatus.ok and termination == TerminationCondition.optimal:
        # Charger la solution manuellement pour HiGHS
        if 'highs' in solverName.lower() or 'appsi_highs' in solverName:
            model.solutions.load_from(results)
        
        for k in K:
            if pyo.value(model.r[k]) > 0.5:
                sectors[k] = []
                x1_val = int(round(pyo.value(model.x1[k])))
                y1_val = int(round(pyo.value(model.y1[k])))
                x2_val = int(round(pyo.value(model.x2[k])))
                y2_val = int(round(pyo.value(model.y2[k])))
                
                for s in S:
                    if pyo.value(model.z[s, k]) > 0.5:
                        sectors[k].append(s)
                
                if toPrint:
                    print(f"Rectangle {k}: coin sup-gauche=({x1_val},{y1_val}), "
                          f"coin inf-droit=({x2_val},{y2_val}), "
                          f"{len(sectors[k])} secteurs")
        
        obj_value = int(pyo.value(model.obj))
        
        if toPrint:
            print(f"\nSolution found!")
            print(f"Objective value (total sectors): {obj_value}")
            print(f"Number of rectangles used: {len(sectors)}")
            total_protected = sum(len(v) for v in sectors.values())
            print(f"Total protected sectors: {total_protected}")
    
    elif termination == TerminationCondition.infeasible:
        obj_value = -1
        if toPrint:
            print("Problem is INFEASIBLE")
    
    else:
        obj_value = -1
        if toPrint:
            print(f"No optimal solution. Status: {status}, Termination: {termination}")
    
    return Solution(sectors, obj_value, solve_time, status)

################################################
################### VERSION 3 ##################
################################################

def runMILPModelForVersion3(data, toPrint, timeLimit, solverName):
    # ======= ENSEMBLES =======
    H = data.height()
    W = data.width()
    S = range(H * W)  # Ensemble des secteurs
    E = range(data.nbSpecies())  # Ensemble des espèces
    K_max = data.nbZonesMax()
    K = range(K_max)  # Ensemble des zones connexes {0, 1, ..., K_max-1}
    
    # T: ensemble des secteurs terrestres
    T = [s for s in S if data.isLand(s)]
    
    # V(s): ensemble des voisins du secteur s (secteurs partageant une arête)
    def get_neighbors(s):
        """Retourne les voisins (4-connectivité) du secteur s"""
        x = s // W  # ligne
        y = s % W   # colonne
        neighbors = []
        # Haut
        if x > 0:
            neighbors.append((x - 1) * W + y)
        # Bas
        if x < H - 1:
            neighbors.append((x + 1) * W + y)
        # Gauche
        if y > 0:
            neighbors.append(x * W + (y - 1))
        # Droite
        if y < W - 1:
            neighbors.append(x * W + (y + 1))
        return neighbors
    
    V = {s: get_neighbors(s) for s in S}
    
    # ======= MODÈLE =======
    model = pyo.ConcreteModel()
    
    # ======= VARIABLES DE DÉCISION =======
    # z[s,k]: 1 si le secteur s appartient à la zone k
    model.z = pyo.Var([(s, k) for s in S for k in K], within=pyo.Binary)
    
    # y[k]: 1 si la zone k est utilisée
    model.y = pyo.Var([k for k in K], within=pyo.Binary)
    
    # r[s,k]: 1 si s est la racine de la zone k
    model.r = pyo.Var([(s, k) for s in S for k in K], within=pyo.Binary)
    
    # f[s,v,k]: flux de s vers v dans la zone k 
    model.f = pyo.Var(
        [(s, v, k) for s in S for v in V.get(s, []) for k in K],
        within=pyo.NonNegativeReals,
        bounds=(0, len(S))
    )
    
    # ======= OBJECTIF (1.30) =======
    # Minimiser le nombre total de secteurs protégés
    model.obj = pyo.Objective(
        expr=sum(model.z[s, k] for s in S for k in K),
        sense=pyo.minimize
    )
    
    # ======= CONTRAINTES =======
    model.constraints = pyo.ConstraintList()
    
    # (1.31) Protection minimale de chaque espèce
    # sum_{k in K} sum_{s in S} η_es * z_s^k >= p_e pour chaque espèce e
    for e in E:
        model.constraints.add(
            sum(
                data.population(e, s) * model.z[s, k]
                for s in S
                for k in K
            ) >= data.nbToProtect(e)
        )
    
    # (1.32) Nombre max de zones connexes utilisées <= K_max
    model.constraints.add(
        sum(model.y[k] for k in K) <= K_max
    )
    
    # (1.33) Un secteur appartient à au plus une zone
    # sum_{k in K} z_s^k <= 1 pour chaque secteur s
    for s in S:
        model.constraints.add(
            sum(model.z[s, k] for k in K) <= 1
        )
    
    # (1.34) Un secteur ne peut appartenir qu'à une zone utilisée
    # z_s^k <= y^k pour chaque s, k
    for s in S:
        for k in K:
            model.constraints.add(
                model.z[s, k] <= model.y[k]
            )
    
    # (1.35) Interdiction de protéger les secteurs terrestres
    # z_s^k = 0 pour s in T, pour tout k
    for s in T:
        for k in K:
            model.constraints.add(
                model.z[s, k] == 0
            )
    
    # (1.36) Contrainte de séparation des zones (assure que zones différentes non adjacentes)
    # z_s^{k1} + z_v^{k2} <= 1 pour k1 != k2, pour tout s, pour tout v in V(s)
    # Deux zones différentes ne peuvent pas avoir de secteurs adjacents
    for s in S:
        for v in V[s]:
            if s < v:  # Pour éviter les doublons (s,v) et (v,s)
                for k1 in K:
                    for k2 in K:
                        if k1 != k2:
                            model.constraints.add(
                                model.z[s, k1] + model.z[v, k2] <= 1
                            )
    
    # (1.37) Brisure de symétrie: y^{k+1} <= y^k
    # Force l'utilisation séquentielle des zones
    for k in range(K_max - 1):
        model.constraints.add(
            model.y[k + 1] <= model.y[k]
        )
    
    # ========== NOUVELLES CONTRAINTES DE CONNEXITÉ (C1-C5) ==========
    
    # (C1) Une seule racine par zone utilisée
    # sum_{s in S} r_s^k = y^k pour chaque zone k
    for k in K:
        model.constraints.add(
            sum(model.r[s, k] for s in S) == model.y[k]
        )
    
    # (C2) La racine doit appartenir à la zone
    # r_s^k <= z_s^k pour chaque s, k
    for s in S:
        for k in K:
            model.constraints.add(
                model.r[s, k] <= model.z[s, k]
            )
    
    # (C3) Conservation du flux
    # Pour chaque secteur s non-racine dans une zone k:
    # flux entrant = flux sortant + 1
    # Pour la racine: flux entrant = flux sortant
    for s in S:
        if s in T:  # Skip land sectors
            continue
        for k in K:
            # Flux entrant dans s
            flux_in = sum(
                model.f[v, s, k] 
                for v in S if s in V.get(v, [])
            )
            
            # Flux sortant de s
            flux_out = sum(
                model.f[s, v, k] 
                for v in V.get(s, [])
            )
            
            # Conservation: flux_in = flux_out + z[s,k] - r[s,k]
            model.constraints.add(
                flux_in == flux_out + model.z[s, k] - model.r[s, k]
            )
    
    # (C4a) et (C4b) Le flux ne peut circuler qu'entre secteurs de la même zone
    # f[s,v,k] <= |S| * z[s,k] et f[s,v,k] <= |S| * z[v,k]
    for s in S:
        for v in V.get(s, []):
            for k in K:
                model.constraints.add(
                    model.f[s, v, k] <= len(S) * model.z[s, k]
                )
                model.constraints.add(
                    model.f[s, v, k] <= len(S) * model.z[v, k]
                )
    
    # (C5) est implicite: f >= 0 par définition de la variable
    
    # ======= RÉSOLUTION =======
    solver = pyo.SolverFactory(solverName)
    if solver is None or not solver.available():
        raise ValueError(f"Solver '{solverName}' is not available.")
    
    if 'highs' in solverName.lower() or 'appsi_highs' in solverName:
        solver.options['time_limit'] = float(timeLimit)
    elif 'gurobi' in solverName.lower():
        solver.options['TimeLimit'] = timeLimit
    elif 'cbc' in solverName.lower():
        solver.options['seconds'] = timeLimit
    
    if toPrint:
        print("Solving Version 3 (flow model) with solver:", solverName)
        print(f"  - Grid: {H} x {W} = {H*W} sectors")
        print(f"  - Species: {len(E)}")
        print(f"  - Max zones: {K_max}") 
        print(f"  - Land sectors: {len(T)}")
    
    start_time = time.time()
    
    # ===== GESTION DES ERREURS =====
    try:
        if 'highs' in solverName.lower() or 'appsi_highs' in solverName:
            results = solver.solve(model, tee=toPrint, load_solutions=False)
        else:
            results = solver.solve(model, tee=toPrint)
    except Exception as e:
        if toPrint:
            print(f"Solver error: {e}")
        return Solution({}, -1, time.time() - start_time, "error")
    
    solve_time = time.time() - start_time
    
    status = results.solver.status
    termination = results.solver.termination_condition
    
    # ======= EXTRACTION DE LA SOLUTION =======
    sectors = {}
    
    if status == SolverStatus.ok and termination == TerminationCondition.optimal:
        # Charger la solution manuellement pour HiGHS
        if 'highs' in solverName.lower() or 'appsi_highs' in solverName:
            model.solutions.load_from(results)
        
        for k in K:
            if pyo.value(model.y[k]) > 0.5:  
                sectors[k] = []
                for s in S:
                    if pyo.value(model.z[s, k]) > 0.5:
                        sectors[k].append(s)
        
        obj_value = int(pyo.value(model.obj))
        
        if toPrint:
            print(f"\nSolution found!")
            print(f"Objective value: {obj_value}")
            print(f"Number of zones used: {len(sectors)}")
            for k, sec_list in sectors.items():
                coords = [(s // W, s % W) for s in sec_list]
                print(f"  Zone {k}: sectors {sec_list} = coords {coords}")
    
    elif termination == TerminationCondition.infeasible:
        obj_value = -1
        if toPrint:
            print("Problem is INFEASIBLE")
    
    else:
        obj_value = -1
        if toPrint:
            print(f"No optimal solution. Status: {status}, Termination: {termination}")
    
    from solution import Solution
    return Solution(sectors, obj_value, solve_time, status)

