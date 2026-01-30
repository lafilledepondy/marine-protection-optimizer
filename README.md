# MarineOpt Environment Setup

## Overview

MarineOpt solves variants of the marine protected areas design problem through mixed-integer programming and post-processing scripts. The core CLI entry points live in [Code/solver.py](Code/solver.py) for single instances and [Code/scriptExperiments.py](Code/scriptExperiments.py) for batch runs. Supporting utilities parse grid data ([Code/data.py](Code/data.py)), validate solutions ([Code/solutionValidator.py](Code/solutionValidator.py)), and build experiment summaries/graphics ([Code/scriptCreateSummaryFiles.py](Code/scriptCreateSummaryFiles.py), [Code/scriptGraphicSummary.py](Code/scriptGraphicSummary.py)).

## Repository Layout

- [Code/](Code) – optimization models, data loaders, CLI helpers, plotting scripts.
- [Solutions/](Solutions) – sample `.sol` outputs for quick validation.
- `Solutions_*` – dated experiment folders created by the batch runner (each contains `logs/`, `solutions/`, and `time_of_experiments.txt`).
- [Code_Highspy_neMarchePas/](Code_Highspy_neMarchePas) – archived experiments with the HiGHS native Python API (kept for reference only).

## Python Version & Virtual Environment

- Target Python: **3.10+** (the repo currently runs on 3.12 via `.venv`).
- Recommended setup:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  python -m pip install --upgrade pip
  ```

## Required Python Packages

| Package        | Install command              | Used in                                                                                                                                        |
| -------------- | ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `pyomo[appsi]` | `pip install "pyomo[appsi]"` | [Code/solver.py](Code/solver.py), [Code/models.py](Code/models.py)                                                                             |
| `numpy`        | `pip install numpy`          | [Code/data.py](Code/data.py), [Code/helpersShowGrid.py](Code/helpersShowGrid.py)                                                               |
| `matplotlib`   | `pip install matplotlib`     | [Code/data.py](Code/data.py), [Code/helpersShowGrid.py](Code/helpersShowGrid.py), [Code/scriptGraphicSummary.py](Code/scriptGraphicSummary.py) |
| `pandas`       | `pip install pandas`         | [Code/scriptGraphicSummary.py](Code/scriptGraphicSummary.py)                                                                                   |
| `tabulate`     | `pip install tabulate`       | [Code/scriptExperiments.py](Code/scriptExperiments.py)                                                                                         |

## Optional / Feature-Specific Packages

| Package                         | When to install                                                                      | Notes                                                                                                                |
| ------------------------------- | ------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| `highspy`                       | `pip install highspy` if you plan to use the `highs` solver via `--solverName highs` | Required by Pyomo's `appsi_highs` driver for high-performance HiGHS runs.                                            |
| `gurobipy`                      | Install from Gurobi (requires license) when using `--solverName gurobi`              | Ensure the `GRB_LICENSE_FILE` environment variable points to a valid license.                                        |
| `cylp` or external CBC binaries | Needed for `--solverName cbc`                                                        | On Ubuntu you can run `sudo apt install coinor-cbc`. Pyomo will call the CBC executable that appears on your `PATH`. |

## Installing Everything at Once

After activating the virtual environment:

```bash
pip install "pyomo[appsi]" numpy pandas matplotlib tabulate highspy
```

Install solver-specific extras only if you need that backend (Gurobi, HiGHS, or CBC).

## Verifying the Environment

1. **Check Pyomo/Solver availability**

```bash
python Code/solver.py \
  -d=/path/to/instances/toy01.dat \
  -v=1 \
  -z=1 \
  -t=30 \
  -s=highs \
  -f=Solutions
```

Point `-d` to any `.dat` instance available in your dataset folder. 2. **Batch experiments**: run `python Code/scriptExperiments.py -d /path/to/data -f Solutions_V3_Z3_Standard -v 3 -z 3 7 10 -t 120 -s highs` to spawn dated solution/log folders. 3. **Summaries and graphics**:

- Combine logs into CSV: `python Code/scriptCreateSummaryFiles.py -l Solutions_V3_Z3_Standard_YYYY-MM-DD_HH-MM-SS/logs`
- Plot CPU-time CDFs: `python Code/scriptGraphicSummary.py`

## Troubleshooting Tips

- If Pyomo reports that a solver is unavailable, ensure the binary is on `PATH` (`which cbc`, `which highs`) or that the proprietary solver license is configured.
- When running on headless servers, `matplotlib` already forces the `Agg` backend in [Code/scriptGraphicSummary.py](Code/scriptGraphicSummary.py), so no extra setup is needed.
- To reset the virtual environment safely, delete `.venv/` and recreate it with the steps in the **Python Version & Virtual Environment** section.
