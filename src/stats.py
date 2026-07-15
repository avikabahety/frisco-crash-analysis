"""Statistical tests used across the analyses.

Deliberately explicit rather than pulled from scipy: each test is short enough to
read, and the assumptions are visible at the point of use.
"""

from math import erfc, exp, log, sqrt

import numpy as np


def _p_from_z(z):
    """Two-sided p-value from a z statistic."""
    return erfc(abs(z) / sqrt(2))


def compare_proportions(k1, n1, k2, n2):
    """Two-proportion z test. Returns (p1, p2, difference_pp, z, p)."""
    if min(n1, n2) == 0:
        return np.nan, np.nan, np.nan, np.nan, np.nan
    p1, p2 = k1 / n1, k2 / n2
    pooled = (k1 + k2) / (n1 + n2)
    se = sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    if se == 0:
        return p1, p2, (p1 - p2) * 100, np.nan, np.nan
    z = (p1 - p2) / se
    return p1, p2, (p1 - p2) * 100, z, _p_from_z(z)


def rate_ratio(k1, exposure1, k2, exposure2):
    """Ratio of two counts, each divided by its exposure, with a 95% interval.

    Exposure here is calendar days. A ratio of raw counts would mislead if the two
    periods covered different numbers of days.
    """
    if min(k1, k2) == 0:
        return np.nan, np.nan, np.nan
    r = (k1 / exposure1) / (k2 / exposure2)
    se = sqrt(1 / k1 + 1 / k2)                 # Poisson, on the log scale
    return r, exp(log(r) - 1.96 * se), exp(log(r) + 1.96 * se)


def mantel_haenszel(strata):
    """Common odds ratio across strata, with the MH chi-square.

    Each stratum is (a, b, c, d): exposed-case, exposed-noncase, unexposed-case,
    unexposed-noncase. Stratifying by intersection separates the effect of darkness
    from differences in which intersections appear in each group, a confound a pooled
    test cannot detect.
    """
    num = den = expected = observed = variance = 0.0
    for a, b, c, d in strata:
        n = a + b + c + d
        if n < 2:
            continue
        num += a * d / n
        den += b * c / n
        observed += a
        expected += (a + b) * (a + c) / n
        variance += ((a + b) * (c + d) * (a + c) * (b + d)) / (n * n * (n - 1))
    if den == 0 or variance == 0:
        return np.nan, np.nan, np.nan
    or_mh = num / den
    chi = (abs(observed - expected) - 0.5) ** 2 / variance
    return or_mh, chi, erfc(sqrt(chi / 2))


def interaction(k1a, n1a, k1b, n1b, k2a, n2a, k2b, n2b):
    """Is the effect in group 1 DIFFERENT from the effect in group 2?

    Comparing two significant effects and eyeballing which looks larger is not a
    test. Two effects can both be real and still be indistinguishable from each
    other. This compares the log odds ratios directly.

    Group 1: (k1a of n1a) vs (k1b of n1b).  Group 2: (k2a of n2a) vs (k2b of n2b).
    Returns (or1, or2, z, p).
    """
    def log_or(ka, na, kb, nb):
        a, b, c, d = ka, na - ka, kb, nb - kb
        if min(a, b, c, d) == 0:
            return np.nan, np.nan
        odds = (a / b) / (c / d)
        return log(odds), sqrt(1 / a + 1 / b + 1 / c + 1 / d)

    l1, se1 = log_or(k1a, n1a, k1b, n1b)
    l2, se2 = log_or(k2a, n2a, k2b, n2b)
    if np.isnan(l1) or np.isnan(l2):
        return np.nan, np.nan, np.nan, np.nan
    z = (l1 - l2) / sqrt(se1 ** 2 + se2 ** 2)
    return exp(l1), exp(l2), z, _p_from_z(z)


def sign_test(successes, trials):
    """Do more strata move in the predicted direction than chance would give?"""
    if trials == 0:
        return np.nan, np.nan
    z = (successes - trials / 2) / sqrt(trials / 4)
    return z, _p_from_z(z)


def stars(p):
    if p is None or (isinstance(p, float) and np.isnan(p)):
        return ""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "n.s."
