# Pre-execution freeze revision

The first freeze was created before final reviewer feedback about exception
preservation. No validation case, reference comparison, grid, or formal conic
benchmark had run. The runner was amended to retain the current case ID and
partially completed row when an unexpected exception occurs. The initial freeze
is preserved as freeze.preexecution.json; freeze.json is the operative version.
No result or threshold was changed and no new input was generated.

Timing boundary disclosure: exact_seconds includes converting weights/counts/
coefficients into d,v; conic receives these already constructed vectors and its
timer excludes inexpensive input/type preparation. Imports are excluded from both.
This conservatively disadvantages the exact method, but the timings are not
identical instruction regions. Both receive the same mathematical problem.
