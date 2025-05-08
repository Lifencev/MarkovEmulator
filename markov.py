from math import log, exp


class MarkovError(ValueError):
    pass


class Rule:
    def __init__(self, pattern, replacement, terminal=False):
        if ':' in pattern or ':' in replacement:
            raise MarkovError("there must be only one ':'")
        self.pattern = pattern
        self.replacement = replacement
        self.terminal = terminal

    def __repr__(self) -> str:
        suffix = "." if self.terminal else ""
        return f"Rule({self.pattern!r}:{self.replacement!r}{suffix})"


class TraceStep:
    def __init__(self, step, word, rule_pattern):
        self.step = step
        self.word = word
        self.rule = rule_pattern


    def __repr__(self) -> str:
        return f"Step {self.step}: {self.word!r} (rule '{self.rule}')"


class MarkovEngine:
    def __init__(self, rules, max_steps=10_000):
        if not rules:
            raise MarkovError("no rules")
        self.rules = rules
        self.max_steps = max_steps
        self.longest_word: str | None = None
        self.max_space: int = 0

    def _find_leftmost(self, word):
        for i, rule in enumerate(self.rules):
            pos = word.find(rule.pattern)
            if pos != -1:
                return i, rule, pos, pos + len(rule.pattern)
        return None

    def run(self, word):
        trace = []
        longest_word = word
        for step in range(self.max_steps):
            found = self._find_leftmost(word)
            if found is None:
                break
            idx, rule, a, b = found
            word = word[:a] + rule.replacement + word[b:]

            if len(word) > len(longest_word):
                longest_word = word

            trace.append(TraceStep(step + 1, word, f"{rule.pattern}:{rule.replacement}"))
            if rule.terminal:
                break
        else:
            raise MarkovError("step limit exceeded")

        self.longest_word = longest_word
        self.max_space = len(longest_word)

        return word, trace


    def space_complexity(self):
        if self.longest_word is None:
            raise MarkovError("space_complexity() requested before run()")
        return self.max_space, self.longest_word


def _ols(xvals, yvals):
    n = len(xvals)
    sx = sum(xvals)
    sy = sum(yvals)
    sxx = sum(x * x for x in xvals)
    sxy = sum(x * y for x, y in zip(xvals, yvals))
    normal = n * sxx - sx * sx
    if normal == 0:
        return 0.0, 0.0
    slope = (n * sxy - sx * sy) / normal
    intercept = (sy - slope * sx) / n
    return slope, intercept


def _r2(xvals, yvals, slope, intercept):
    mean_y = sum(yvals) / len(yvals)
    ss_tot = sum((y - mean_y) ** 2 for y in yvals)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xvals, yvals))
    return 1 - ss_res / ss_tot if ss_tot else 0.0


COMPLEXITIES = {
    0: "O(1)",
    1: "O(n)",
    2: "O(n^2)",
    3: "O(n^3)",
    "log": "O(log n)",
    "nlog":"O(n log n)"
}


def guess_big_o(samples):
    nvals, svals = zip(*samples)

    if len(set(svals)) == 1:
        return COMPLEXITIES[0]

    xs_log = [log(n) for n in nvals]
    ys_n = [s / n for n, s in samples]
    slope_nlog, int_nlog = _ols(xs_log, ys_n)
    r2_nlog = _r2(xs_log, ys_n, slope_nlog, int_nlog)

    if len(xs_log) > 1 and r2_nlog  > 0.80:
        return COMPLEXITIES['nlog']

    ys_log = list(svals)
    slope_log, int_log = _ols(xs_log, ys_log)
    r2_log = _r2(xs_log, ys_log, slope_log, int_log)

    if len(xs_log) > 1 and r2_log > 0.80:
        return COMPLEXITIES['log']

    xs = [log(n) for n in nvals]
    ys = [log(s) if s > 0 else 0 for s in svals]
    slope, intercept = _ols(xs, ys)
    r_pol = _r2(xs, ys, slope, intercept)

    if len(xs) > 1 and r_pol > 0.80:
        p = round(slope)
        return COMPLEXITIES.get(p, f"O(n^{slope})")

    xs = nvals
    ys = [log(s) if s > 0 else 0 for s in svals]
    slope, intercept = _ols(xs, ys)
    r_exp = _r2(xs, ys, slope, intercept)

    if len(xs) > 1 and r_exp > 0.80:
        base = exp(slope)
        if abs(base - 2) < 0.3:
            return "O(2^n)"
        return f"O({base:.1f}^n)"

    return "?"


def empirical_space_complexity(rules, sizes, word_builder):
    samples: list[tuple[int, int]] = []
    for n in sizes:
        eng = MarkovEngine(rules)
        w = word_builder(n)
        eng.run(w)
        samples.append((n, eng.max_space))
    return guess_big_o(samples), samples


def empirical_time_complexity(rules, sizes, word_builder):
    samples: list[tuple[int, int]] = []
    for n in sizes:
        eng = MarkovEngine(rules)
        w = word_builder(n)
        _, trace = eng.run(w)
        samples.append((n, len(trace)))
    return guess_big_o(samples), samples
