"""Elliptic Fourier analysis (EFA) of closed 2D outlines.

An outline is a closed curve traced on a specimen (a semi-landmark curve with
``closed`` set). EFA describes it as a sum of harmonics, each an ellipse given
by four coefficients ``(a, b, c, d)`` (Kuhl & Giardina 1982):

    x(t) = A0 + sum_n a_n cos(n t) + b_n sin(n t)
    y(t) = C0 + sum_n c_n cos(n t) + d_n sin(n t)        t in [0, 2*pi)

Conventions fixed for Modan2 (devlog 288):

* **The first traced point is homologous.** The user starts every outline at a
  landmark-like point, so the starting point is *kept*, not normalized away --
  no phase shift is applied, and harmonic 1 is not reduced to a constant.
* **Direction is always clockwise as displayed** (image coordinates, y down).
  A counter-clockwise trace is reversed about its first point before analysis.
* **Size and rotation** are normalized by the first harmonic ellipse: divided by
  its semi-major axis and rotated so the major axis lies on +x. The major axis
  has two ends; the one nearest the starting point (in the curve parameter) is
  taken, the same rule as Momocs' ``efourier_norm(start = TRUE)``.
* **Translation** is dropped (A0, C0 are not part of the shape vector).

The statistics in Modan2 operate on landmark coordinates, so a normalized
coefficient vector is turned into ``m`` points by evaluating the series at
equally spaced ``t`` and scaling by ``sqrt(2/m)`` (:func:`coefficients_to_points`).
With ``m > 2 * harmonics`` the Fourier basis is orthogonal on those samples, so
this map is an exact isometry of the coefficient space: PCA, CVA and MANOVA on
the points give the same results as on the coefficients themselves, while the
viewers can draw every shape -- including PCA-reconstructed ones -- unchanged.
"""

import math

import numpy as np

# The superimposition-method name an outline analysis is stored and requested
# under (MdAnalysis.superimposition_method, ModanController.run_analysis).
ELLIPTIC_FOURIER = "Elliptic Fourier"
# Default share of total harmonic power the automatic harmonic count retains.
DEFAULT_POWER_THRESHOLD = 0.99
# Upper bound on harmonics considered; Nyquist (half the outline's point count)
# applies as well. Fifty is well past what morphometric outlines use.
MAX_HARMONICS = 50
# Fewest points an outline is sampled to for display/statistics.
MIN_OUTLINE_POINTS = 64


def clean_outline(points):
    """Outline points as an ``(k, 2)`` array without repeats.

    Drops consecutive duplicates and a trailing copy of the first point (a
    closed trace often ends where it began); EFA divides by segment length, so a
    zero-length segment would be a division by zero.

    Raises:
        ValueError: fewer than 3 distinct points remain.
    """
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or pts.shape[0] == 0 or pts.shape[1] < 2:
        raise ValueError("an outline needs [x, y] points")
    pts = pts[:, :2]
    keep = [0]
    for i in range(1, len(pts)):
        if not np.allclose(pts[i], pts[keep[-1]]):
            keep.append(i)
    pts = pts[keep]
    while len(pts) > 1 and np.allclose(pts[-1], pts[0]):
        pts = pts[:-1]
    if len(pts) < 3:
        raise ValueError("an outline needs at least 3 distinct points")
    return pts


def signed_area(points):
    """Shoelace area of a closed polygon in the points' own coordinates.

    Positive means clockwise *as displayed* in image coordinates (y down),
    which is counter-clockwise in the usual y-up mathematical sense.
    """
    pts = np.asarray(points, dtype=float)
    x, y = pts[:, 0], pts[:, 1]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


def make_clockwise(points):
    """The outline running clockwise as displayed, starting at the same point.

    A counter-clockwise trace is reversed about its first point
    (``p0, p1, ..., pk`` -> ``p0, pk, ..., p1``) so the homologous start stays
    first.
    """
    pts = np.asarray(points, dtype=float)
    if signed_area(pts) < 0:
        pts = np.vstack([pts[:1], pts[:0:-1]])
    return pts


def efa_coefficients(points, harmonics):
    """Elliptic Fourier coefficients of a closed polygon (Kuhl & Giardina 1982).

    The polygon is taken exactly as given (no direction change); the curve
    parameter is proportional to arc length and ``t = 0`` is the first point.

    Returns:
        ``(coeffs, (A0, C0))`` -- ``coeffs`` is ``(harmonics, 4)`` holding
        ``a, b, c, d`` per harmonic; ``A0, C0`` is the outline's centre.
    """
    pts = clean_outline(points)
    closed = np.vstack([pts, pts[:1]])
    d = np.diff(closed, axis=0)
    dt = np.sqrt((d**2).sum(axis=1))
    t = np.concatenate([[0.0], np.cumsum(dt)])
    period = t[-1]
    phi = 2.0 * np.pi * t / period

    n = np.arange(1, harmonics + 1)[:, None]
    const = period / (2.0 * n**2 * np.pi**2)
    dcos = np.cos(n * phi[1:]) - np.cos(n * phi[:-1])
    dsin = np.sin(n * phi[1:]) - np.sin(n * phi[:-1])
    dxdt = d[:, 0] / dt
    dydt = d[:, 1] / dt
    coeffs = np.column_stack(
        [
            (const[:, 0] * (dcos * dxdt).sum(axis=1)),
            (const[:, 0] * (dsin * dxdt).sum(axis=1)),
            (const[:, 0] * (dcos * dydt).sum(axis=1)),
            (const[:, 0] * (dsin * dydt).sum(axis=1)),
        ]
    )

    # Centre (A0, C0): the mean of the curve over the period, segment by segment.
    xm = (closed[:-1, 0] + closed[1:, 0]) / 2.0
    ym = (closed[:-1, 1] + closed[1:, 1]) / 2.0
    center = (float((xm * dt).sum() / period), float((ym * dt).sum() / period))
    return coeffs, center


def normalize_coefficients(coeffs):
    """Size- and rotation-normalize coefficients, keeping the starting point.

    Returns:
        ``(normalized, scale, psi)`` -- the coefficients divided by the first
        ellipse's semi-major axis ``scale`` and rotated by ``-psi`` (the major
        axis angle). No phase shift: the traced starting point stays ``t = 0``.

    Raises:
        ValueError: the first harmonic is degenerate (zero size).
    """
    coeffs = np.asarray(coeffs, dtype=float)
    a1, b1, c1, d1 = coeffs[0]
    # Parameter of the major-axis end nearest t = 0: maximizes |r(t)|^2 of the
    # first ellipse, in (-pi/2, pi/2].
    theta = 0.5 * math.atan2(2.0 * (a1 * b1 + c1 * d1), a1**2 + c1**2 - b1**2 - d1**2)
    x_end = a1 * math.cos(theta) + b1 * math.sin(theta)
    y_end = c1 * math.cos(theta) + d1 * math.sin(theta)
    scale = math.hypot(x_end, y_end)
    if scale == 0 or not math.isfinite(scale):
        raise ValueError("the outline's first harmonic is degenerate")
    psi = math.atan2(y_end, x_end)
    rot = np.array([[math.cos(psi), math.sin(psi)], [-math.sin(psi), math.cos(psi)]])

    out = np.empty_like(coeffs)
    for i, (a, b, c, d) in enumerate(coeffs):
        m = rot @ np.array([[a, b], [c, d]]) / scale
        out[i] = (m[0, 0], m[0, 1], m[1, 0], m[1, 1])
    return out, scale, psi


def harmonic_power(coeffs):
    """Power of each harmonic, ``(a^2 + b^2 + c^2 + d^2) / 2``."""
    coeffs = np.asarray(coeffs, dtype=float)
    return (coeffs**2).sum(axis=1) / 2.0


def harmonics_for_power(coeffs, threshold=DEFAULT_POWER_THRESHOLD):
    """Fewest harmonics whose cumulative power reaches ``threshold``.

    Power is measured relative to all harmonics in ``coeffs``.
    """
    power = harmonic_power(coeffs)
    total = power.sum()
    if total <= 0:
        return 1
    cumulative = np.cumsum(power) / total
    return int(np.searchsorted(cumulative, threshold - 1e-12) + 1)


def max_harmonics(points):
    """Highest harmonic count the outline supports (Nyquist, capped)."""
    return max(1, min(MAX_HARMONICS, len(clean_outline(points)) // 2))


def choose_harmonics(outlines, threshold=DEFAULT_POWER_THRESHOLD):
    """Dataset harmonic count reaching ``threshold`` power for every outline.

    Each outline's power is measured over the harmonics the *whole set*
    supports (the smallest Nyquist limit, capped at :data:`MAX_HARMONICS`), so
    every specimen is judged on the same scale. The largest per-outline count
    is returned: the set keeps at least ``threshold`` of every specimen's power.
    """
    limit = min(max_harmonics(p) for p in outlines)
    needed = 1
    for p in outlines:
        coeffs, _ = efa_coefficients(make_clockwise(clean_outline(p)), limit)
        needed = max(needed, harmonics_for_power(coeffs, threshold))
    return min(needed, limit)


def outline_points_count(harmonics):
    """Sample count for :func:`coefficients_to_points`; always > 2 * harmonics."""
    return max(MIN_OUTLINE_POINTS, 4 * int(harmonics))


def reconstruct(coeffs, n_points, center=(0.0, 0.0)):
    """Evaluate the series at ``n_points`` equally spaced parameters from t = 0."""
    coeffs = np.asarray(coeffs, dtype=float)
    t = 2.0 * np.pi * np.arange(n_points) / n_points
    n = np.arange(1, len(coeffs) + 1)[:, None]
    cos_nt, sin_nt = np.cos(n * t), np.sin(n * t)
    x = center[0] + coeffs[:, 0] @ cos_nt + coeffs[:, 1] @ sin_nt
    y = center[1] + coeffs[:, 2] @ cos_nt + coeffs[:, 3] @ sin_nt
    return np.column_stack([x, y])


def coefficients_to_points(coeffs, n_points):
    """Shape points whose geometry equals the coefficient space's.

    ``reconstruct`` (centred) scaled by ``sqrt(2 / n_points)``: for
    ``n_points > 2 * harmonics`` the squared distance between two such point
    sets equals the squared distance between their coefficient vectors, so the
    points can stand in for the coefficients in any statistic.
    """
    if n_points <= 2 * len(coeffs):
        raise ValueError("n_points must exceed twice the harmonic count")
    return reconstruct(coeffs, n_points) * math.sqrt(2.0 / n_points)


def analyze_outline(points, harmonics):
    """Full per-specimen pipeline: clean, clockwise, EFA, normalize.

    Returns:
        dict with ``coefficients`` (normalized, ``(harmonics, 4)``), ``size``
        (first ellipse semi-major axis, in the outline's units), ``rotation``
        (radians removed) and ``center`` (A0, C0).
    """
    pts = make_clockwise(clean_outline(points))
    coeffs, center = efa_coefficients(pts, harmonics)
    normalized, scale, psi = normalize_coefficients(coeffs)
    return {"coefficients": normalized, "size": scale, "rotation": psi, "center": center}
