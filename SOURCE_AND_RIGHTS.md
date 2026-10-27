# Sources, rights, and contribution boundaries

Review date: 2026-10-27. This record concerns the original source package, its
synthetic examples, and the locally installed dependencies used for comparison.
It is a source and license inventory, not a freedom-to-operate opinion.

## Original material and publication scope

The oracle, independent certificate checker, independent reference calculation,
synthetic-input generator, conic-baseline wrapper, validation harness, tests, and
paper-building script were written for this study. The implementation is not a
copy of the cited authors' software. The independently formulated SOCP baseline
calls CVXPY and Clarabel; it does not import the production oracle or use its
breakpoint algorithm to supply a solver answer. The reference and certificate
checks have separate implementations, with their precise shared assumptions
described in the protocol and manuscript.

The package's original code, documentation, and original synthetic artifacts are
offered under the [MIT License](LICENSE), copyright 2026 AnimaFoundry. This does
not relicense the cited literature, dependency packages, fonts, or any third-party
material. The synthetic cases are mathematical inputs generated for this study;
they are not observations from people, production systems, or sensor deployments.
No private conversation, case summary, case counts, conversation link, unique
story, or user trace is included.

Only the final explicit publication allowlist may be released. The local `.deps/`
installation, caches, virtual environments, downloaded wheels, and full release
archives are outside the publication scope. The dependency packages listed below
are not vendored or redistributed in this source package. No external paper PDF,
figure, dataset, or source-code implementation is copied into it. References
identify antecedents; formulas and explanations are presented in newly written
form with attribution.

## Mathematical and algorithmic antecedents

The method concerns a fixed centered affine estimator, independent binomial
strata, and a specified continuous parameter box. It does not invent shrinkage
estimation, binomial minimax theory, diagonal loading, conic duality, scalar
breakpoint methods, or the general polynomial tractability of this quadratic
problem. Its bounded claim is a specialized exact rational implementation with
a separate, short optimality-certificate check and the computational comparisons
actually reported. The prior-art screen does not establish that this specialized
algorithm is unprecedented.

1. **Timothy Allen DeRouen (1971), _Bayes-suggested solutions in binomial
   estimation_.** Doctoral dissertation, Virginia Polytechnic Institute and
   State University. [Institutional record](https://vtechworks.lib.vt.edu/items/8918cc0e-bd2c-40d7-bc6c-3050761cb153).
   The recorded abstract establishes earlier work on symmetric-beta Bayes and
   minimax estimation of linear binomial combinations. The full dissertation
   was not successfully retrieved in this study's bounded review.
2. **T. A. DeRouen and T. J. Mitchell (1974), _A G1-Minimax Estimator for a
   Linear Combination of Binomial Probabilities_.** _Journal of the American
   Statistical Association_ 69(345), 231-233.
   DOI: [10.1080/01621459.1974.10480160](https://doi.org/10.1080/01621459.1974.10480160).
   The title, authors, journal, pages, and DOI were corroborated by discovery
   indexes. The [publisher page](https://www.tandfonline.com/doi/abs/10.1080/01621459.1974.10480160)
   returned HTTP 403 during this review; a Crossref lookup was also unavailable.
   Bibliographic corroboration must not be described as a full-text theorem
   review. No conclusion in this package depends on an uninspected theorem from
   that article.
3. **Sunyoung Kim and Masakazu Kojima (2003), _Exact Solutions of Some
   Nonconvex Quadratic Optimization Problems via SDP and SOCP Relaxations_.**
   _Computational Optimization and Applications_ 26(2), 143-154.
   DOI: [10.1023/A:1025794313696](https://doi.org/10.1023/A:1025794313696).
   The DOI and bibliographic details were checked against the
   [publisher's article page](https://link.springer.com/article/10.1023/A:1025794313696)
   and the [author-submitted primary entry](https://optimization-online.org/2002/04/467/).
   Existing SDP/SOCP exactness is a substantive baseline, not a result first
   established by this study. The precise nonpositive-linear-term boundary was
   checked through the explicit restatement in the 2026 manuscript below.
4. **Stephen Becker and M. Jalal Fadili (2012), _A Quasi-Newton Proximal
   Splitting Method_.** _Advances in Neural Information Processing Systems_ 25.
   [Primary preprint](https://arxiv.org/abs/1206.1156);
   [proceedings record](https://papers.neurips.cc/paper_files/paper/2012/hash/e034fb6b66aacc1d48f445ddfb08da98-Abstract.html).
   Diagonal-plus-rank-one proximal calculations and sorted piecewise-affine
   breakpoints predate this work. Their convex positive-definite-metric setting
   is distinct from the present nonconvex risk maximum; the distinction does
   not establish general algorithmic novelty.
5. **Samuel Burer, Karthik Natarajan, and Rick Willemsen, _On the Semidefinite
   Representability of Continuous Quadratic Submodular Minimization With
   Applications to Pricing and Moment Problems_.** The primary manuscript
   version reviewed in 2026 is available at
   [Optimization Online](https://optimization-online.org/wp-content/uploads/2025/04/submodular-1.pdf).
   Its Proposition 1 restates the relevant Kim-Kojima exactness case. Our
   minimization has `Q = Diag(v) - d d^T` and zero linear term, so it belongs
   to that known exact class. The broader arbitrary-linear-term problem must
   not be substituted for this special case when describing prior art.

The manuscript and mathematical review may cite further adjacent work. A
bibliographic reference neither grants permission to redistribute its full text
nor implies endorsement by its authors. No text or code from the cited papers is
claimed as AnimaFoundry's original intellectual contribution.

## Benchmark dependency inventory

The following entries were checked from the thirteen explicitly named local
`*.dist-info/METADATA` files under `.deps/`, using `Name`, `Version`,
`License-Expression`, `License`, license classifiers, and `Requires-Dist`.
This is installed-distribution metadata, not a source-code audit of every
transitive component. Optional extras listed in metadata were not treated as
installed dependencies. Package names and versions below identify the actual
local installation used for the conic comparison.

| Distribution | Version | Declared license in inspected metadata | Role |
| --- | --- | --- | --- |
| cvxpy | 1.7.3 | Apache License, Version 2.0 | Conic formulation/canonicalization |
| clarabel | 0.11.1 | Apache-2.0 | Executed SOCP solver |
| numpy | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | Numerical dependency; composite SPDX expression retained |
| scipy | 1.18.1 | BSD license text with three conditions; bundled-component notices below | Numerical dependency |
| cffi | 2.1.1 | MIT-0 | Foreign-function dependency |
| pycparser | 3.12 | BSD-3-Clause | cffi dependency |
| osqp | 1.1.3 | Apache-2.0 | Installed CVXPY dependency; not the selected benchmark solver |
| scs | 3.3.1 | MIT | Installed CVXPY dependency; not the selected benchmark solver |
| Jinja2 | 3.1.6 | OSI Approved BSD License classifier; exact variant not declared in METADATA | OSQP dependency |
| MarkupSafe | 3.0.4 | BSD-3-Clause | Jinja2 dependency |
| joblib | 1.6.0 | BSD-3-Clause | OSQP dependency |
| cloudpickle | 3.1.2 | BSD-3-Clause | joblib dependency |
| setuptools | 84.2.1 | MIT | Installed OSQP dependency/tooling |

SciPy's inspected metadata additionally names OpenBLAS under BSD-3-Clause,
LAPACK under BSD-3-Clause-Open-MPI, and the GCC runtime library under
GPL-3.0-or-later WITH GCC-exception-3.1. These notices are retained here instead
of describing the entire binary distribution as a single BSD component.
NumPy's composite expression is likewise not shortened to BSD alone. The
Jinja2 metadata classifier is recorded as given, without inventing a more
specific SPDX identifier.

Every listed distribution remains a separately installed dependency governed by
its own license. The package's MIT license does not replace those licenses.
Because their code/binaries are not redistributed here, this package does not
vendor their complete license trees. Any future wheel bundle, container image,
or executable redistribution needs a fresh inventory of the files actually
included, with the corresponding license texts and notices.

## PDF construction and font notice

The paper builder uses the separately installed ReportLab distribution and its
Bitstream Vera font files. The source package contains the full font notice in
[FONT-LICENSE.txt](FONT-LICENSE.txt); the builder loads the installed fonts and
embeds subsets in the generated PDF. Font binaries are not copied into the
source package. The notice includes the original copyright, permissions,
conditions, and disclaimer; it is not replaced by the package's MIT license.

The following three named installed METADATA files were separately inspected
through the paper-building interpreter. Its distributions resolve to the bundled
runtime's site-packages, rather than the package's `.deps/` directory. No broader
runtime directory scan or source-package/archive read was performed.

| Build distribution | Version | Declared license in inspected METADATA | Role |
| --- | --- | --- | --- |
| reportlab | 4.4.9 | BSD license declaration/classifier; exact variant not specified in METADATA | PDF construction |
| pillow | 12.3.0 | MIT-CMU | ReportLab dependency |
| charset-normalizer | 3.5.2 | MIT | ReportLab dependency |

ReportLab's declared required dependencies are Pillow and charset-normalizer;
its optional accelerator, renderer, bidirectional-text and shaping extras are
not asserted to have been used. These build distributions are not vendored or
relicensed. The separately reproduced Vera font notice covers the font material
used in the PDF. A reproducible build receipt should additionally preserve the
interpreter and platform versions, exact input hashes, and final PDF hash.

## Unresolved legal and evidential limits

This review did not perform a patent claim chart, jurisdiction-specific patent
search, or professional legal analysis. A permissive software license is not a
license to third-party patents. Neither the limited prior-art search nor a
passing mathematical/computational check establishes patent novelty,
patentability, freedom to operate, or absence of future disputes. A concrete
source-rights dispute or identified conflicting patent claim requires focused
review before releasing the affected functionality.

No new model inference, benchmark execution, or rerun was performed as part of
this rights review. Mathematical correctness, benchmark validity, release
verification, and source rights are separate checks; one does not substitute
for the others.
