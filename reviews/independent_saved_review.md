# Independent saved-evidence review

Status: PASS.
Audit UTC: 2026-10-27T02:11:18.029342+00:00.

A standalone standard-library checker read the saved fixture, raw result rows,
manifests, guard and receipts. It imported none of the oracle, reference, original
certificate checker, runner or conic baseline modules.

- 11 operative frozen files match their hashes.
- The retained initial manifest differs only for the runner; saved timestamps place
  its replacement before the recorded execution. This is local evidence consistency.
- 148 exact upper/lower certificates and estimator moments pass.
- 128 saved reference values and 16 saved full-outcome values agree.
- 6 of 64 saved grid values understate the certified continuous risk.
- 56 conic records contain 54 reported solver calls;
  56 numerical acceptances and errors were independently recomputed.
- Maximum absolute conic risk difference: 1.2387751519016277e-09.
- Median saved shared-case time ratio: 29.8776198449.

No optimization, face enumeration, grid search, model call or full binomial
outcome enumeration was repeated. This checker was created after the recorded run;
it is an independent saved-evidence replay, not part of the original frozen solver.

## Evidence limits

- Saved upper/lower certificates are independently verified; no solver is rerun.
- Saved reference, grid and full-outcome values are compared but not re-enumerated.
- Timing ratios are recalculated from saved durations, not independently remeasured.
- Reported solver calls and dependency identities are checked for consistency, not attested execution.
- Local hashes and saved timestamps are integrity/consistency records, not external timestamp attestations.
- No statistical deployment, hardware, patent novelty or model-performance claim follows from this replay.

The frozen protocol contains both a between-case rule and wording about a next
operation. The actual runner checks before cases and completes the current case;
600 seconds is not a hard mid-method deadline. The saved run finished below it.
Exact timing includes estimator parameter construction while the conic solve receives
constructed d,v; these are not identical timed boundaries. This disadvantages the
exact method in the saved ratio but does not establish results on other hardware.
