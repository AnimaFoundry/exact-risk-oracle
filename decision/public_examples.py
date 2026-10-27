"""Original bounded verification of a cited public teaching example.

SPDX-License-Identifier: MIT. No course source or implementation is copied.
Known-example verification and a denominator erratum, not novel mathematics or
part of the new synthetic sampling-decision cohort. Run once; verify saved
certificates without another oracle or reference call.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import json
from math import comb
from pathlib import Path
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "public_examples_protocol.json"
RESULT = HERE / "public_examples_result.json"
GUARD = HERE / "public_examples_guard.json"


def utc():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, obj, exclusive=False):
    with path.open("x" if exclusive else "w", encoding="utf-8", newline="\n") as out:
        json.dump(obj, out, indent=2, sort_keys=True)
        out.write("\n")


def polynomial(n, shift):
    """Coefficients [constant, linear, quadratic] from E[X] and Var[X]."""
    denominator = F(n + 2 * shift)
    slope = F(n) / denominator
    bias_constant = F(shift) / denominator
    bias_slope = slope - 1
    variance_factor = F(n) / denominator**2
    return (bias_constant**2,
            variance_factor + 2 * bias_constant * bias_slope,
            -variance_factor + bias_slope**2)


def polynomial_maximum(coefficients):
    c, b, a = coefficients
    points = [F(0), F(1)]
    if a < 0:
        vertex = -b / (2 * a)
        if 0 <= vertex <= 1:
            points.append(vertex)
    scored = [(c + b * p + a * p * p, p) for p in points]
    maximum = max(value for value, _ in scored)
    return maximum, min(p for value, p in scored if value == maximum)


def outcome_risk(n, shift, p):
    """Enumerate outcomes directly; does not reuse the risk polynomial."""
    denominator = n + 2 * shift
    total = F(0)
    for count in range(n + 1):
        mass = comb(n, count) * p**count * (1 - p)**(n - count)
        estimate = F(count + shift, denominator)
        total += mass * (estimate - p)**2
    return total


def check_protocol():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    for rel, expected in protocol["frozen_sha256"].items():
        if sha(ROOT / rel) != expected:
            raise ValueError("Frozen source mismatch: " + rel)
    if protocol["budget"] != {
        "oracle_calls": 2, "face_reference_calls": 2,
        "direct_outcome_terms": 170, "model_calls": 0,
        "external_inference_usd": 0, "between_case_seconds": 60,
    }:
        raise ValueError("Unexpected public-example budget")
    if len(protocol["cases"]) != 2:
        raise ValueError("Expected exactly two public examples")
    return protocol


def run():
    protocol = check_protocol()
    if RESULT.exists() or GUARD.exists():
        raise RuntimeError("Public-example cohort already started; use --verify")
    started_utc = utc()
    save(GUARD, {"started_utc": started_utc,
                 "protocol_sha256": sha(PROTOCOL),
                 "budget": protocol["budget"]}, exclusive=True)
    sys.path.insert(0, str(ROOT))
    from oracle import from_estimator
    from reference import maximize_reference
    from check_certificate import verify
    started = perf_counter()
    output = {
        "status": "running", "started_utc": started_utc,
        "protocol_sha256": sha(PROTOCOL), "source": protocol["source"],
        "rows": [], "oracle_calls": 0, "face_reference_calls": 0,
        "direct_outcome_terms": 0, "model_calls": 0,
        "external_inference_usd": 0,
        "interpretation": "Known public examples and a formula erratum; no new theorem, benchmark, or synthetic decision-case result",
    }
    try:
        for case in protocol["cases"]:
            if perf_counter() - started >= 60:
                raise TimeoutError("Between-case time budget reached")
            n, shift = case["count"], case["symmetric_pseudocount"]
            a = F(n, n + 2 * shift)
            coefficients = polynomial(n, shift)
            analytical_maximum, analytical_p = polynomial_maximum(coefficients)
            if list(map(str, coefficients)) != case["expected_polynomial"]:
                raise AssertionError("Predeclared polynomial mismatch")
            if analytical_maximum != F(case["expected_worst_risk"]):
                raise AssertionError("Predeclared maximum mismatch")
            output["oracle_calls"] += 1
            d, v, certificate = from_estimator([1], [n], [a])
            output["face_reference_calls"] += 1
            reference = maximize_reference(d, v)
            if not verify(d, v, certificate.to_dict()):
                raise AssertionError("Certificate rejected")
            if certificate.risk != analytical_maximum or reference.risk != analytical_maximum:
                raise AssertionError("Exact risk disagreement")
            diagnostics = []
            for raw_p in protocol["diagnostic_probabilities"]:
                p = F(raw_p)
                output["direct_outcome_terms"] += n + 1
                direct = outcome_risk(n, shift, p)
                poly = coefficients[0] + coefficients[1] * p + coefficients[2] * p**2
                if direct != poly:
                    raise AssertionError("Direct expectation mismatch")
                diagnostics.append({"p": str(p), "risk": str(direct)})
            output["rows"].append({
                "id": case["id"], "count": n, "symmetric_pseudocount": shift,
                "coefficient": str(a), "d": list(map(str, d)), "v": list(map(str, v)),
                "polynomial": list(map(str, coefficients)),
                "analytical_worst_risk": str(analytical_maximum),
                "analytical_attaining_p": str(analytical_p),
                "certificate": certificate.to_dict(), "certificate_valid": True,
                "face_reference_risk": str(reference.risk),
                "faces_examined": reference.faces_examined,
                "diagnostics": diagnostics,
            })
        # The typo is nonlinear and outside the oracle contract. Its p=0 value
        # follows directly from a degenerate binomial X=0, with no solver call.
        typo_estimate = F(0 + 2, 0 + 4)
        output["typo_boundary"] = {
            "p": "0", "almost_sure_count": 0, "estimate": str(typo_estimate),
            "risk": str(typo_estimate**2), "oracle_called": False,
            "outside_centered_affine_contract": True,
        }
        if typo_estimate**2 != F(protocol["expected_typo_boundary_risk"]):
            raise AssertionError("Boundary expectation mismatch")
        check_protocol()
        output["status"] = "passed"
    except Exception as error:
        output.update(status="failed", error_type=type(error).__name__, error=str(error))
        raise
    finally:
        output["elapsed_seconds_after_imports"] = perf_counter() - started
        output["ended_utc"] = utc()
        output["frozen_sha256_after"] = {rel: sha(ROOT / rel) for rel in protocol["frozen_sha256"]}
        save(RESULT, output, exclusive=True)
    return output


def verify_saved():
    """Recompute algebra and verify saved witnesses; no optimization calls."""
    protocol = check_protocol()
    output = json.loads(RESULT.read_text(encoding="utf-8"))
    guard = json.loads(GUARD.read_text(encoding="utf-8"))
    if not (protocol["frozen_utc"] <= guard["started_utc"] <= output["ended_utc"]):
        raise ValueError("Invalid freeze/run chronology")
    if output["status"] != "passed" or output["protocol_sha256"] != sha(PROTOCOL):
        raise ValueError("Incomplete or mismatched result")
    if guard["protocol_sha256"] != sha(PROTOCOL) or guard["started_utc"] != output["started_utc"]:
        raise ValueError("Guard mismatch")
    for name in ("oracle_calls", "face_reference_calls", "direct_outcome_terms", "model_calls", "external_inference_usd"):
        if output[name] != protocol["budget"][name]:
            raise ValueError("Budget mismatch: " + name)
    if output["source"] != protocol["source"] or output["frozen_sha256_after"] != protocol["frozen_sha256"]:
        raise ValueError("Source or frozen hashes mismatch")
    if len(output["rows"]) != len(protocol["cases"]):
        raise ValueError("Unexpected row count")
    sys.path.insert(0, str(ROOT))
    from check_certificate import verify
    for row, case in zip(output["rows"], protocol["cases"]):
        n, shift = case["count"], case["symmetric_pseudocount"]
        coefficients = polynomial(n, shift)
        maximum, pstar = polynomial_maximum(coefficients)
        a = F(n, n + 2 * shift)
        d, v = [1-a], [a*a/n]
        expected = {"id": case["id"], "count": n, "symmetric_pseudocount": shift,
                    "coefficient": str(a), "d": list(map(str, d)), "v": list(map(str, v)),
                    "polynomial": list(map(str, coefficients)), "analytical_worst_risk": str(maximum),
                    "analytical_attaining_p": str(pstar), "face_reference_risk": str(maximum),
                    "certificate_valid": True, "faces_examined": 3}
        if any(row[key] != value for key, value in expected.items()):
            raise ValueError("Saved row mismatch")
        if str(maximum) != case["expected_worst_risk"] or list(map(str, coefficients)) != case["expected_polynomial"]:
            raise ValueError("Expected formula mismatch")
        if not verify(d, v, row["certificate"]):
            raise ValueError("Saved certificate rejected")
        diagnostics = [{"p": p, "risk": str(outcome_risk(n, shift, F(p)))}
                       for p in protocol["diagnostic_probabilities"]]
        if row["diagnostics"] != diagnostics:
            raise ValueError("Saved outcome diagnostics mismatch")
    if output["typo_boundary"] != {"p": "0", "almost_sure_count": 0, "estimate": "1/2",
                                    "risk": "1/4", "oracle_called": False,
                                    "outside_centered_affine_contract": True}:
        raise ValueError("Typo boundary mismatch")
    return {"status": "saved_evidence_verified", "oracle_calls_this_verification": 0,
            "reference_calls_this_verification": 0, "result_sha256": sha(RESULT),
            "protocol_sha256": sha(PROTOCOL), "cases": 2}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--run", action="store_true")
    choice.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.run:
        result = run()
        print(json.dumps({"status": result["status"], "oracle_calls": result["oracle_calls"],
                          "result_sha256": sha(RESULT)}, sort_keys=True))
    else:
        print(json.dumps(verify_saved(), sort_keys=True))
