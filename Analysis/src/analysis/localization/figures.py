"""Render the localization figures (plain-language titles, embedded in the report)."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .config import FAMILY_LABELS, localization_paths

plt.rcParams.update({"figure.dpi": 150, "font.size": 10, "axes.titlesize": 12})

COVER = "#2a7fb8"
TIMBRE = "#5aa9d6"
PITCH = "#8c6bb1"
CENTRAL = "#d6604d"
DAMP = "#bdbdbd"
GEOM = "#444444"
FAMILY_COLOR = {
    "peripheral_cover": COVER,
    "timbre": TIMBRE,
    "source_pitch": PITCH,
    "central_control": CENTRAL,
    "geometry_damping": DAMP,
    "geometry": GEOM,
}
FAMILY_ORDER = ["peripheral_cover", "timbre", "source_pitch", "central_control", "geometry_damping", "geometry"]


def _t(name: str):
    return localization_paths().tables_dir / name


def _save(fig, name: str):
    out = localization_paths().figures_dir / name
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def fig_localization_map():
    fe = pd.read_csv(_t("feature_effects.csv"))
    fe = fe[fe["task"] == "prosody"].copy()
    fe["forder"] = fe["family"].map({f: i for i, f in enumerate(FAMILY_ORDER)})
    fe = fe.sort_values(["forder", "cliffs_delta"]).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(9, 9))
    ax.axvspan(-0.147, 0.147, color="0.92", zorder=0)
    ax.axvline(0, color="0.5", lw=0.8)
    y = np.arange(len(fe))
    ax.barh(y, fe["cliffs_delta"], color=[FAMILY_COLOR[f] for f in fe["family"]])
    ax.set_yticks(y)
    ax.set_yticklabels(fe["label"], fontsize=8)
    ax.set_ylim(-1, len(fe))
    ax.set_xlabel("Luteal vs follicular effect (Cliff's delta; right = higher in luteal)")
    ax.set_title("What the cycle moves in the voice - and what it leaves alone\n"
                 "(grey band = negligible effect; top dark block = vocal-tract geometry)")
    handles = [plt.Rectangle((0, 0), 1, 1, color=FAMILY_COLOR[f]) for f in FAMILY_ORDER]
    ax.legend(handles, [FAMILY_LABELS[f] for f in FAMILY_ORDER], loc="lower right", fontsize=8, frameon=True)
    return _save(fig, "fig01_localization_map.png")


def fig_sensitivity_floor():
    s = pd.read_csv(_t("sensitivity_floor.csv"))
    fig, ax = plt.subplots(figsize=(8.5, 5))
    x = np.arange(len(s))
    w = 0.27
    ax.bar(x - w, s["within_recording_sd_hz"], w, label="Within one sentence", color="#2a7fb8")
    ax.bar(x, s["vowel_vs_prosody_shift_hz"], w, label="Between speech tasks", color="#9ecae1")
    ax.bar(x + w, s["cycle_shift_hz"], w, label="Across the cycle (luteal vs follicular)", color="#d6604d")
    ax.set_yscale("log")
    ax.set_ylim(1, 600)
    ax.set_xticks(x)
    ax.set_xticklabels(s["formant"])
    ax.set_ylabel("Movement in the formant (Hz, log scale)")
    ax.set_title("The dog that didn't bark\n"
                 "The same measurement resolves far bigger shifts than the cycle ever produces")
    for xi, row in zip(x, s.itertuples()):
        r = row.sensitivity_ratio_withinrec
        if np.isfinite(r):
            ax.text(xi - w, row.within_recording_sd_hz * 1.25, f"{r:.0f}x\nvs cycle", ha="center", fontsize=8)
    ax.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.01, 1.0), borderaxespad=0)
    return _save(fig, "fig02_sensitivity_floor.png")


def fig_two_hormones():
    hc = pd.read_csv(_t("hormone_coupling.csv"))
    pvc = pd.read_csv(_t("peripheral_vs_central.csv"))
    main = hc[hc["hormone"].isin(["pdg", "e3g"])].dropna(subset=["partial_rho"])
    order = (
        main[main["hormone"] == "pdg"].reindex(
            main[main["hormone"] == "pdg"]["partial_rho"].abs().sort_values(ascending=False).index
        )["feature"].head(8).tolist()
    )
    main = main[main["feature"].isin(order)]
    labels = main.drop_duplicates("feature").set_index("feature")["label"].to_dict()
    arms = main.drop_duplicates("feature").set_index("feature")["arm"].to_dict()

    fig, (axA, axB) = plt.subplots(1, 2, figsize=(13, 5.5), gridspec_kw={"width_ratios": [2.1, 1]})
    y = np.arange(len(order))
    pdg = [main[(main.feature == f) & (main.hormone == "pdg")]["partial_rho"].mean() for f in order]
    e3g = [main[(main.feature == f) & (main.hormone == "e3g")]["partial_rho"].mean() for f in order]
    axA.axvline(0, color="0.5", lw=0.8)
    axA.scatter(pdg, y, color="#d6604d", s=60, label="Progesterone (PdG)", zorder=3)
    axA.scatter(e3g, y, color="#2a7fb8", s=60, label="Estrogen (E3G)", zorder=3)
    axA.set_yticks(y)
    axA.set_yticklabels([f"{labels[f]}  [{arms[f]}]" for f in order], fontsize=8)
    axA.set_xlabel("Drift-controlled correlation with hormone (partial Spearman, n=29)")
    axA.set_title("Which hormone moves each feature")
    axA.legend(fontsize=8)

    pv = pvc[pvc["task"] == "prosody"]
    arms_o = ["peripheral", "central"]
    horms = ["pdg", "e3g"]
    x = np.arange(len(arms_o))
    w = 0.35
    for i, h in enumerate(horms):
        vals = [pv[(pv.arm == a) & (pv.hormone == h)]["mean_abs_partial_rho"].mean() for a in arms_o]
        axB.bar(x + (i - 0.5) * w, vals, w, label={"pdg": "PdG", "e3g": "E3G"}[h],
                color={"pdg": "#d6604d", "e3g": "#2a7fb8"}[h])
    axB.set_xticks(x)
    axB.set_xticklabels(["Cover\n(tissue)", "Pitch control\n(brain)"])
    axB.set_ylabel("Average coupling strength")
    axB.set_title("Two pathways")
    axB.legend(fontsize=8)
    return _save(fig, "fig03_two_hormones.png")


def fig_rate_variability():
    p = _t("variability_by_pdg_rate.csv")
    if not p.exists():
        return None
    v = pd.read_csv(p)
    fig, ax = plt.subplots(figsize=(7, 5))
    chans = ["cover", "geometry"]
    groups = ["slow", "fast"]
    x = np.arange(len(chans))
    w = 0.35
    for i, g in enumerate(groups):
        vals = [v[(v.channel == c) & (v.pdg_rate_group == g)]["dispersion_iqr_z"].mean() for c in chans]
        ax.bar(x + (i - 0.5) * w, vals, w, label=f"{g} progesterone change",
               color={"slow": "#9ecae1", "fast": "#d6604d"}[g])
    ax.set_xticks(x)
    ax.set_xticklabels(["Cover (mucosa/closure)", "Vocal-tract geometry"])
    ax.set_ylabel("Day-to-day voice variability (within-cycle units)")
    ax.set_title("Rate, not level\n"
                 "The cover wobbles more on fast-progesterone-change days; geometry does not")
    ax.legend(fontsize=8)
    return _save(fig, "fig04_rate_variability.png")


def fig_premenstrual():
    pw = pd.read_csv(_t("premenstrual_window.csv"))
    windows = ["follicular_z", "mid_luteal_z", "premenstrual_z"]
    wlabels = ["Follicular", "Mid-luteal", "Premenstrual"]
    fig, ax = plt.subplots(figsize=(8.5, 5))
    x = np.arange(len(windows))
    for _, row in pw.iterrows():
        style = "-o" if row["arm"] == "central" else "--s"
        ax.plot(x, [row[w] for w in windows], style, label=f"{row['label']} [{row['arm']}]")
    ax.axhline(0, color="0.6", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(wlabels)
    ax.set_ylabel("Voice level (within-cycle units; 0 = cycle average)")
    ax.set_title("The premenstrual spike\n"
                 "Timbre and pitch-control instability peak in the late-luteal/premenstrual window")
    ax.legend(fontsize=8, loc="upper left")
    return _save(fig, "fig05_premenstrual.png")


def fig_body_context():
    h = pd.read_csv(_t("hrv_context.csv"))
    fig, ax = plt.subplots(figsize=(7.5, 4))
    y = np.arange(len(h))
    colors = ["#d6604d" if d > 0 else "#2a7fb8" for d in h["cliffs_delta_luteal_vs_foll"]]
    ax.barh(y, h["cliffs_delta_luteal_vs_foll"], color=colors)
    ax.axvline(0, color="0.5", lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(h["signal"])
    ax.set_xlabel("Luteal vs follicular effect (Cliff's delta)")
    ax.set_title("Supporting context: the body confirms the cycle is real")
    return _save(fig, "fig06_body_context.png")


def main():
    localization_paths().figures_dir.mkdir(parents=True, exist_ok=True)
    for fn in (fig_localization_map, fig_sensitivity_floor, fig_two_hormones,
               fig_rate_variability, fig_premenstrual, fig_body_context):
        out = fn()
        if out is not None:
            print("wrote", out)


if __name__ == "__main__":
    main()
