"""F0/loudness-residualized HNR: is the clarity-vs-progesterone signal an artifact?

HNR (harmonics-to-noise ratio = voice clarity) is the main report's headline
signal: it rises with progesterone in both the sustained vowel and connected
speech. Like H1-H2, HNR can co-vary with F0 (pitch) and loudness (intensity), so
the same confound check applies. This regresses daily HNR on F0 and loudness and
re-runs the cycle analyses on the residual.

If both residualized H1-H2 AND residualized HNR rise in the luteal phase, that is
a specific acoustic fingerprint of the soft-cover mechanism: no single pitch or
intensity confound would lift an open-quotient proxy and a noise-ratio measure
together.

Thin wrapper over `feature_residual`; the analysis logic lives there.
"""

from __future__ import annotations

from .feature_residual import ResidualSpec, run

SPEC = ResidualSpec(
    target_base="egemaps_HNRdBACF_sma3nz_amean",
    label="HNR",
    resid_key="HNR",
    unit="dB",
    fig_task="prosody",
)


def main() -> None:
    run(SPEC, table_prefix="hnr_residual", fig_name="fig11_hnr_residual.png")


if __name__ == "__main__":
    main()
