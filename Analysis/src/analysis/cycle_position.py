"""Progesterone proxy derived from calendar position, for cycles without draws.

We only measured hormones on ~2 cycles, but the cycle calendar labels ~4. To
test whether a voice signal persists in the un-sampled cycles, we need a stand-in
for "where progesterone is" on days we did not assay it.

Progesterone is low through the follicular phase, rises after ovulation, peaks in
the mid-luteal phase (about a week before the next period), then falls before
menstruation. We approximate that trajectory with a triangular bump on
`days_to_next_start`, peaking 7 days before the next cycle start and tapering to
zero at the phase boundaries. It needs no hormone data, so it applies to every
labeled day.

The proxy is validated against measured PdG where the two overlap (see
`h1h2_across_cycles`); it is a coarse position index, not a calibrated level.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

LUTEAL_PEAK_DAYS_BEFORE_NEXT = 7  # mid-luteal progesterone peak
LUTEAL_HALF_WIDTH = 7             # taper to zero at ovulation and at menses


def progesterone_proxy(df: pd.DataFrame) -> pd.Series:
    """Return a 0..1 cycle-position progesterone proxy aligned to `df`.

    Requires `days_to_next_start`. Days outside the luteal window (and days with
    no known next cycle start) get 0 / NaN respectively.
    """
    days_to_next = pd.to_numeric(df["days_to_next_start"], errors="coerce")
    bump = 1.0 - (days_to_next - LUTEAL_PEAK_DAYS_BEFORE_NEXT).abs() / LUTEAL_HALF_WIDTH
    proxy = bump.clip(lower=0.0)
    proxy[days_to_next.isna()] = np.nan
    return proxy
