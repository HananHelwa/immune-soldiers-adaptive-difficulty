"""Two-channel Bayesian Knowledge Tracing (Section 3.2).

Standard single-channel BKT extended with a second observation channel: an
encounter can yield a quiz/dialogue outcome, a combat outcome, or both, and
both update the same latent per-KC mastery estimate via their own guess/slip
pair. Flagged in the manuscript as needing a supporting citation before
submission -- treat this as our own modest extension, not an established
technique.
"""

from utils import clip


class TwoChannelBKT:
    def __init__(self, kcs, p_l0, p_t, p_g, p_s, p_f):
        self.mastery = {kc: p_l0 for kc in kcs}
        self.p_t = p_t
        self.p_g = p_g  # {"quiz": ..., "combat": ...}
        self.p_s = p_s
        self.p_f = p_f
        self.practiced_this_session = set()

    def observe(self, kc: str, channel: str, correct: bool) -> float:
        """Bayes evidence step only (no learning transit) -- so that an encounter
        with both a quiz and a combat observation applies two evidence updates
        but still only one learning transit (see `apply_transit`); doing the
        transit per-channel would double-count a single practice opportunity."""
        L = self.mastery[kc]
        g = self.p_g[channel]
        s = self.p_s[channel]

        if correct:
            numerator = L * (1 - s)
            denominator = numerator + (1 - L) * g
        else:
            numerator = L * s
            denominator = numerator + (1 - L) * (1 - g)

        self.mastery[kc] = clip(numerator / denominator if denominator > 0 else L, 0.0, 1.0)
        self.practiced_this_session.add(kc)
        return self.mastery[kc]

    def apply_transit(self, kc: str) -> float:
        """Learning-transit step, applied once per encounter (Section 3.2)."""
        l_post = self.mastery[kc]
        self.mastery[kc] = clip(l_post + (1 - l_post) * self.p_t, 0.0, 1.0)
        return self.mastery[kc]

    def end_session(self) -> None:
        """Apply forgetting once to every KC not practiced this session (Section 3.2)."""
        for kc in self.mastery:
            if kc not in self.practiced_this_session:
                self.mastery[kc] = clip(self.mastery[kc] * (1 - self.p_f), 0.0, 1.0)
        self.practiced_this_session = set()
