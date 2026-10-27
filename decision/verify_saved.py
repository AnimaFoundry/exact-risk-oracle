"""Independent standard-library replay of the saved sampling-decision evidence.

SPDX-License-Identifier: MIT. No imports from the solver, runner, design, scoring,
CVXPY or the original certificate checker. It checks saved certificates and
reconstructs finite calendars/grids; it never reruns continuous optimization or
remeasures a timing. Written after the protocol was frozen, not a preregistration.
"""
from collections import Counter
from datetime import datetime
from fractions import Fraction as F
from itertools import product
import hashlib
import json
import math
from pathlib import Path
import statistics


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def close(actual, expected, message, tolerance=1e-12):
    require(isinstance(actual, (float, int)) and not isinstance(actual, bool)
            and math.isfinite(actual) and math.isfinite(expected)
            and abs(actual - expected) <= tolerance * max(1.0, abs(expected)), message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def parse(text):
    def invalid_constant(value):
        raise ValueError("Nonstandard JSON float: " + value)
    return json.loads(text, object_pairs_hook=unique_object, parse_constant=invalid_constant)


def read(path):
    return parse(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def risk_at(d, v, point):
    variance = sum((vi * (1 - xi * xi) for vi, xi in zip(v, point)), F(0)) / 4
    bias = sum((di * xi for di, xi in zip(d, point)), F(0)) / 2
    return variance + bias * bias


def certificate_check(d, v, certificate):
    x = tuple(map(F, certificate["x"]))
    loading = tuple(map(F, certificate["loading"]))
    require(len(x) == len(d) == len(loading), "certificate dimensions")
    require(all(-1 <= xi <= 1 for xi in x), "certificate witness outside box")
    require(all(li >= 0 for li in loading), "negative diagonal bound")
    denominator = tuple(vi + li for vi, li in zip(v, loading))
    require(all(bi != 0 or di == 0 for di, bi in zip(d, denominator)), "uncertified zero denominator")
    bound_ratio = sum((di * di / bi for di, bi in zip(d, denominator) if bi), F(0))
    require(bound_ratio <= 1, "majorizer does not upper-bound objective")
    objective = 4 * risk_at(d, v, x) - sum(v, F(0))
    require(objective == sum(loading, F(0)), "witness fails to attain upper bound")
    require(F(certificate["objective"]) == objective, "reported objective")
    require(F(certificate["risk"]) == risk_at(d, v, x), "reported risk")
    return F(certificate["risk"])


def scenario_check(scenario):
    """Enumerate entire action schedules, independently of the production DP."""
    weights = tuple(map(F, scenario["weights"]))
    c = F(scenario["shrinkage"])
    require(2 <= len(weights) <= 4 and sum(weights) == 1
            and all(w > 0 for w in weights) and c in (0, F(1, 2), 1, 2), "scenario contract")
    options = []
    powered = 0
    for slot in scenario["calendar"]:
        require(type(slot["powered"]) is bool, "power status")
        eligible = slot["eligible"]
        require(eligible and eligible == sorted(set(eligible))
                and all(type(i) is int and 0 <= i < len(weights) for i in eligible), "eligible channels")
        powered += slot["powered"]
        options.append(tuple([-1] + eligible) if slot["powered"] else (-1,))
    require(powered == scenario["budget"] and powered in (2, 3, 4), "power budget")
    paths = {}
    for schedule in product(*options):
        counts = tuple(schedule.count(i) for i in range(len(weights)))
        if counts not in paths or schedule < paths[counts]:
            paths[counts] = schedule
    expected = [{"counts": list(n), "schedule": list(paths[n])} for n in sorted(paths)]
    require(scenario["candidates"] == expected, "missing/invalid candidate or noncanonical schedule")
    inputs = []
    for row in expected:
        a = [wi * F(ni) / (ni + c) if ni else F(0) for wi, ni in zip(weights, row["counts"])]
        d = tuple(wi - ai for wi, ai in zip(weights, a))
        v = tuple(ai * ai / ni if ni else F(0) for ai, ni in zip(a, row["counts"]))
        inputs.append((d, v))
    return inputs


def grid_check(d, v, saved):
    """Recompute the complete signed five-point grid, not the production shortcut."""
    maximum = max(risk_at(d, v, x) for x in product(
        (F(-1), F(-1, 2), F(0), F(1, 2), F(1)), repeat=len(d)))
    witness = tuple(map(F, saved["x"]))
    require(len(witness) == len(d) and all(x in (0, F(1, 2), 1) for x in witness), "grid witness")
    require(F(saved["risk"]) == maximum == risk_at(d, v, witness), "grid maximum mismatch")
    require(saved["points_evaluated"] == 3 ** len(d), "grid symmetry workload")
    return maximum


def conic_check(d, v, saved):
    """Independently recompute the numerical conditions from the saved vectors."""
    require(saved["dimension"] == len(d) and saved["active_dimension"] == sum(z > 0 for z in d), "conic dimension")
    require(saved["is_dpp"] is True and saved["enforce_dpp"] is True
            and saved["warm_start_requested"] is True, "conic reuse contract")
    require(saved["solver_options"] == {"tol_gap_abs":1e-10, "tol_gap_rel":1e-10,
                                        "tol_feas":1e-10, "max_iter":200}, "conic options")
    require(saved["residual_tolerance"] == 1e-7
            and saved["objective_is_exact_certificate"] is False, "conic certificate boundary")
    if not any(d):
        require(saved["status"] == "analytic_zero_d" and saved["solver_calls"] == 0, "analytic case mislabelled")
        require(saved["lambda"] == [0.0] * len(d) and saved["objective"] == 0, "analytic zero objective")
        close(saved["risk"], float(sum(v, F(0))) / 4, "analytic risk")
        require(saved["numerically_accepted"] is True, "analytic acceptance")
        return True
    require(saved["solver_calls"] == 1, "conic retries/call count")
    scale = max(sum((z * z for z in d), F(0)), max(v))
    require(F(saved["normalization_scale_exact"]) == scale, "normalization is not input-derived")
    close(saved["normalization_scale"], float(scale), "scale float")
    if saved["status"] == "solver_error" or saved.get("lambda_normalized") is None:
        require(saved["numerically_accepted"] is False, "missing solver point accepted")
        return False
    loading, epigraph = saved["lambda_normalized"], saved["epigraph"]
    require(len(loading) == len(d) == len(epigraph), "returned conic vectors")
    if any(isinstance(z, dict) for z in loading + epigraph):
        require(saved["numerically_accepted"] is False
                and saved["residuals"]["finite"] is False, "nonfinite point accepted")
        return False
    require(all(isinstance(z, (int, float)) and math.isfinite(z) for z in loading + epigraph), "unencoded nonfinite vector")
    dn = [math.sqrt(float(di * di / scale)) for di in d]
    vn = [float(vi / scale) for vi in v]
    denominator = [vi + li for vi, li in zip(vn, loading)]
    positive = all(b > 0 for di, b in zip(dn, denominator) if di > 0)
    cone_sum = math.fsum(di * di / b for di, b in zip(dn, denominator) if di > 0) if positive else None
    soc = max(0.0, max(math.hypot(2 * di, b - z) - b - z
                       for di, b, z in zip(dn, denominator, epigraph)))
    checks = {
        "nonnegative_violation_normalized": max(0.0, -min(loading)),
        "epigraph_nonnegative_violation": max(0.0, -min(epigraph)),
        "soc_violation": soc,
        "epigraph_sum_violation": max(0.0, math.fsum(epigraph) - 1.0),
        "cone_violation": max(0.0, cone_sum - 1.0) if positive else None,
    }
    residuals = saved["residuals"]
    require(residuals["finite"] is True, "finite-vector residual status")
    require(residuals["positive_active_denominators"] == positive, "active denominator status")
    for key, value in checks.items():
        if value is None:
            require(residuals[key] is None, key)
        else:
            close(residuals[key], value, key)
    if cone_sum is not None:
        close(residuals["cone_sum"], cone_sum, "cone sum")
    objective = math.fsum(loading) * float(scale)
    close(saved["objective"], objective, "conic objective rescaling")
    close(saved["risk"], (float(sum(v, F(0))) + objective) / 4, "conic risk reconstruction")
    require(len(saved["lambda"]) == len(d), "rescaled loading dimension")
    for exact, reported in zip(loading, saved["lambda"]):
        close(reported, exact * float(scale), "rescaled loading")
    objective_disagreement = abs(math.fsum(loading) - saved["solver_objective"] / float(scale))
    close(residuals["objective_disagreement_normalized"], objective_disagreement, "objective residual")
    numerical = positive and all(value is not None and value <= 1e-7 for value in checks.values()) and objective_disagreement <= 1e-7
    require(residuals["accepted"] == numerical, "conic residual acceptance")
    accepted = saved["status"] == "optimal" and numerical
    require(saved["numerically_accepted"] == accepted, "conic final status acceptance")
    return accepted


def choice(values, truth):
    minimum = min(values)
    winners = [i for i, value in enumerate(values) if value == minimum]
    regrets = [truth[i] - min(truth) for i in winners]
    return {"chosen":winners[0], "minimizers":winners, "reported_minimum":str(minimum),
            "selected_risk":str(truth[winners[0]]), "selected_regret":str(regrets[0]),
            "best_tied_regret":str(min(regrets)), "worst_tied_regret":str(max(regrets))}


def numerical_choice(rows, truth):
    if any(not r["conic"]["numerically_accepted"] or r["conic"]["risk"] is None for r in rows):
        return {"status":"INCONCLUSIVE_NUMERICAL_FAILURE"}
    values = [r["conic"]["risk"] for r in rows]
    near = [i for i, z in enumerate(values) if z <= min(values) + 1e-7]
    regrets = [truth[i] - min(truth) for i in near]
    return {"status":"accepted", "chosen":near[0], "numerical_near_set":near,
            "selected_risk":str(truth[near[0]]), "selected_regret":str(regrets[0]),
            "best_near_regret":str(min(regrets)), "worst_near_regret":str(max(regrets)),
            "includes_exact_optimum":min(regrets) == 0}


def summary_rebuild(scenarios, rows, setups):
    decisions = []
    grouped = {(s["id"], p):[] for s in scenarios for p in range(3)}
    for row in rows:
        grouped[(row["scenario"], row["pass"])].append(row)
    for scenario in scenarios:
        sid = scenario["id"]
        batches = [sorted(grouped[sid, p], key=lambda r:r["candidate"]) for p in range(3)]
        truth = [F(r["exact"]["risk"]) for r in batches[0]]
        passes = []
        for rep, batch in enumerate(batches):
            times = {m:sum(r[m + "_seconds"] for r in batch) for m in ("grid","exact","conic")}
            times["conic_with_build_seconds"] = times["conic"] + (setups[sid]["build_seconds"] if rep == 0 else 0)
            passes.append({"pass":rep,
                           "exact":choice([F(r["exact"]["risk"]) for r in batch], truth),
                           "grid":choice([F(r["grid"]["risk"]) for r in batch], truth),
                           "conic":numerical_choice(batch, truth), "times":times,
                           "conic_to_exact_ratio":times["conic_with_build_seconds"] / times["exact"]})
        decisions.append({"scenario":sid, "candidates":len(truth), "optimal_risk":str(min(truth)),
                          "passes":passes,
                          "tie_robust_gain":F(passes[0]["grid"]["best_tied_regret"]) > 0,
                          "any_grid_tie_regret":F(passes[0]["grid"]["worst_tied_regret"]) > 0,
                          "selected_grid_regret":passes[0]["grid"]["selected_regret"],
                          "grid_choice_stable":len({p["grid"]["chosen"] for p in passes}) == 1,
                          "conic_choice_stable":all(p["conic"]["status"] == "accepted" for p in passes)
                          and len({p["conic"]["chosen"] for p in passes}) == 1})
    first = [r for r in rows if r["pass"] == 0]
    errors = [abs(r["conic"]["risk"] - float(F(r["exact"]["risk"]))) for r in rows if r["conic"]["risk"] is not None]
    conic_ok = all(r["conic"]["numerically_accepted"] for r in rows) and all(z <= 1e-7 for z in errors)
    robust = sum(d["tie_robust_gain"] for d in decisions)
    tied = sum(d["any_grid_tie_regret"] for d in decisions)
    cold = [d["passes"][0]["conic_to_exact_ratio"] for d in decisions]
    warm = [statistics.median([p["conic_to_exact_ratio"] for p in d["passes"][1:]]) for d in decisions]
    def descriptive(values):
        return {"median":statistics.median(values), "min":min(values), "max":max(values)}
    return {"status":"complete", "scenarios_completed":len(scenarios),
            "unique_allocations_expected":len(first), "rows_completed":len(rows),
            "certificate_valid":len(rows), "reference_matches":len(first),
            "grid_understatements_first_pass":sum(F(r["grid"]["risk"]) < F(r["exact"]["risk"]) for r in first),
            "conic_accepted":sum(r["conic"]["numerically_accepted"] for r in rows),
            "conic_actual_solves":sum(r["conic"]["solver_calls"] for r in rows),
            "conic_status_counts":dict(Counter(r["conic"]["status"] for r in rows)),
            "conic_max_absolute_risk_error":max(errors) if errors else None,
            "conic_warning_records":sum(bool(r["conic"]["warnings"]) for r in rows),
            "correctness_gate":True, "conic_comparison_gate":conic_ok,
            "decision_result":"TIE_ROBUST_GAIN_OBSERVED" if robust else "TIE_DEPENDENT_ONLY" if tied else "NO_DECISION_GAIN_OBSERVED",
            "tie_robust_gain_scenarios":robust, "any_grid_tie_regret_scenarios":tied,
            "selected_grid_regret_scenarios":sum(F(d["selected_grid_regret"]) > 0 for d in decisions),
            "cold_ratio_descriptive_all":descriptive(cold), "warm_ratio_descriptive_all":descriptive(warm),
            "speed_claim_eligible":conic_ok,
            "speed_2x_gate":conic_ok and statistics.median(warm) >= 2,
            "decisions":decisions}


def verify_bundle(root):
    root = Path(root)
    folder = root / "decision"
    freeze = read(folder / "freeze.json")
    receipt = read(folder / "results/receipt.json")
    guard = read(folder / "results/RUN_GUARD.json")
    fixture = read(folder / "inputs.json")
    summary = read(folder / "results/summary.json")
    setups = read(folder / "results/setups.json")
    require(receipt["status"] == "complete" and receipt["failure"] is None, "incomplete cohort")
    require(fixture["seed"] == 271027117 and len(fixture["scenarios"]) == 48, "frozen cohort contract")
    require(len(freeze["files"]) == 15, "freeze file count")
    for relative, expected in freeze["files"].items():
        path = Path(relative)
        require(not path.is_absolute() and ".." not in path.parts, "unsafe frozen path")
        require(sha(root / path) == expected, "frozen hash changed: " + relative)
    for field, path in [("freeze_sha256", folder/"freeze.json"), ("fixture_sha256",folder/"inputs.json"),
                        ("rows_sha256",folder/"results/rows.jsonl"), ("setups_sha256",folder/"results/setups.json")]:
        require(receipt[field] == sha(path), "receipt hash: " + field)
    require(guard["freeze_sha256"] == receipt["freeze_sha256"], "guard freeze")
    require(freeze["dependencies"] == receipt["dependencies"] and freeze["python"] == receipt["python"], "run environment changed")
    for source in (freeze, receipt):
        require(source["model_calls"] == 0 and source["external_api_usd"] == 0, "resource contract")
    times = [freeze["created_utc"], guard["started_utc"], receipt["started_utc"], receipt["finished_utc"]]
    dates = [datetime.fromisoformat(z.replace("Z", "+00:00")) for z in times]
    require(dates == sorted(dates), "pre-execution chronology")
    require(math.isfinite(receipt["wall_seconds"]) and receipt["wall_seconds"] >= 0
            and freeze["between_call_wall_seconds"] == 900, "saved wall budget contract")
    scenarios = fixture["scenarios"]
    require(len({s["id"] for s in scenarios}) == 48, "scenario identity collision")
    require(set(setups) == {s["id"] for s in scenarios}, "setup identities")
    derived = {s["id"]:scenario_check(s) for s in scenarios}
    count = sum(len(v) for v in derived.values())
    require(count == freeze["unique_allocations"] and count <= 1344
            and count * 3 == freeze["calls_per_method"] <= 4032, "evaluation budget")
    rows = [parse(line) for line in (folder/"results/rows.jsonl").read_text(encoding="utf-8").splitlines()]
    expected_keys = [(s["id"], rep, i) for s in scenarios for rep in range(3) for i in range(len(s["candidates"]))]
    require([(r["scenario"],r["pass"],r["candidate"]) for r in rows] == expected_keys, "missing/duplicate/reordered row")
    scenarios_by_id = {s["id"]:s for s in scenarios}
    grid_values = {}
    prior_solves = Counter()
    for row in rows:
        sid, rep, index = row["scenario"], row["pass"], row["candidate"]
        scenario = scenarios_by_id[sid]
        d, v = derived[sid][index]
        require(row["counts"] == scenario["candidates"][index]["counts"], "row count mapping")
        require(tuple(map(F,row["d"])) == d and tuple(map(F,row["v"])) == v, "statistical reduction")
        require(row["method_order"] == [["grid","exact","conic"],["exact","conic","grid"],
                                        ["conic","grid","exact"]][rep], "method rotation")
        risk = certificate_check(d,v,row["exact"])
        require(row["certificate_valid"] is True, "saved certificate status")
        if rep == 0:
            grid_values[sid,index] = grid_check(d,v,row["grid"])
            require(row["reference_match"] is True and F(row["reference_risk"]) == risk, "saved reference disagreement")
            point = tuple(map(F,row["reference_x"]))
            require(len(point) == len(d) and all(0 <= z <= 1 for z in point)
                    and risk_at(d,v,point) == risk, "reference witness")
        else:
            require(F(row["grid"]["risk"]) == grid_values[sid,index], "repeat grid changed")
            point = tuple(map(F, row["grid"]["x"]))
            require(len(point) == len(d) and all(z in (0, F(1,2), 1) for z in point)
                    and risk_at(d,v,point) == grid_values[sid,index]
                    and row["grid"]["points_evaluated"] == 3 ** len(d), "repeat grid witness")
        require(F(row["grid"]["risk"]) <= risk, "grid above global certificate")
        conic_check(d,v,row["conic"])
        conic = row["conic"]
        require(conic["call_index"] == rep * len(scenario["candidates"]) + index + 1, "reuse call sequence")
        require(conic["prior_solver_calls"] == prior_solves[sid], "solver reuse sequence")
        prior_solves[sid] += conic["solver_calls"]
        for method in ("grid","exact","conic"):
            value = row[method + "_seconds"]
            require(isinstance(value,(float,int)) and math.isfinite(value) and value >= 0, "invalid saved timing")
        require(setups[sid]["is_dpp"] is True and math.isfinite(setups[sid]["build_seconds"])
                and setups[sid]["build_seconds"] >= 0, "invalid construction record")
    reconstructed = summary_rebuild(scenarios, rows, setups)
    require(summary == reconstructed, "decision/count/timing summary disagrees with independent replay")
    return {"status":"PASS", "frozen_files_checked":len(freeze["files"]), "scenarios":48,
            "complete_rows":len(rows), "candidate_sets_independently_enumerated":48,
            "certificates_checked":len(rows), "full_signed_grids_recomputed":count,
            "saved_reference_values_and_witnesses_checked":count,
            "conic_records_rechecked":len(rows), "continuous_optimizer_calls":0,
            "model_calls":0, "timings_remeasured":False,
            "decision_result":reconstructed["decision_result"],
            "conic_comparison_gate":reconstructed["conic_comparison_gate"],
            "rows_sha256":receipt["rows_sha256"]}


if __name__ == "__main__":
    print(json.dumps(verify_bundle(Path(__file__).resolve().parents[1]), indent=2, sort_keys=True))
