# Exact Worst-Case Risk Certificates for Stratified Bernoulli Estimation

## A Rational Breakpoint Method with Independently Checkable Witnesses

AnimaFoundry Research | Original methods manuscript | 27 October 2026

Version 1.0.0. Not peer reviewed. Original implementation, mathematical derivation, and synthetic verification. No claim of patent novelty, first-ever conic tractability, hardware validation, or improved statistical estimation.

## Abstract

Evaluating an estimator on a finite parameter grid can understate its continuous worst-case risk. We develop a compact certifying implementation for a specified class of fixed, centered affine estimators of weighted independent binomial probabilities, including unobserved strata. The risk reduces to a rank-one-coupled box quadratic. A rational breakpoint sweep computes an attaining parameter witness in O(k log k) arithmetic operations. A separate O(k) verifier checks a diagonal-majorizer upper bound and equality at that witness, without repeating or trusting the search. The estimator family, relevant conic exactness, and one-dimensional breakpoint techniques have substantial prior art; the contribution is their explicit, executable specialization with exact rational certificates and boundary handling. A frozen original suite produced 148 valid certificates, 128 exact matches with independently implemented face enumeration, and 16 matches with direct binomial expectation. Six of 64 coarse grids understated risk. An independently formulated CVXPY/Clarabel baseline agreed numerically on all 56 compared inputs. On eight shared scale cases, the median ratio of general conic end-to-end time to exact solving plus checking was 29.88, in one Windows run. This is a finite implementation comparison, not a universal solver speed claim. No model calls, private data, or external inference fees were used.

**Keywords:** worst-case risk; stratified estimation; binomial probabilities; exact arithmetic; certificate verification; structured quadratic optimization; missing strata.

## 1. Motivation and contribution boundary

A sensing or sampling design can leave some strata unobserved. Its quality then depends not only on which states are covered, but also on the estimator and its uncertainty treatment. A finite risk grid is convenient, yet a reassuring grid maximum is only a lower bound on the continuous maximum. Increasing grid density raises computation cost without, by itself, producing an exact certificate.

The engineering question addressed here is narrow: can a user evaluate a fixed estimator over every admissible probability vector and receive a small mathematical certificate that a different program can verify? We do not choose a sampling policy, estimate unknown state frequencies, or infer missingness assumptions from data. A result is conditional on the statistical contract supplied by the user.

The original deliverable has three parts: an exact rational sweep, an attaining probability vector, and a verifier using a different proof route. It makes a known tractable structure directly usable without a general optimization dependency in the production solver. Independent value is evaluated against both a complete exact reference and an established numerical conic formulation. A coarse grid is included to illustrate a practical failure mode, not to serve as the strongest baseline.

This is an invention-style method specification in the sense of a concrete mechanism, executable prototype, proof, and falsifiers. It is not a determination of patentability or evidence that no equivalent algorithm exists. The reviewed literature already rules out broad novelty claims about minimax binomial estimation, conic exactness, and sorted breakpoints.

## 2. Established antecedents

DeRouen's dissertation and the DeRouen-Mitchell report studied estimation of linear combinations of binomial probabilities using symmetric-beta Bayes estimators and minimax criteria [1,2]. Their subsequent article makes the historical proximity explicit [3]. Therefore shrinkage for unbalanced binomial strata is not introduced here. We inspected the dissertation abstract and relevant primary report pages; the publisher full text of [3] was inaccessible, so no uninspected theorem is attributed to it.

The quadratic in this paper is also inside an established optimization class. Kim and Kojima obtained exact SDP/SOCP relaxations for certain nonconvex quadratic problems [4]. The explicit restatement by Burer, Natarajan, and Willemsen covers submodular box minimization with a nonpositive linear term [5]. Our matrix is Diag(v)-dd^T, whose off-diagonal entries are nonpositive, and its linear term is zero. We therefore do not claim newly discovered polynomial solvability. The broader arbitrary-linear-term case in [5] must not be conflated with this special case.

Becker and Fadili's diagonal-plus-rank-one proximal calculus uses one-dimensional, piecewise-linear structure and sorted breakpoints [6]. Its convex metric setting differs from the present box maximum, but the general pattern of scalar reduction and sorting is prior art. Hladik, Cerny, and Rada provide another adjacent exact method for fixed-rank box quadratics [7]; our full matrix may have full rank because of its diagonal term. None of these distinctions proves absence of an earlier equivalent specialization.

The bounded search supports a carefully delimited methods contribution: an explicit rational certificate-producing implementation, its statistical contract, independent verification, and measured cost on disclosed instances. It does not establish a first-ever algorithm or freedom to operate.

## 3. Statistical contract and risk identity

Let there be k strata with known weights w_i >= 0 and sum_i w_i = 1. For each observed stratum, K_i is independently Binomial(n_i,p_i), with fixed integer n_i > 0 and unknown p_i in [0,1]. An unobserved stratum has n_i = 0. The target is the population quantity theta = sum_i w_i p_i, not a realized finite-sample mean.

Fix coefficients 0 <= a_i <= w_i, requiring a_i = 0 when n_i = 0. Define the centered affine estimator

    T = 1/2 + sum_{i:n_i>0} a_i (K_i/n_i - 1/2).

Counts and coefficients must not be selected using the same observed outcomes unless a separate valid conditional model justifies the identity below. Adaptive stopping, correlated strata, unknown weights, and non-binomial outcomes are outside the certified statistical contract.

Set d_i = w_i-a_i, v_i = a_i^2/n_i for n_i > 0 and v_i = 0 otherwise, and x_i = 2p_i-1. Bias-variance decomposition gives the exact identity

    4 E_p[(T-theta)^2] = sum_i v_i + q(x),
    q(x) = (sum_i d_i x_i)^2 - sum_i v_i x_i^2.                 (1)

The bias is -(d^T x)/2 and the variance is sum_i v_i(1-x_i^2)/4. Since d_i >= 0, replacing x by its componentwise absolute value cannot decrease q. Thus maximizing over [-1,1]^k is equivalent to maximizing over [0,1]^k. The implementation also exposes this nonnegative d,v quadratic directly.

Zero samples do not imply a known zero probability. They produce a_i=v_i=0 with d_i=w_i, retaining uncertainty about that stratum. When all coefficients are zero, T=1/2 and the continuous worst risk is 1/4.

## 4. Rational breakpoint solution

Let D=sum_i d_i. The identity y^2=max_t(2ty-t^2) yields

    max_x q(x) = max_{0<=t<=D} g(t),
    g(t) = -t^2 + sum_i max_{0<=x_i<=1}(2td_i x_i-v_i x_i^2).  (2)

For d_i,v_i>0, the inner maximizer is x_i(t)=min(td_i/v_i,1), with breakpoint b_i=v_i/d_i. A coordinate with v_i=0<d_i is saturated for positive t. Coordinates with d_i=0 can use x_i=0.

For the unsaturated set U and saturated set S, write A=sum_U d_i^2/v_i and C=sum_S d_i. Within a breakpoint interval,

    g'(t)/(2t) = A + C/t - 1,                                (3)

for t>0. This expression is continuous and nonincreasing across the entire positive range. Once positive mass is saturated it is strictly decreasing. Consequently there are no separated local maxima to search.

If there is no coordinate v_i=0<d_i and A_0=sum_{v_i>0}d_i^2/v_i <= 1, return t=0 and x=0. Equality permits an initial flat region, but zero is a valid maximizer. Otherwise the positive root obeys

    sum_{i:d_i>0} d_i^2 / max(v_i,td_i) = 1.                 (4)

Sort positive b_i. In each interval with A<1, the possible root is t=C/(1-A); retain it if it lies inside the interval. Otherwise process the next group of equal breakpoints by subtracting d_i^2/v_i from A and adding d_i to C. After all breakpoints, A=0 and t=D is available. Exact rational comparisons handle roots at breakpoints without tolerances.

Sorting costs O(k log k) comparisons; the sweep and construction cost O(k) arithmetic operations. These are not O(k log k) bit-operation bounds. Fractions may grow with input bit length and dimension; exact gcd, multiplication, division and comparisons are not constant-time operations. The validation records certificate numerator/denominator bit lengths.

## 5. Independent certificate and proof

The solver returns a feasible x and nonnegative diagonal loading lambda. The verifier ignores the solver's root and interval metadata. It accepts only if, with B_i=v_i+lambda_i,

    B_i=0 implies d_i=0;
    sum_{i:B_i>0} d_i^2/B_i <= 1;
    |x_i| <= 1 for every i;
    q(x) = sum_i lambda_i.                                 (5)

**Theorem 1 (certificate soundness).** Conditions (5), nonnegative lambda, and nonnegative v prove that q(x) is the global maximum over [-1,1]^k.

**Proof.** For any feasible y, weighted Cauchy-Schwarz gives

    (d^T y)^2 <= (sum d_i^2/B_i)(sum B_i y_i^2)
              <= sum B_i y_i^2.

Subtracting sum v_i y_i^2 yields q(y)<=sum lambda_i y_i^2<=sum lambda_i. The reported feasible x attains that bound by (5). Hence the lower and upper bounds coincide. Zero B_i terms are harmless because their d_i are zero. This proof does not depend on the breakpoint algorithm. QED.

**Theorem 2 (certificate construction).** For a positive root of (4), let lambda_i=max(td_i-v_i,0), and x_i=td_i/B_i when B_i>0, otherwise zero. These values satisfy (5). In the zero-root case, x=lambda=0 is valid.

**Proof.** Equation (4) gives sum d_i^2/B_i=1 and d^T x=t. The witness lies in [0,1]^k. Cauchy-Schwarz is attained because x_i=td_i/B_i. Every positive loading has x_i=1, making the box-bound inequality tight. In the zero-root case the ratio is at most one and q(0)=0. QED.

The verifier requires O(k) exact operations and no optimization library. It checks the risk reported in (1) as well as the objective. Deliberately altered bounds and nonattaining witnesses are rejected in development tests. Metadata such as elapsed time is not mathematically certified.

The certificate is a specialization of diagonal-majorizer/conic reasoning, not a new general duality theorem. It certifies this input's algebra, not the truth of independence, the provenance of counts, or deployment safety.

## 6. Validation design and falsifiers

The protocol, input JSON, generator, implementations and tests were hashed before the formal run. A first pre-execution freeze was superseded solely to preserve a partial row on an unexpected exception; both freezes are retained. No benchmark outcome had been evaluated. Development toys were separated from the new deterministic synthetic suite.

The suite contains 128 small instances, eight shared scale instances and 12 larger exact-only instances. Small instances use k=1..6, normalized positive integer weights, zero or small integer counts, and coefficients chosen from 0,1/4,1/2,3/4,1 times the weight. The first 16 use counts at most three for full outcome enumeration. The first 64 have k<=5 for complete five-point parameter grids. Scale instances have uniform weights and independently generated count/coefficient combinations; they are not claims about natural data distributions.

The exact reference independently enumerates every 0/free/1 face of [0,1]^k and solves its stationary linear equations using rational Gaussian elimination. Singular stationary faces can be skipped: moving along a Hessian null direction preserves the objective until a smaller face is reached; repeated reduction reaches a vertex or a nonsingular stationary face. This gives a complete small-dimensional reference without reproducing the scalar algorithm.

The maintained strong baseline is CVXPY 1.7.3 with Clarabel 0.11.1, independently minimizing sum lambda subject to lambda>=0 and sum d_i^2/(v_i+lambda_i)<=1. It normalizes from input magnitudes, uses 1e-10 solver tolerances and at most 200 iterations, and never retries. Numerical residual acceptance and absolute risk error <=1e-7 are diagnostics, not exact proofs. An all-zero d input is explicitly solved algebraically with no conic call.

The declared budget was 148 exact calls, 128 reference calls, 64 grids, 16 direct expectations and at most 56 conic calls, with a 600-second between-case stop rule. The guard prevents accidental replay of the recorded matrix. Saved certificates may be independently checked without rerunning optimization. No model inference, private case, or external API expenditure is part of the experiment.

Any exact mismatch defeats correctness. The operational gate additionally requires at least one understated grid and a median conic/exact-plus-check time ratio of at least two on the eight shared scale cases. Discovery of an equivalent earlier specialization defeats an algorithmic novelty claim, regardless of this test outcome. Violating the statistical contract defeats an application claim even if the algebraic checker accepts.

## 7. Results

The single formal Windows run began at 2026-10-27T02:07:26.067319Z and finished at 02:07:30.955709Z. Measured wall time after imports was 4.877 seconds, on Python 3.12.14 and Windows 11. All 148 cases completed; all operative frozen hashes remained unchanged. The development suite contained 25 passing test methods. The following figures refer to one generated suite and one timed call per method/input.

| Check | Result | Interpretation |
|---|---|---|
| Independent exact certificate conditions | 148/148 | Attained global bounds under the stated algebra |
| Exhaustive face reference equality | 128/128 | Independent small-instance optimum agreement |
| Direct binomial expectation equality | 16/16 | Risk identity checked without reusing its formula |
| Coarse grids understating continuous risk | 6/64 | A finite grid is not always a full-domain certificate |
| Conic numerical acceptance | 56/56 | Includes two algebraic zero-d cases; 54 actual solves |
| Maximum absolute conic risk discrepancy | 1.239e-9 | Below the declared 1e-7 agreement threshold |

The maximum grid gap was approximately 0.001772 in squared-error risk, at input small-056. This is not an estimate of how often real applications fail. A disclosed development example has w=(1/2,1/2), n=(1,1), and a=(1/3,1/6). Its true worst risk is 7/108 at p=(5/6,1), whereas the quarter grid yields 37/576, understating by exactly 1/1728.

| Shared dimension k | Exact solve, median ms | Check, median ms | General conic, median ms |
|---|---|---|---|
| 16 | 0.236 | 0.241 | 15.707 |
| 32 | 0.450 | 0.331 | 30.586 |
| 64 | 1.331 | 0.945 | 61.038 |
| 256 | 4.548 | 2.540 | 200.191 |

Each row summarizes two distinct inputs. Across the eight individual ratios, the median was 29.88, with range 20.90-47.59. The exact time includes constructing d,v from the statistical input; the conic baseline receives those vectors and excludes initial type preparation. Imports are excluded from both. Conic time includes expression construction, canonicalization, solve and residual evaluation. Solver-reported internal time is separately retained. These timings support a one-shot implementation advantage over this baseline; they do not show that the numerical cone solver's internal iterations are intrinsically slower, nor compare warm cached programs, alternative formulations, or other solvers.

The exact-only extension reached k=16,384, with median solve/check times of 371.534/231.331 ms across two cases. No conic comparison was performed at those sizes. The maximum numerator or denominator length among saved certificate components was 41 bits. Larger or adversarial rational inputs may cost substantially more.

Both prospective correctness and operational gates passed. The ordinary conic baseline also succeeded; there was no solver failure to exploit. The contribution is the combination of exact output, a directly checkable attaining witness, and low overhead within this specified family, not a new statistical performance advantage.

## 8. Limitations and research opportunities

First, the proof is conditional. Outcome-dependent sampling, uncertain weights, cross-stratum dependence, asymmetric shrinkage, or a loss other than squared error requires a different derivation. A missingness mechanism can invalidate the binomial contract without triggering the checker. Second, timings are a small one-machine engineering observation, not a repeated performance study. The conic baseline was not tuned using benchmark outcomes, and optimized cached/vectorized implementations remain untested. Third, certificate bit growth is underexplored. Fourth, the bounded literature screen does not establish unprecedented invention.

The most valuable next experiment is a fresh, prespecified design-selection task: compare sampling allocations chosen using coarse-grid risk, the exact certificate, and a reusable conic baseline under the same exogenous energy model and observation budget. A useful decision contribution requires better risk choices, not merely a different numerical maximum. If all chosen allocations coincide, the decision-level value claim fails even though the oracle remains correct. Any such experiment is NOT PERFORMED here.

A second extension would seek tractable certificates for asymmetrically centered affine estimators. A linear term can change the optimization structure; the present theorem must not be silently generalized. A third would benchmark high-bit rational inputs and warm reusable conic programs. If equivalent exact certificates at comparable cost are already provided by a maintained solution, an independent software product may be unnecessary.

## 9. Reproducibility, authorship, and rights

The package provides original source, frozen synthetic inputs, full exact certificates, numerical baseline records, the two pre-execution freeze records, and a guarded runner. The solver and checker use only the Python standard library; optional conic dependencies are needed only to reproduce the numerical benchmark. The manuscript PDF is generated from this Markdown with a deterministic local ReportLab builder and a separately retained font license.

AnimaFoundry supplied the research direction and publication authorization. An AI research agent developed the mechanism, code and prose, with separate AI-agent mathematical, implementation and saved-evidence reviews. Those checks are internal verification, not independent institutional replication or peer review. No human, biological, hardware or trained-model experiment was performed. The three earlier model queues were not reopened. Private conversations and their distinctive case data are excluded.

The production code and original documents are released under the accompanying MIT license; third-party dependencies remain under their own licenses and are not vendored. Citations acknowledge mathematical antecedents. An open-source license does not grant rights under unrelated third-party patents. The package makes no FTO, patentability, novelty-certification or zero-dispute promise.

## References

[1] T. A. DeRouen. Bayes-suggested solutions in binomial estimation. Doctoral dissertation, Virginia Polytechnic Institute and State University, 1971. Institutional abstract: https://vtechworks.lib.vt.edu/items/8918cc0e-bd2c-40d7-bc6c-3050761cb153

[2] T. A. DeRouen and T. J. Mitchell. Estimation of a Linear Combination of Binomial Probabilities. In Mathematics Division Annual Progress Report for Period Ending December 31, 1971, ORNL-4761, pp. 131-133, April 1972. https://digital.library.unt.edu/ark:/67531/metadc1032271/m2/1/high_res_d/4504208.pdf

[3] T. A. DeRouen and T. J. Mitchell. A G1-Minimax Estimator for a Linear Combination of Binomial Probabilities. Journal of the American Statistical Association 69(345), 231-233, 1974. https://doi.org/10.1080/01621459.1974.10480160

[4] S. Kim and M. Kojima. Exact Solutions of Some Nonconvex Quadratic Optimization Problems via SDP and SOCP Relaxations. Computational Optimization and Applications 26(2), 143-154, 2003. https://doi.org/10.1023/A:1025794313696 . Primary author record: https://optimization-online.org/2002/04/467/

[5] S. Burer, K. Natarajan, and R. Willemsen. On the Semidefinite Representability of Continuous Quadratic Submodular Minimization With Applications to Pricing and Moment Problems. March 2026, revised September 2026. https://optimization-online.org/wp-content/uploads/2025/04/submodular-1.pdf

[6] S. Becker and M. J. Fadili. A Quasi-Newton Proximal Splitting Method. Advances in Neural Information Processing Systems 25, pp. 2627-2635, 2012. https://arxiv.org/abs/1206.1156

[7] M. Hladik, M. Cerny, and M. Rada. A New Polynomially Solvable Class of Quadratic Optimization Problems with Box Constraints. Optimization Letters 15, 2331-2341, 2021. https://doi.org/10.1007/s11590-021-01711-6 . Author preprint: https://arxiv.org/abs/1911.10877
