import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
import glob
from itertools import cycle


def plot_optimal_instances_correct(csv_paths):

    data_sets = []
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    def expand_paths(paths):
        expanded = []
        for raw in paths:
            if not raw:
                continue

            pattern = raw if os.path.isabs(raw) else os.path.join(base_dir, raw)
            matches = glob.glob(pattern)
            if not matches:
                print("Aucun fichier correspondant :", raw)
                continue
            expanded.extend(matches)
        return expanded

    def label_from_path(file_path):
        norm_path = os.path.normpath(file_path)
        parent = os.path.dirname(os.path.dirname(norm_path))
        label = os.path.basename(parent) if parent else os.path.basename(norm_path)
        return label or os.path.basename(norm_path)

    fallback_cols = [
        'logFile', 'dataFileName', 'Problem version', 'Number of zones',
        'solutionValue', 'isFeasible', 'solutionStatus', 'dualBound', 'cpuTime'
    ]
    required = {'dataFileName', 'Problem version', 'Number of zones', 'cpuTime'}

    resolved_paths = expand_paths(csv_paths)
    if not resolved_paths:
        print("Aucun CSV trouvé avec les chemins fournis → arrêt")
        return

    for path in resolved_paths:
        if not os.path.isfile(path):
            print("Fichier introuvable :", path)
            continue

        df = pd.read_csv(path, sep=';')

        if not required.issubset(df.columns):
            # Les CSV générés sans en-têtes peuvent être relus en imposant les noms attendus
            try:
                df = pd.read_csv(path, sep=';', header=None, names=fallback_cols)
            except Exception as exc:
                print(f"Lecture alternative impossible pour {path} : {exc}")
                continue

            if not required.issubset(df.columns):
                print("Colonnes manquantes dans :", path)
                continue

        df['cpuTime'] = pd.to_numeric(df['cpuTime'], errors='coerce')
        df['Number of zones'] = pd.to_numeric(df['Number of zones'], errors='coerce')
        df = df.dropna(subset=['cpuTime', 'Number of zones'])
        if df.empty:
            print("Pas de mesures CPU exploitables dans :", path)
            continue

        grouping_cols = ['dataFileName', 'Problem version', 'Number of zones']
        df_unique = (
            df
            .groupby(grouping_cols, as_index=False)
            .agg(cpuTime=('cpuTime', 'min'))
        )

        if df_unique.empty:
            print("Pas d'instances uniques construites pour :", path)
            continue

        data_sets.append({
            'path': path,
            'label': label_from_path(path),
            'df_unique': df_unique
        })

    if not data_sets:
        print("Aucun CSV exploitable → arrêt")
        return

    plt.figure(figsize=(9, 6))
    stats = []
    zone_palette = {
        1: ['tab:red', '#ff9e80'],
        3: ['tab:blue', '#4dabf5'],
        7: ['tab:orange', '#ffb347'],
        10: ['tab:green', '#8dd3c7']
    }
    per_zone_cycles = {
        zone: cycle(colors if isinstance(colors, (list, tuple)) else [colors])
        for zone, colors in zone_palette.items()
    }
    default_cycle = cycle(plt.rcParams['axes.prop_cycle'].by_key()['color'])

    for dataset in data_sets:
        grouped = dataset['df_unique'].groupby(['Number of zones', 'Problem version'])
        for (zone_value, version_value), df_zone in grouped:
            df_zone = df_zone.sort_values('cpuTime').reset_index(drop=True)
            df_zone['instances_resolues'] = range(1, len(df_zone) + 1)

            zone_key = int(zone_value)
            color_iter = per_zone_cycles.get(zone_key)
            color = next(color_iter) if color_iter else next(default_cycle)
            label = f"{dataset['label']} | Z = {zone_key} | V = {int(version_value)}"

            plt.step(
                df_zone['cpuTime'],
                df_zone['instances_resolues'],
                where='post',
                color=color,
                label=label
            )

            stats.append({
                'dataset': dataset['label'],
                'zone': zone_key,
                'version': int(version_value),
                'instances': len(df_zone),
                'median_cpu': df_zone['cpuTime'].median()
            })

    plt.xlabel("Temps CPU (s)")
    plt.ylabel("Nombre d'instances résolues")
    plt.grid(True)
    plt.legend(title="Nombre de zones (Z)")

    output_path = "instances_optimal_vs_cpu.png"
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

    print("Graphe généré avec succès :")
    print(os.path.abspath(output_path))
    for item in sorted(stats, key=lambda x: (x['dataset'], x['zone'], x.get('version', 0))):
        print(
            f"- {item['dataset']} | Z={item['zone']} | V={item.get('version', '?')}: "
            f"{item['instances']} instances, médiane CPU = "
            f"{item['median_cpu']:.2f} s"
        )


csv_file_paths = [
    # "Solutions_V1_Z1_Standard_*/logs/result_summary.csv",
    # "Solutions_V21_Z3_Standard_*/logs/result_summary.csv",
    # "Solutions_V21_Z7_Standard_*/logs/result_summary.csv",
    # "Solutions_V21_Z10_Standard_*/logs/result_summary.csv",
    "Solutions_V3_Z3_Standard_*/logs/result_summary.csv",
    # "Solutions_V22_Z3_Standard_2026-01-23_16-22-26/logs/result_summary.csv",
    # "Solutions_V22_Z6_Standard_*/logs/result_summary.csv",
    # "Solutions_V22_Z10_Standard_*/logs/result_summary.csv",
    "Solution_V3_Z7_2026-01-23_11-47-29/logs/result_summary.csv"
]


plot_optimal_instances_correct(csv_file_paths)

