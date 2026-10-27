"""Independent standard-library replay of saved evidence, not a new benchmark.

SPDX-License-Identifier: MIT

No solver, reference enumerator, original checker, runner, or optional package
is imported. The only inputs are saved JSON bytes and the frozen source files.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import platform
import sys


class AuditFailure(ValueError):
    pass


def demand(condition, message):
    if not condition:
        raise AuditFailure(message)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        demand(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _no_constant(value):
    raise AuditFailure(f"non-finite JSON constant: {value}")


def decode(text):
    return json.loads(text, object_pairs_hook=_unique_object, parse_constant=_no_constant)


def read_json(path):
    return decode(path.read_text(encoding="utf-8"))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rational(value):
    demand(not isinstance(value, bool) and isinstance(value, (int, str)),
           "saved exact number must be an integer or rational string")
    return Fraction(value)


def number(value, label, *, nonnegative=True):
    demand(not isinstance(value, bool) and isinstance(value, (int, float)),
           f"{label}: expected a real JSON number")
    demand(math.isfinite(value), f"{label}: non-finite value")
    demand(not nonnegative or value >= 0, f"{label}: negative value")
    return float(value)


def close(actual, expected, label, *, atol=1e-12):
    demand(math.isclose(actual, expected, rel_tol=1e-12, abs_tol=atol),
           f"{label}: recomputation differs ({actual!r} versus {expected!r})")


def timestamp(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    demand(result.tzinfo is not None, "timestamp lacks timezone")
    return result


def within(root, relative):
    path = (root / relative).resolve()
    demand(path.is_relative_to(root.resolve()), "manifest path escapes package")
    return path


def audit_certificate(case, row):
    label = case["id"]
    weights = tuple(map(rational, case["w"]))
    coefficients = tuple(map(rational, case["a"]))
    counts = case["n"]
    k = len(weights)
    demand(k > 0 and len(coefficients) == len(counts) == k, f"{label}: dimensions")
    demand(sum(weights) == 1 and all(w > 0 for w in weights), f"{label}: weights")
    demand(all(type(n) is int and n >= 0 for n in counts), f"{label}: counts")
    demand(all(0 <= a <= w and (n != 0 or a == 0)
               for a, w, n in zip(coefficients, weights, counts)), f"{label}: coefficients")
    demand(row["k"] == k and row["group"] == case["group"], f"{label}: row identity")
    d = tuple(w - a for w, a in zip(weights, coefficients))
    v = tuple(a * a / n if n else Fraction(0) for a, n in zip(coefficients, counts))
    certificate = row["certificate"]
    x = tuple(map(rational, certificate["x"]))
    loading = tuple(map(rational, certificate["loading"]))
    demand(len(x) == len(loading) == k, f"{label}: certificate dimensions")
    demand(all(-1 <= z <= 1 for z in x), f"{label}: infeasible witness")
    demand(all(z >= 0 for z in loading), f"{label}: negative loading")

    # Weighted Cauchy proves dd^T <= diag(v+loading). Zero diagonal entries
    # require zero d. The box then supplies the bound sum(loading).
    cauchy_sum = Fraction(0)
    for di, vi, li in zip(d, v, loading):
        diagonal = vi + li
        if diagonal == 0:
            demand(di == 0, f"{label}: unsupported zero denominator")
        else:
            cauchy_sum += di * di / diagonal
    demand(cauchy_sum <= 1, f"{label}: upper-bound inequality fails")
    linear = sum(di * xi for di, xi in zip(d, x))
    attained = linear * linear - sum(vi * xi * xi for vi, xi in zip(v, x))
    upper = sum(loading)
    risk = (sum(v) + attained) / 4
    demand(attained == upper == rational(certificate["objective"]),
           f"{label}: witness does not attain the upper bound")
    demand(risk == rational(certificate["risk"]), f"{label}: saved risk")
    demand(row["certificate_valid"] is True, f"{label}: saved certificate flag")

    # A separate estimator moment calculation checks the risk interpretation.
    # This is not a fresh full binomial-outcome enumeration.
    probabilities = tuple((1 + xi) / 2 for xi in x)
    target_mean = sum(w * p for w, p in zip(weights, probabilities))
    estimator_mean = Fraction(1, 2) + sum(
        a * (p - Fraction(1, 2)) for a, p in zip(coefficients, probabilities)
    )
    variance = sum(a * a * p * (1 - p) / n if n else Fraction(0)
                   for a, p, n in zip(coefficients, probabilities, counts))
    demand(variance + (estimator_mean - target_mean) ** 2 == risk,
           f"{label}: direct estimator moments differ")

    # t and intervals are algorithm metadata, not necessary for the proof.
    metadata_t = rational(certificate["t"])
    demand(type(certificate["intervals"]) is int and certificate["intervals"] >= 0,
           f"{label}: interval metadata")
    all_rationals = x + loading + (metadata_t, attained, risk)
    bits = max(max(z.numerator.bit_length(), z.denominator.bit_length())
               for z in all_rationals)
    demand(row["max_bits"] == bits, f"{label}: rational bit length")
    for key in ("exact_seconds", "check_seconds"):
        number(row[key], f"{label}: {key}")
    return d, v, risk, bits


def audit_conic(row, d, v, exact_risk):
    label = row["id"]
    conic = row["conic"]
    demand(conic["dimension"] == len(d), f"{label}: conic dimension")
    active = [i for i, di in enumerate(d) if di > 0]
    demand(conic["active_dimension"] == len(active), f"{label}: active dimension")
    demand(conic["solver"] == "CLARABEL", f"{label}: conic solver identity")
    demand(conic["solver_options"] == {"max_iter": 200, "tol_feas": 1e-10,
                                      "tol_gap_abs": 1e-10, "tol_gap_rel": 1e-10},
           f"{label}: solver options")
    demand(conic["objective_is_exact_certificate"] is False,
           f"{label}: numerical result mislabeled exact")
    elapsed = number(conic["time_seconds"], f"{label}: conic elapsed")
    calls = conic["solver_calls"]
    demand(type(calls) is int and calls == (1 if active else 0),
           f"{label}: reported conic call count")
    demand(conic["residual_tolerance"] == 1e-7, f"{label}: tolerance changed")
    risk_value = conic["risk"]
    if risk_value is None:
        demand(conic["numerically_accepted"] is False, f"{label}: missing risk accepted")
        demand(row["conic_risk_error"] is None, f"{label}: missing risk error")
        return {"calls": calls, "accepted": False, "error": None, "elapsed": elapsed}

    numerical_risk = number(risk_value, f"{label}: conic risk", nonnegative=False)
    error = abs(numerical_risk - float(exact_risk))
    close(number(row["conic_risk_error"], f"{label}: recorded risk error"), error,
          f"{label}: risk error", atol=1e-18)
    lam = [number(value, f"{label}: numerical loading", nonnegative=False)
           for value in conic["lambda"]]
    demand(len(lam) == len(d), f"{label}: conic loading length")
    numerical_objective = math.fsum(lam)
    close(number(conic["objective"], label, nonnegative=False), numerical_objective,
          f"{label}: numerical objective")
    close(numerical_risk, (float(sum(v)) + numerical_objective) / 4,
          f"{label}: numerical risk reconstruction")
    if active:
        scale = number(conic["normalization_scale"], f"{label}: scale")
        demand(scale > 0, f"{label}: nonpositive scale")
        expected_scale = float(max(sum(di * di for di in d), max(v)))
        close(scale, expected_scale, f"{label}: normalization chosen from inputs", atol=1e-18)
        denominator = [float(v[i]) + lam[i] for i in active]
        demand(all(z > 0 for z in denominator), f"{label}: conic positive denominators")
        cone_sum = math.fsum(float(d[i]) ** 2 / den for i, den in zip(active, denominator))
        nonnegative_violation = max(0.0, -min(lam)) / scale
        cone_violation = max(0.0, cone_sum - 1.0)
        solver_objective = number(conic["solver_objective"], label, nonnegative=False)
        disagreement = abs(numerical_objective - solver_objective) / scale
        accepted = (conic["status"] == "optimal" and nonnegative_violation <= 1e-7
                    and cone_violation <= 1e-7 and disagreement <= 1e-7)
        demand(conic["residuals"]["finite"] is True and
               conic["residuals"]["positive_active_denominators"] is True,
               f"{label}: finite/positive residual flags")
        close(conic["residuals"]["cone_sum"], cone_sum, f"{label}: cone sum")
        close(conic["residuals"]["cone_violation"], cone_violation, f"{label}: cone residual")
        close(conic["residuals"]["nonnegative_violation_normalized"], nonnegative_violation,
              f"{label}: nonnegative residual")
        close(conic["residuals"]["objective_disagreement_normalized"], disagreement,
              f"{label}: objective residual")
    else:
        demand(conic["status"] == "analytic_zero_d" and all(z == 0 for z in lam),
               f"{label}: analytic branch")
        accepted = numerical_objective == 0 and numerical_risk == float(sum(v)) / 4
    demand(conic["numerically_accepted"] is accepted, f"{label}: acceptance flag")
    return {"calls": calls, "accepted": accepted, "error": error, "elapsed": elapsed}


def audit(root):
    root = root.resolve()
    freeze_path = root / "freeze.json"
    freeze = read_json(freeze_path)
    initial = read_json(root / "freeze.preexecution.json")
    fixture = read_json(root / "synthetic_inputs.json")
    receipt = read_json(root / "results/receipt.json")
    guard = read_json(root / "results/RUN_GUARD.json")
    saved_summary = read_json(root / "results/summary.json")
    raw_path = root / "results/rows.jsonl"
    rows = [decode(line) for line in raw_path.read_text(encoding="utf-8").splitlines()]
    cases = fixture["cases"]

    for relative, digest in freeze["files"].items():
        demand(sha256(within(root, relative)) == digest, f"frozen byte mismatch: {relative}")
    operative_digest = sha256(freeze_path)
    demand(receipt["freeze_sha256"] == guard["freeze_sha256"] == operative_digest,
           "operative freeze identity")
    demand(receipt["fixture_sha256"] == sha256(root / "synthetic_inputs.json"), "fixture hash")
    demand(receipt["raw_rows_sha256"] == sha256(raw_path), "raw row hash")
    demand(receipt["dependencies"] == freeze["dependencies"], "dependency receipt mismatch")
    demand(receipt["python"] == freeze["runtime"], "runtime receipt mismatch")
    demand(receipt["model_calls"] == freeze["model_budget"] == 0, "model budget")
    demand(receipt["external_inference_usd"] == freeze["external_inference_usd"] == 0,
           "external inference cost")
    demand(freeze["between_case_wall_budget_seconds"] == 600, "between-case budget")
    demand(timestamp(initial["created_utc"]) <= timestamp(freeze["created_utc"])
           < timestamp(guard["started_utc"]) <= timestamp(receipt["started_utc"])
           < timestamp(receipt["finished_utc"]), "saved chronology is inconsistent")
    demand(initial["files"].keys() == freeze["files"].keys(), "pre-execution manifest keys")
    amended = [path for path in initial["files"] if initial["files"][path] != freeze["files"][path]]
    demand(amended == ["run_validation.py"], "unexpected pre-execution amendment")
    for key in ("dependencies", "runtime", "model_budget", "external_inference_usd",
                "between_case_wall_budget_seconds"):
        demand(initial[key] == freeze[key], f"pre-execution metadata changed: {key}")

    demand(len(rows) == len(cases) == 148, "complete suite requires 148 saved rows")
    demand([row["id"] for row in rows] == [case["id"] for case in cases], "case order/IDs")
    demand(len({case["id"] for case in cases}) == 148, "duplicate case ID")
    demand(Counter(case["group"] for case in cases) ==
           {"small": 128, "shared": 8, "exact-scale": 12}, "group counts")
    demand(receipt["status"] == saved_summary["status"] == "complete", "incomplete run")
    demand(all(not (root / "results" / name).exists()
               for name in ("error.json", "freeze_error.json")), "run contains failure receipt")

    references = expectations = grids = 0
    understated = []
    conics = []
    ratios = []
    maximum_bits = 0
    for case, row in zip(cases, rows):
        d, v, risk, bits = audit_certificate(case, row)
        maximum_bits = max(maximum_bits, bits)
        for flag, key in (("reference", "reference_risk"), ("expectation", "expectation_risk"),
                          ("grid", "grid_risk"), ("conic", "conic")):
            demand(type(case[flag]) is bool and case[flag] == (key in row),
                   f"{case['id']}: expected method presence {flag}")
        if case["reference"]:
            demand(rational(row["reference_risk"]) == risk and row["reference_match"] is True,
                   f"{case['id']}: saved reference value mismatch")
            demand(row["reference_faces"] == 3 ** len(d), f"{case['id']}: reference face count")
            number(row["reference_seconds"], "reference duration")
            references += 1
        if case["expectation"]:
            demand(rational(row["expectation_risk"]) == risk and row["expectation_match"] is True,
                   f"{case['id']}: saved expectation value mismatch")
            number(row["expectation_seconds"], "expectation duration")
            expectations += 1
        if case["grid"]:
            grid = rational(row["grid_risk"])
            demand(0 <= grid <= risk, f"{case['id']}: invalid saved grid value")
            number(row["grid_seconds"], "grid duration")
            grids += 1
            if grid < risk:
                understated.append(case["id"])
        if case["conic"]:
            checked = audit_conic(row, d, v, risk)
            conics.append(checked)
            if case["group"] == "shared" and checked["accepted"]:
                denominator = row["exact_seconds"] + row["check_seconds"]
                demand(denominator > 0, "zero exact-plus-check time")
                ratios.append(checked["elapsed"] / denominator)
    demand((references, expectations, grids, len(conics)) == (128, 16, 64, 56),
           "declared method budgets not represented")
    ordered = sorted(ratios)
    median = ((ordered[3] + ordered[4]) / 2) if len(ordered) == 8 else None
    errors = [record["error"] for record in conics if record["error"] is not None]
    recomputed = {
        "status": "complete", "completed_cases": len(rows), "certificates_valid": len(rows),
        "reference_matches": references, "expectation_matches": expectations,
        "grid_cases": grids, "grid_understatements": len(understated),
        "conic_cases": len(conics), "conic_actual_calls": sum(c["calls"] for c in conics),
        "conic_numerically_accepted": sum(c["accepted"] for c in conics),
        "conic_risk_agreements_1e_7": len(errors) == len(conics) and all(e <= 1e-7 for e in errors),
        "conic_max_abs_risk_error": max(errors) if errors else None,
        "shared_time_ratios": ratios, "shared_median_time_ratio": median,
        "correctness_gate": True,
        "operational_value_gate": bool(understated and median is not None and median >= 2),
        "maximum_certificate_rational_bits": maximum_bits,
    }
    for key, expected in recomputed.items():
        actual = saved_summary[key]
        if isinstance(expected, list):
            demand(len(actual) == len(expected), f"summary length: {key}")
            for observed, calculated in zip(actual, expected):
                close(observed, calculated, f"summary: {key}")
        elif isinstance(expected, float):
            close(actual, expected, f"summary: {key}", atol=1e-18)
        else:
            demand(actual == expected, f"summary differs: {key}")

    evidence_files = ["freeze.json", "freeze.preexecution.json", "synthetic_inputs.json",
                      "results/rows.jsonl", "results/summary.json", "results/receipt.json",
                      "results/RUN_GUARD.json"]
    return {
        "status": "PASS", "audited_utc": datetime.now(timezone.utc).isoformat(),
        "checker_sha256": sha256(Path(__file__)), "checker_runtime": sys.version,
        "checker_platform": platform.platform(), "post_run_checker": True,
        "frozen_files_unchanged": len(freeze["files"]), "preexecution_changed_files": amended,
        "saved_chronology_consistent": True,
        "recorded_run_wall_seconds": number(receipt["wall_seconds"], "recorded run wall time"),
        "deadline_semantics": "600 seconds checked between cases; not a hard mid-method limit",
        "evidence_sha256": {path: sha256(root / path) for path in evidence_files},
        "recomputed_summary": recomputed, "grid_understatement_case_ids": understated,
        "estimator_moment_checks": len(rows), "new_solver_calls": 0,
        "new_reference_enumerations": 0, "new_grid_searches": 0,
        "new_binomial_outcome_enumerations": 0,
        "evidence_limits": [
            "Saved upper/lower certificates are independently verified; no solver is rerun.",
            "Saved reference, grid and full-outcome values are compared but not re-enumerated.",
            "Timing ratios are recalculated from saved durations, not independently remeasured.",
            "Reported solver calls and dependency identities are checked for consistency, not attested execution.",
            "Local hashes and saved timestamps are integrity/consistency records, not external timestamp attestations.",
            "No statistical deployment, hardware, patent novelty or model-performance claim follows from this replay.",
        ],
    }


def markdown(report):
    summary = report["recomputed_summary"]
    return "\n".join([
        "# Independent saved-evidence review", "", f"Status: {report['status']}.",
        f"Audit UTC: {report['audited_utc']}.", "",
        "A standalone standard-library checker read the saved fixture, raw result rows,",
        "manifests, guard and receipts. It imported none of the oracle, reference, original",
        "certificate checker, runner or conic baseline modules.", "",
        f"- {report['frozen_files_unchanged']} operative frozen files match their hashes.",
        "- The retained initial manifest differs only for the runner; saved timestamps place",
        "  its replacement before the recorded execution. This is local evidence consistency.",
        f"- {summary['certificates_valid']} exact upper/lower certificates and estimator moments pass.",
        f"- {summary['reference_matches']} saved reference values and {summary['expectation_matches']} saved full-outcome values agree.",
        f"- {summary['grid_understatements']} of {summary['grid_cases']} saved grid values understate the certified continuous risk.",
        f"- {summary['conic_cases']} conic records contain {summary['conic_actual_calls']} reported solver calls;",
        f"  {summary['conic_numerically_accepted']} numerical acceptances and errors were independently recomputed.",
        f"- Maximum absolute conic risk difference: {summary['conic_max_abs_risk_error']:.17g}.",
        f"- Median saved shared-case time ratio: {summary['shared_median_time_ratio']:.12g}.",
        "", "No optimization, face enumeration, grid search, model call or full binomial",
        "outcome enumeration was repeated. This checker was created after the recorded run;",
        "it is an independent saved-evidence replay, not part of the original frozen solver.",
        "", "## Evidence limits", "",
        *[f"- {limit}" for limit in report["evidence_limits"]], "",
        "The frozen protocol contains both a between-case rule and wording about a next",
        "operation. The actual runner checks before cases and completes the current case;",
        "600 seconds is not a hard mid-method deadline. The saved run finished below it.",
        "Exact timing includes estimator parameter construction while the conic solve receives",
        "constructed d,v; these are not identical timed boundaries. This disadvantages the",
        "exact method in the saved ratio but does not establish results on other hardware.", "",
    ])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--markdown-out", type=Path)
    args = parser.parse_args()
    try:
        report = audit(args.root)
    except (AuditFailure, KeyError, ValueError, TypeError, OSError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, sort_keys=True))
        return 1
    rendered = json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n"
    if args.json_out:
        args.json_out.write_text(rendered, encoding="utf-8")
    if args.markdown_out:
        args.markdown_out.write_text(markdown(report), encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
