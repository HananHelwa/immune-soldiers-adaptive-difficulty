import math
import random


def clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def sample_bounded_gauss(mean: float, sd: float, bounds: tuple, rng: random.Random) -> float:
    """Clamped (not resampled) truncated normal -- adequate here since sd is small
    relative to the bounds, so tail distortion from clamping is negligible."""
    return clip(rng.gauss(mean, sd), bounds[0], bounds[1])


def pearson_r(xs: list, ys: list) -> float:
    n = len(xs)
    if n < 2:
        return float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx == 0 or vy == 0:
        return float("nan")
    return cov / math.sqrt(vx * vy)


def mean(xs: list) -> float:
    xs = list(xs)
    return sum(xs) / len(xs) if xs else float("nan")


def stdev(xs: list) -> float:
    xs = list(xs)
    n = len(xs)
    if n < 2:
        return float("nan")
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
