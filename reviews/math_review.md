# Mathematical and prior-art review: exact affine-binomial risk oracle

Date: 2026-10-27. Status: mathematical review and bounded prior-art screen; no code, experiment, model call, runtime benchmark, or new empirical result was performed by this reviewer. This is a new proposed method problem. The completed `energy_missingness_audit` remains a negative finite audit and its cases are not a fresh evaluation set.

## Assessment

A defensible narrow contribution is an exact rational breakpoint algorithm and independently checkable certificate for the continuous-box worst-case squared-error risk of a **fixed** centered affine estimator of a weighted sum of independent binomial probabilities. The calculation requires O(k log k) rational comparisons/arithmetic operations, followed by an O(k) arithmetic certificate check. These are arithmetic-operation counts, not bit-operation bounds.

The estimator class, minimax estimation of binomial combinations, polynomial solvability of the underlying special quadratic program, and SDP/SOCP certification are established topics. Do not describe those as inventions. The potential contribution is the specialized implementation, direct certificate, transparent treatment of absent strata, and demonstrated computational or certification benefit. The bounded search did not establish that this specialized algorithm is unprecedented. The result can support a methods manuscript without a first-ever or patent-novelty claim.

## Statistical contract and exact risk

Let k strata have fixed counts n_i >= 0, known weights w_i >= 0 summing to one, independent K_i ~ Binomial(n_i, p_i) for n_i > 0, and p_i in [0,1]. The estimand is theta = sum_i w_i p_i. Counts and coefficients must not depend on observed outcomes; a calendar can determine counts only under a stated exogenous/conditional independence model.

Fix rational coefficients 0 <= a_i <= w_i, with a_i = 0 if n_i = 0, and use

    T = 1/2 + sum_{i:n_i>0} a_i (K_i/n_i - 1/2).

Define d_i = w_i - a_i and v_i = a_i^2/n_i for n_i > 0, with v_i = 0 otherwise. Let x_i = 2 p_i - 1. Direct bias-variance decomposition gives

    4 R(p) = sum_i v_i + q(x),
    q(x) = (sum_i d_i x_i)^2 - sum_i v_i x_i^2.

This is an identity, not an asymptotic approximation. Since d_i >= 0, replacing x by its componentwise absolute value cannot decrease q. Therefore its maximum on [-1,1]^k equals its maximum on [0,1]^k.

The calculation does not validate the independence/binomial model, prove that an observed count is missing at random, or certify a data-dependent estimator. Such departures change the risk formula. It is not a general natural-language or world-model fact verifier.

## Scalar reduction and algorithm

Write D = sum_i d_i. For x in [0,1]^k, the identity y^2 = max_t (2ty - t^2), with y = d'x in [0,D], yields

    max_x q(x) = max_{0<=t<=D} g(t),
    g(t) = -t^2 + sum_i h_i(t),
    h_i(t) = max_{0<=x_i<=1} [2td_i x_i - v_i x_i^2].

For d_i > 0 and v_i > 0, the maximizer is x_i(t) = min(td_i/v_i, 1), with breakpoint b_i = v_i/d_i. The contribution is t^2 d_i^2/v_i below b_i and 2td_i - v_i above it. If v_i = 0 < d_i, choose x_i = 1 for t > 0 and h_i(t) = 2td_i. If d_i = 0, take x_i = 0 and h_i = 0. A coordinate with d_i = v_i = 0 is irrelevant.

On an interval with saturated set S and unsaturated set U, define

    A_U = sum_{i in U} d_i^2/v_i,
    D_S = sum_{i in S} d_i,
    V_S = sum_{i in S} v_i.

Then

    g(t) = (A_U - 1)t^2 + 2 D_S t - V_S.

Sorting the positive breakpoints and sweeping these aggregate quantities is sufficient. A simple implementation can compare the interval endpoints and an in-interval concave stationary point. A stronger characterization avoids searching multiple maxima:

    g'(t)/(2t) = A_U + D_S/t - 1,  for t > 0.

The right side is continuous and nonincreasing as t increases, including across breakpoints. Once any positive-mass coordinate is saturated, it is strictly decreasing. Thus the function has no separated local maxima.

If every positive d_i has v_i > 0 and A_0 = sum_i d_i^2/v_i <= 1, return t = 0, x = 0, and q_max = 0. Equality A_0 = 1 permits an initial flat set of maximizers, but the zero solution remains correct.

Otherwise a positive root exists in (0,D], characterized by

    sum_i d_i^2 / max(v_i, t d_i) = 1,

where zero-over-zero coordinates are omitted. In an interval containing this root,

    t = D_S/(1 - A_U).

Select the interval by exact rational comparisons. A positive denominator is required for this formula; do not divide when A_U = 1. The maximizing coordinates follow from x_i(t). Tied breakpoints may be processed as a group; assigning a coordinate at exact equality to either side leaves the formula and witness unchanged.

## Independent O(k) certificate verifier

The verifier need not trust the sorted sweep, its interval selection, or a claimed optimizer tolerance. Accept a supplied vector lambda and witness x only if all conditions below hold exactly:

1. lambda_i >= 0 and 0 <= x_i <= 1.
2. Set B_i = v_i + lambda_i. Every B_i = 0 has d_i = 0.
3. S = sum_{i:B_i>0} d_i^2/B_i <= 1.
4. q(x) = sum_i lambda_i.

For any y in [-1,1]^k, weighted Cauchy-Schwarz gives

    (d'y)^2 <= S sum_i B_i y_i^2 <= sum_i B_i y_i^2.

Therefore

    q(y) <= sum_i lambda_i y_i^2 <= sum_i lambda_i.

Condition 4 supplies a feasible lower bound equal to this universal upper bound. Together they prove global optimality. The certified risk is (sum_i v_i + sum_i lambda_i)/4. The parameter witness is p_i = (1+x_i)/2; its simultaneous reflected vector (1-x_i)/2 is also valid.

For a positive root t produced by the algorithm, choose

    lambda_i = max(t d_i - v_i, 0),
    B_i = max(v_i, t d_i),
    x_i = t d_i/B_i when B_i > 0, and x_i = 0 otherwise.

Then S = 1 and d'x = t. Weighted Cauchy-Schwarz is tight, and lambda_i > 0 implies x_i = 1; hence condition 4 holds. When A_0 <= 1, lambda = x = 0 gives the certificate. This is a specialized diagonal-loading/conic-duality certificate, not a claim to have invented those general ideas.

## Boundary and arithmetic audit

- If a_i = w_i, then d_i = 0. That coordinate contributes v_i/4 to worst-case risk and can use p_i = 1/2; it must not be assigned an undefined breakpoint.
- If n_i = 0, then a_i = v_i = 0. If w_i > 0, the coordinate has d_i > 0 and is saturated at any positive root. An absent stratum is represented by uncertainty, not silently given a known value.
- If all d_i = 0, return x = lambda = 0 and risk sum_i v_i/4.
- If all v_i = 0 and D > 0, take t = D, x_i = 1 for d_i > 0, and lambda_i = D d_i. Then q_max = D^2. In the statistical contract with every a_i = 0, D = 1 and the constant estimator's maximum risk is 1/4.
- If A_0 = 1 and there is no positive d_i with v_i = 0, return the zero certificate. A flat initial interval is not a numerical failure or a reason to divide by zero.
- Tied breakpoints and roots exactly at a breakpoint are legitimate. Exact rational comparisons avoid unstable equality heuristics.
- Coefficients, counts, risk, witness, and certificate remain rational. All divisions need explicit denominator checks.
- O(k log k) counts arithmetic/comparison operations on rationals. Numerator/denominator lengths grow with k and input bit length; arbitrary-precision multiplication, division, gcd, and comparison are not constant time. Straightforward exact sums/products have polynomial bit growth, but this review does not claim an O(k log k) bit bound. Runtime/memory reports must include operand sizes or at least maximum numerator/denominator bit lengths.
- The certificate is valid for the submitted input only. Its packaging should bind the exact counts, coefficients, model assumptions, and code/protocol version; hashing does not establish the statistical assumptions.

## Fresh algebraic diagnostic, not an experiment

Take w = (1/2,1/2), n = (1,1), a = (1/3,1/6). Then d = (1/6,1/3), v = (1/9,1/36). The root t = 4/9 gives x = (2/3,1), p = (5/6,1), lambda = (0,13/108), and risk 7/108.

The quarter grid p_i in {0,1/4,1/2,3/4,1} has maximum 37/576. Its exact understatement is 1/1728. The corners alone give 1/16. This hand-derived diagnostic illustrates why a finite grid is not a continuous-domain certificate. It is a disclosed development example, not held-out evidence of an empirical performance rate. It does not imply every coarse grid leads to the wrong acquisition decision.

## Bounded prior-art screen and claim boundaries

Six primary works were selected for review or attempted retrieval; inaccessible texts are identified rather than treated as read. Other search hits were discovery leads, not completed paper reviews. No novelty, patent clearance, or freedom-to-operate conclusion follows.

1. Timothy Allen DeRouen, *Bayes-suggested solutions in binomial estimation*, doctoral dissertation, Virginia Polytechnic Institute and State University, 1971. [Institutional record](https://vtechworks.lib.vt.edu/items/8918cc0e-bd2c-40d7-bc6c-3050761cb153). Abstract reviewed; PDF retrieval failed. It explicitly describes minimax risk optimization within symmetric-beta Bayes estimators for linear binomial combinations. This rules out presenting that broad estimator idea as new.

2. T. A. DeRouen and Toby J. Mitchell, *A G1-Minimax Estimator for a Linear Combination of Binomial Probabilities*, JASA 69(345), 231-233, 1974, DOI 10.1080/01621459.1974.10480160. [Publisher](https://www.tandfonline.com/doi/abs/10.1080/01621459.1974.10480160). Publisher retrieval returned 403. Bibliographic identification is available, but this review does not rely on an uninspected full theorem.

3. K. He, *On Estimating a Linear Combination of Strata Means with Random Sample Sizes*, Journal of Multivariate Analysis 55(1), 39-60, 1995, DOI 10.1006/jmva.1995.1066. [Publisher](https://www.sciencedirect.com/science/article/pii/S0047259X85710664). Publisher retrieval returned 403; only the indexed abstract was reviewed. This is an adjacent random-sample-size estimator problem, not evidence that our fixed-count certificate is absent from prior art.

4. T. A. DeRouen and T. J. Mitchell, *Estimation of a Linear Combination of Binomial Probabilities*, pp. 131-133 in *Mathematics Division Annual Progress Report for Period Ending December 31, 1971*, ORNL-4761, April 1972. [Primary report](https://digital.library.unt.edu/ark:/67531/metadc1032271/m2/1/high_res_d/4504208.pdf). Relevant pages reviewed. The report summarizes known symmetric-beta shrinkage/minimax results, including unequal binomial sample sizes and improved maximum risk in unbalanced cases. It does not establish our particular implementation's novelty.

5. Milan Hladik, Michal Cerny, and Miroslav Rada, *A new polynomially solvable class of quadratic optimization problems with box constraints*, Optimization Letters 15, 2331-2341, 2021, DOI 10.1007/s11590-021-01711-6. [Author preprint](https://arxiv.org/pdf/1911.10877). It provides a fixed-rank quadratic-box method based on zonotope faces. Our full matrix dd' - diag(v) need not have fixed rank, so their stated low-rank condition does not directly describe our whole family. This difference alone establishes no novelty.

6. Samuel Burer, Karthik Natarajan, and Rick Willemsen, *On the Semidefinite Representability of Continuous Quadratic Submodular Minimization With Applications to Pricing and Moment Problems*, March 2026, revised September 2026. [Primary manuscript](https://optimization-online.org/wp-content/uploads/2025/04/submodular-1.pdf), particularly pp. 2 and 7. Proposition 1 restates Kim and Kojima (2003), Theorems 3.1 and 3.5: submodular BoxQP with nonpositive linear term has an exact SDP/SOCP relaxation for arbitrary dimension. Our minimization has Q = diag(v) - dd' and c = 0, so it lies in that known tractable class. General polynomial tractability is therefore not a contribution here.

The antecedent identified through work 6 is S. Kim and M. Kojima, *Exact solutions of some nonconvex quadratic optimization problems via SDP and SOCP relaxations*, Computational Optimization and Applications 26(2), 143-154, 2003. Its original text was not separately reviewed within this six-work budget; the theorem boundary above is sourced to the explicit restatement in work 6.

An independent reviewer also identified a nearby diagonal-plus/minus-rank-one proximal literature lead (Becker and Fadili, 2012). It has not been reviewed here and should not be claimed to be resolved; its positive-definite metric assumptions need checking before comparing it to this nonconvex risk maximization. Water-filling and diagonal-loading connections should be acknowledged even if the statistical application is useful.

## Recommended new verification and falsifiers

Freeze a new protocol and new original rational inputs. Separate disclosed algebraic development cases from a fresh confirmatory suite. Do not reuse the negative audit as untouched evaluation data.

Correctness comparison: an independently implemented exact face/active-set optimizer for small k, plus direct enumeration of binomial outcome expectations for very small counts. Every certificate must survive an independently implemented upper/lower verifier. Include zero counts, zero weights, no shrinkage, maximal shrinkage, all-zero variances, repeated breakpoints, A_0 below/equal/above one, and roots at breakpoints. Deliberately corrupted certificates must be rejected.

The meaningful strong computational baseline is the known exact SDP/SOCP formulation or a verified global optimizer; a coarse grid is only a failure demonstration. If no conic solver is available, report the comparison as not performed and limit empirical efficiency claims to the executed reference implementation. A narrow arithmetic/verification advantage is not a statistical improvement in the estimator.

Falsifiers: any certificate/value mismatch invalidates the implementation; a failure of a proof assumption invalidates application to that data; identification of an existing equivalent breakpoint algorithm defeats algorithmic novelty; no practical advantage against the strongest relevant implementation defeats the claimed operational advantage. A certificate can be useful without constituting an invention. Do not lower these distinctions to meet a same-day paper target.
