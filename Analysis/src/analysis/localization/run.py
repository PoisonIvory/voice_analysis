"""Run the driver-localization analysis: writes all tables + summary.json."""

from __future__ import annotations

import json

import pandas as pd

from .config import FOCUSED_MOVED, PRIMARY_TASK, SECONDARY_TASK, localization_paths
from . import dissociation as d1
from . import sensitivity as s1
from . import hormones as h2
from . import rate_variability as r3
from . import pmdd as p4
from .dataset import load_daily


def _save(df: pd.DataFrame, path) -> None:
    df.to_csv(path, index=False)


def main() -> dict:
    paths = localization_paths()
    paths.tables_dir.mkdir(parents=True, exist_ok=True)
    paths.figures_dir.mkdir(parents=True, exist_ok=True)

    df = load_daily()

    # --- Thread 1: mean dissociation ---
    effects = pd.concat(
        [d1.feature_effect_table(df, PRIMARY_TASK), d1.feature_effect_table(df, SECONDARY_TASK)],
        ignore_index=True,
    )
    _save(effects, paths.tables_dir / "feature_effects.csv")

    focused = list(FOCUSED_MOVED)
    dissoc = pd.DataFrame([
        d1.dissociation_test(df, PRIMARY_TASK, label="broad"),
        d1.dissociation_test(df, SECONDARY_TASK, label="broad"),
        d1.dissociation_test(df, PRIMARY_TASK, moved=focused, label="focused"),
        d1.dissociation_test(df, SECONDARY_TASK, moved=focused, label="focused"),
    ])
    _save(dissoc, paths.tables_dir / "dissociation_test.csv")

    equiv = pd.DataFrame([d1.equivalence_test(df, PRIMARY_TASK), d1.equivalence_test(df, SECONDARY_TASK)])
    _save(equiv, paths.tables_dir / "equivalence_test.csv")

    sens = s1.sensitivity_table(df)
    _save(sens, paths.tables_dir / "sensitivity_floor.csv")
    hub = s1.hubert_vowel_geometry()
    if not hub.empty:
        _save(hub, paths.tables_dir / "hubert_vowel_geometry.csv")

    # --- Thread 2: two-hormone attribution ---
    coupling = h2.coupling_table(df, PRIMARY_TASK)
    _save(coupling, paths.tables_dir / "hormone_coupling.csv")
    pvc = h2.peripheral_vs_central(coupling)
    _save(pvc, paths.tables_dir / "peripheral_vs_central.csv")
    peri = pd.DataFrame([h2.estrogen_periovulatory(df, PRIMARY_TASK), h2.estrogen_periovulatory(df, SECONDARY_TASK)])
    _save(peri, paths.tables_dir / "estrogen_periovulatory.csv")

    # --- Thread 3: rate / variability ---
    var_window = r3.variability_by_window(df, PRIMARY_TASK)
    _save(var_window, paths.tables_dir / "variability_by_window.csv")
    var_rate = r3.variability_by_pdg_rate(df, PRIMARY_TASK)
    if not var_rate.empty:
        _save(var_rate, paths.tables_dir / "variability_by_pdg_rate.csv")

    # --- Thread 4: PMDD lens ---
    premen = p4.premenstrual_window(df, PRIMARY_TASK)
    _save(premen, paths.tables_dir / "premenstrual_window.csv")
    kervin = p4.kervin_contrast(df, PRIMARY_TASK)
    _save(kervin, paths.tables_dir / "kervin_contrast.csv")
    hrv = p4.hrv_context(df)
    _save(hrv, paths.tables_dir / "hrv_context.csv")

    # --- headline summary ---
    dprim = dissoc[dissoc["task"] == PRIMARY_TASK].iloc[0].to_dict()
    eprim = equiv[equiv["task"] == PRIMARY_TASK].iloc[0].to_dict()
    summary = {
        "coverage": {
            "voice_days": int(df["has_voice"].sum()),
            "voice_phase_days": int((df["has_voice"] & df["phase_label"].notna()).sum()),
            "voice_hormone_days": int((df["has_voice"] & df["has_hormones"]).sum()),
        },
        "dissociation_primary": dprim,
        "equivalence_primary": eprim,
        "sensitivity_floor": sens.to_dict(orient="records"),
        "peripheral_vs_central": pvc.to_dict(orient="records"),
    }
    with open(paths.tables_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=float)

    print("dissociation (prosody): D=%.3f p=%.4f moved=%.2f spared=%.2f"
          % (dprim["dissociation_D"], dprim["perm_p"], dprim["moved_abs_cliffs"], dprim["spared_abs_cliffs"]))
    print("equivalence (prosody): geometry |delta|=%.3f CI90=[%.3f,%.3f] equivalent=%s (SESOI=%.3f)"
          % (eprim["geometry_abs_cliffs"], eprim["geometry_ci90_lo"], eprim["geometry_ci90_hi"],
             eprim["equivalent_to_negligible"], eprim["sesoi"]))
    return summary


if __name__ == "__main__":
    main()
