"""F0/loudness-residualized H1-H2: is the cycle signal a pitch/intensity artifact?

H1-H2 (the glottal open-quotient proxy) separates the cycle phases in this data
set (luteal > follicular). But H1-H2 co-varies with F0 (pitch) and vocal intensity
(loudness). This regresses daily H1-H2 on F0 and loudness and re-runs the cycle
analyses on the residual; if the phase signal survives, it is a genuine
vocal-fold tissue property rather than a pitch/intensity artifact.

Thin wrapper over `feature_residual`; the analysis logic lives there.
"""

from __future__ import annotations

from .feature_residual import ResidualSpec, run

SPEC = ResidualSpec(
    target_base="egemaps_logRelF0-H1-H2_sma3nz_amean",
    label="H1-H2",
    resid_key="H1H2",
    unit="connected speech",
    fig_task="prosody",
)


def main() -> None:
    run(SPEC, table_prefix="h1h2_residual", fig_name="fig09_h1h2_residual.png")


if __name__ == "__main__":
    main()
