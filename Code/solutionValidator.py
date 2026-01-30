import os
import re

def checkSolution(data, solution, version, verbose=False):
    if data is None or solution is None:
        if verbose:
            print("[solutionValidator] Data and solution objects are required.")
        return False

    validator = _get_validator(version)
    if validator is None:
        if verbose:
            print(f"[solutionValidator] Unknown version: {version}")
        return False

    max_zones = _extract_max_zones(data)
    is_valid, message = validator(solution, max_zones, data)

    if verbose and message:
        print(f"[solutionValidator] {message}")

    return is_valid


def _get_validator(version):
    validators = {
        1: _validate_v1,
        2.1: _validate_v2_1,
        21: _validate_v2_1,
        2.2: _validate_v2_2,
        22: _validate_v2_2,
        3: _validate_v3,
    }
    return validators.get(version)


def _validate_v1(solution, max_zones, data):
    return _run_common_checks(solution, data)


def _validate_v2_1(solution, max_zones, data):
    is_valid, msg = _check_max_zones(solution, max_zones)
    if not is_valid:
        return False, msg
    return _run_common_checks(solution, data)


def _validate_v2_2(solution, max_zones, data):
    is_valid, msg = _check_max_zones(solution, max_zones)
    if not is_valid:
        return False, msg
    return _run_common_checks(solution, data)


def _validate_v3(solution, max_zones, data):
    is_valid, msg = _check_max_zones(solution, max_zones)
    if not is_valid:
        return False, msg
    return _run_common_checks(solution, data)


def _check_max_zones(solution, max_zones):
    if max_zones is None:
        return True, ""
    zone_count = _extract_zone_count(solution)
    if zone_count is None:
        return True, "Max zone check skipped (zone count unavailable)."
    if zone_count > max_zones:
        return False, f"Solution uses {zone_count} zones but at most {max_zones} are allowed."
    return True, ""

def _check_only_marine_sectors(solution, data):
    if not hasattr(solution, "selectedSectors"):
        return True, "Marine check skipped (selected sectors unavailable)."

    sectors = solution.selectedSectors
    if callable(sectors):
        sectors = sectors()

    nb_cols = data.width()

    for s in sectors:
        i, j = s // nb_cols, s % nb_cols
        if data.isLand(i * nb_cols + j):
            return False, f"Sector {s} ({i},{j}) is terrestrial."
    return True, ""


def _extract_zone_count(solution):
    attrs = [
        "nbZonesUsed",
        "nb_zones_used",
        "nbZones",
        "nb_zones",
        "zones",
        "selectedZones",
        "zoneList",
    ]
    for attr in attrs:
        if not hasattr(solution, attr):
            continue
        value = getattr(solution, attr)
        if callable(value):
            try:
                value = value()
            except TypeError:
                continue
        count = _normalize_count_like(value)
        if count is not None:
            return count
    return None


def _normalize_count_like(value):
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, (list, tuple, set, dict)):
        return len(value)
    return None


def _check_protected_species_constraint(solution, data):
    required = _extract_protected_species_requirement(data)
    if not required:
        return True, ""
    solution_counts = _extract_solution_species_count(solution)
    if not solution_counts:
        return True, "Species constraint skipped (counts unavailable)."
    tolerance = 1e-9
    for species, min_required in required.items():
        min_required_value = _to_float(min_required)
        if min_required_value is None:
            continue
        current_value = _to_float(solution_counts.get(species, 0)) or 0.0
        if current_value + tolerance < min_required_value:
            return False, (
                f"Species '{species}' does not meet the protected quota "
                f"({current_value} < {min_required_value})."
            )
    return True, ""


def _extract_protected_species_requirement(data):
    attrs = [
        "protectedSpeciesCount",
        "protected_species_count",
        "speciesRequirements",
        "species_requirements",
        "speciesRequirement",
        "requiredSpecies",
    ]
    for attr in attrs:
        if not hasattr(data, attr):
            continue
        value = getattr(data, attr)
        if callable(value):
            try:
                value = value()
            except TypeError:
                continue
        if isinstance(value, dict):
            return value
    method_names = ["getProtectedSpeciesCount", "getSpeciesRequirements"]
    for name in method_names:
        if not hasattr(data, name):
            continue
        method = getattr(data, name)
        if callable(method):
            try:
                value = method()
            except Exception:
                continue
            if isinstance(value, dict):
                return value
    return {}


def _extract_solution_species_count(solution):
    attrs = [
        "speciesCount",
        "species_count",
        "speciesAllocation",
        "species_allocation",
        "protectedSpecies",
        "protected_species",
    ]
    for attr in attrs:
        if not hasattr(solution, attr):
            continue
        value = getattr(solution, attr)
        if callable(value):
            try:
                value = value()
            except TypeError:
                continue
        if isinstance(value, dict):
            return value
    zone_attrs = ["zones", "selectedZones", "zoneDetails", "zone_details"]
    for attr in zone_attrs:
        if not hasattr(solution, attr):
            continue
        value = getattr(solution, attr)
        if callable(value):
            try:
                value = value()
            except TypeError:
                continue
        aggregated = _aggregate_species_from_zones(value)
        if aggregated:
            return aggregated
    method_names = ["getSpeciesCount", "getSpeciesAllocation"]
    for name in method_names:
        if not hasattr(solution, name):
            continue
        method = getattr(solution, name)
        if callable(method):
            try:
                value = method()
            except Exception:
                continue
            aggregated = _aggregate_species_from_zones(value)
            if aggregated:
                return aggregated
    zone_methods = ["getZones", "getSelectedZones"]
    for name in zone_methods:
        if not hasattr(solution, name):
            continue
        method = getattr(solution, name)
        if callable(method):
            try:
                value = method()
            except Exception:
                continue
            aggregated = _aggregate_species_from_zones(value)
            if aggregated:
                return aggregated
    return {}


def _normalize_selected_sectors(sectors, nb_cols):
    if isinstance(sectors, dict):
        return list(sectors.keys())
    if isinstance(sectors, (list, tuple, set)):
        normalized = []
        for s in sectors:
            if isinstance(s, dict):
                for key in ("id", "index", "idx", "sector", "sectorId", "sector_id"):
                    if key in s:
                        value = s[key]
                        if isinstance(value, (int, float)):
                            normalized.append(int(value))
                        break
            elif isinstance(s, (int, float)):
                normalized.append(int(s))
        return normalized
    return []


def _run_common_checks(solution, data):
    checks = (
        _check_marine_sectors_constraint,
        _check_protected_species_constraint,
        _check_objective_value,
    )
    last_message = ""
    for check in checks:
        is_valid, message = check(solution, data)
        if not is_valid:
            return False, message
        if message:
            last_message = message
    return True, last_message


def _check_marine_sectors_constraint(solution, data):
    selected = _extract_selected_sectors(solution)
    if not selected:
        return True, "Marine sector check skipped (selected sectors unavailable)."
    sector_matrix = _extract_sector_matrix(data)
    if not sector_matrix:
        return True, "Marine sector check skipped (grid unavailable)."
    nb_cols = _extract_nb_cols(data)
    if nb_cols is None:
        first_row = sector_matrix[0] if sector_matrix else None
        if isinstance(first_row, (list, tuple)):
            nb_cols = len(first_row)
    if not nb_cols:
        return True, "Marine sector check skipped (nbCols unavailable)."
    total_rows = len(sector_matrix)
    for idx in selected:
        if idx is None:
            continue
        if idx < 0:
            return False, f"Sector index {idx} is invalid (negative)."
        row = idx // nb_cols
        col = idx % nb_cols
        if row >= total_rows or col >= len(sector_matrix[row]):
            return False, f"Sector index {idx} maps outside the grid ({row}, {col})."
        if sector_matrix[row][col] != 0:
            return False, (
                f"Sector {idx} at ({row}, {col}) is not marine "
                f"(value={sector_matrix[row][col]})."
            )
    return True, ""


def _check_objective_value(solution, data):
    selected = _extract_selected_sectors(solution)
    if not selected:
        return True, "Objective check skipped (selected sectors unavailable)."
    sector_values = _extract_sector_values(data)
    if sector_values is None:
        return True, "Objective check skipped (sector values unavailable)."
    objective_value = _extract_objective_value(solution)
    if objective_value is None:
        return True, "Objective check skipped (objective value unavailable)."
    nb_cols = _extract_nb_cols(data)
    if nb_cols is None and isinstance(sector_values, (list, tuple)) and sector_values:
        first_row = sector_values[0]
        if isinstance(first_row, (list, tuple)):
            nb_cols = len(first_row)
    total = 0.0
    for idx in selected:
        value = _resolve_sector_value(idx, sector_values, nb_cols)
        if value is None:
            return True, f"Objective check skipped (value missing for sector {idx})."
        total += value
    if abs(total - objective_value) > 1e-6:
        return False, f"Objective mismatch: expected {total}, found {objective_value}."
    return True, ""


def _extract_sector_matrix(data):
    attrs = [
        "sectorMatrix",
        "sector_matrix",
        "sectorGrid",
        "sector_grid",
        "grid",
        "matrix",
        "map",
        "layout",
        "marineMask",
    ]
    for attr in attrs:
        if not hasattr(data, attr):
            continue
        value = getattr(data, attr)
        if callable(value):
            try:
                value = value()
            except TypeError:
                continue
        if isinstance(value, (list, tuple)):
            if not value or isinstance(value[0], (list, tuple)):
                return value
    method_names = ["getSectorMatrix", "getGrid"]
    for name in method_names:
        if not hasattr(data, name):
            continue
        method = getattr(data, name)
        if callable(method):
            try:
                value = method()
            except Exception:
                continue
            if isinstance(value, (list, tuple)):
                if not value or isinstance(value[0], (list, tuple)):
                    return value
    return None


def _extract_nb_cols(data):
    attrs = ["nbCols", "nb_cols", "nbColumns", "columns", "ncols", "width"]
    for attr in attrs:
        if not hasattr(data, attr):
            continue
        value = getattr(data, attr)
        if callable(value):
            try:
                value = value()
            except TypeError:
                continue
        if isinstance(value, (int, float)):
            return int(value)
    method_names = ["getNbCols", "getColumns", "getWidth"]
    for name in method_names:
        if not hasattr(data, name):
            continue
        method = getattr(data, name)
        if callable(method):
            try:
                value = method()
            except Exception:
                continue
            if isinstance(value, (int, float)):
                return int(value)
    return None


def _extract_sector_values(data):
    attrs = [
        "sectorValues",
        "sector_values",
        "cellValues",
        "cell_values",
        "zoneValues",
        "zone_values",
        "valueMatrix",
        "valuesMatrix",
        "gridValues",
        "grid_values",
        "values",
        "profits",
    ]
    for attr in attrs:
        if not hasattr(data, attr):
            continue
        value = getattr(data, attr)
        if callable(value):
            try:
                value = value()
            except TypeError:
                continue
        if isinstance(value, (list, tuple, dict)):
            return value
    method_names = [
        "getSectorValues",
        "getCellValues",
        "getZoneValues",
        "getValueMatrix",
        "getValues",
    ]
    for name in method_names:
        if not hasattr(data, name):
            continue
        method = getattr(data, name)
        if callable(method):
            try:
                value = method()
            except Exception:
                continue
            if isinstance(value, (list, tuple, dict)):
                return value
    return None


def _extract_objective_value(solution):
    attrs = [
        "objective",
        "objectiveValue",
        "objective_value",
        "obj",
        "score",
        "value",
    ]
    for attr in attrs:
        if not hasattr(solution, attr):
            continue
        value = getattr(solution, attr)
        if callable(value):
            try:
                value = value()
            except TypeError:
                continue
        numeric = _to_float(value)
        if numeric is not None:
            return numeric
    method_names = ["getObjective", "getObjectiveValue", "getScore", "getValue"]
    for name in method_names:
        if not hasattr(solution, name):
            continue
        method = getattr(solution, name)
        if callable(method):
            try:
                value = method()
            except Exception:
                continue
            numeric = _to_float(value)
            if numeric is not None:
                return numeric
    return None


def _resolve_sector_value(index, sector_values, nb_cols):
    if sector_values is None:
        return None
    if isinstance(sector_values, dict):
        if index in sector_values:
            return _to_float(sector_values[index])
        if nb_cols is not None:
            row = index // nb_cols
            col = index % nb_cols
            for key in ((row, col), f"{row},{col}", f"{row};{col}"):
                if key in sector_values:
                    return _to_float(sector_values[key])
        return None
    if isinstance(sector_values, (list, tuple)):
        if sector_values and isinstance(sector_values[0], (list, tuple)):
            if nb_cols is None:
                return None
            row = index // nb_cols
            col = index % nb_cols
            if row < len(sector_values) and col < len(sector_values[row]):
                return _to_float(sector_values[row][col])
            return None
        if 0 <= index < len(sector_values):
            return _to_float(sector_values[index])
    return None


def _aggregate_species_from_zones(zones):
    if not isinstance(zones, (list, tuple, set)):
        return {}
    aggregated = {}
    for zone in zones:
        species_data = None
        if isinstance(zone, dict):
            for key in ("species", "speciesCount", "species_count", "protectedSpecies", "protected_species"):
                value = zone.get(key)
                if isinstance(value, dict):
                    species_data = value
                    break
        else:
            for attr in ("species", "speciesCount", "species_count", "protectedSpecies", "protected_species"):
                if hasattr(zone, attr):
                    candidate = getattr(zone, attr)
                    if isinstance(candidate, dict):
                        species_data = candidate
                        break
        if not species_data:
            continue
        for name, amount in species_data.items():
            numeric = _to_float(amount)
            if numeric is None:
                continue
            aggregated[name] = aggregated.get(name, 0.0) + numeric
    return aggregated


def _extract_selected_sectors(solution):
    attrs = [
        "selectedSectors",
        "selected_sectors",
        "sectors",
        "sectorIds",
        "sector_ids",
        "sectorList",
        "selectedZones",
        "zones",
        "zoneIds",
        "zone_ids",
        "cells",
        "selected_cells",
    ]
    for attr in attrs:
        if not hasattr(solution, attr):
            continue
        value = getattr(solution, attr)
        if callable(value):
            try:
                value = value()
            except TypeError:
                continue
        indices = _normalize_index_collection(value)
        if indices:
            return indices
    method_names = ["getSelectedSectors", "getSectors", "getZoneIds", "getSelectedZones"]
    for name in method_names:
        if not hasattr(solution, name):
            continue
        method = getattr(solution, name)
        if callable(method):
            try:
                value = method()
            except Exception:
                continue
            indices = _normalize_index_collection(value)
            if indices:
                return indices
    return []


def _normalize_index_collection(value):
    if value is None or isinstance(value, bool):
        return []
    if isinstance(value, (int, float)):
        return [int(value)]
    if isinstance(value, str):
        return [int(match) for match in re.findall(r"-?\d+", value)]
    if isinstance(value, dict):
        indices = []
        for key_name in ("id", "index", "idx", "sector", "sectorId", "sector_id"):
            candidate = value.get(key_name)
            if isinstance(candidate, bool):
                continue
            if isinstance(candidate, (int, float)):
                indices.append(int(candidate))
        for key in ("sectors", "sectorIds", "indexes", "indices"):
            if key in value:
                indices.extend(_normalize_index_collection(value[key]))
        if not indices:
            for key, selected in value.items():
                if isinstance(key, (int, float)) and bool(selected):
                    indices.append(int(key))
        return indices
    if isinstance(value, (list, tuple, set)):
        indices = []
        for item in value:
            indices.extend(_normalize_index_collection(item))
        return indices
    for attr in ("sector_id", "sectorId", "id", "index", "idx"):
        if hasattr(value, attr):
            attr_value = getattr(value, attr)
            if isinstance(attr_value, bool):
                continue
            if isinstance(attr_value, (int, float)):
                return [int(attr_value)]
    return []


def _to_float(value):
    if isinstance(value, bool):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_max_zones(data):
    attrs = [
        "nbZonesMax",
        "nb_zones_max",
        "maxZones",
        "max_zones",
    ]
    for attr in attrs:
        if not hasattr(data, attr):
            continue
        value = getattr(data, attr)
        if callable(value):
            try:
                value = value()
            except TypeError:
                continue
        if isinstance(value, (int, float)):
            return int(value)
    method_names = ["getNbZonesMax", "maxZones"]
    for name in method_names:
        if not hasattr(data, name):
            continue
        method = getattr(data, name)
        if callable(method):
            try:
                value = method()
            except Exception:
                continue
            if isinstance(value, (int, float)):
                return int(value)
    return None
