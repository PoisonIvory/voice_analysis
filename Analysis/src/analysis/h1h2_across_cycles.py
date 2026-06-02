"""Does the F0/loudness-residualized H1-H2 cycle signal persist across cycles?

The hormone-coupling test only sees the ~2 cycles with Inito draws. Here we use a
calendar-position progesterone proxy (`cycle_position.progesterone_proxy`) to
reach all labeled cycles, and ask two questions:

1. Validation: does the proxy track measured PdG where we have both? (It should,
   or the proxy is meaningless.)
2. Persistence: does the residualized H1-H2 still rise toward the luteal/high-
   progesterone end (a) when correlated against the proxy across ALL voice days,
   and (b) cycle by cycle, including the cycles with no hormone data?

Pure computation + one figure. Reuses the F0/loudness residualization so we are
testing the *tissue-property* residual, not raw H1-H2.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from .analysis_dataset import build_analysis_table
from .cycle_position import progesterone_proxy
from .residualize import residualize
from . import stats as st

H1H2 = "egemaps_logRelF0-H1-H2_sma3nz_amean"
F0 = "egemaps_F0semitoneFrom27.5Hz_sma3nz_amean"
LOUDNESS = "egemaps_loudness_sma3_amean"
TASKS = ("vowel", "prosody")

FOLLICULAR = "#2BA3E8"
LUTEAL = "#5E4DB3"
RAW = "#C7CEDA"
RESID = "#30A37A"
PROGESTERONE = "#5E4DB3"
INK = "#1A1E2E"
GRID = "#D8DCE6"
CYCLE_COLORS = ["#E8913B", "#2BA3E8", "#5E4DB3", "#30A37A", "#C2477F"]


def _col(base: str, task: str) -> str:
    return f"{task}_{base}"


def _spearman(s: pd.DataFrame, a: str, b: str) -> tuple[float, float, int]:
    sub = s[[a, b]].apply(pd.to_numeric, errors="coerce").dropna()
    if len(sub) < 5:
        return np.nan, np.nan, len(sub)
    rho, p = stats.spearmanr(sub[a], sub[b])
    return float(rho), float(p), len(sub)


def build() -> tuple[pd.DataFrame, dict]:
    df = build_analysis_table()
    df["date_ord"] = df["date"].map(lambda d: d.toordinal() if pd.notna(d) else np.nan)
    df["pdg_proxy"] = progesterone_proxy(df)
    voice = df[df["has_voice"]].copy()

    # Residualize H1-H2 on F0 + loudness for each task (tissue-property residual).
    for task in TASKS:
        both = residualize(voice, _col(H1H2, task), [_col(F0, task), _col(LOUDNESS, task)])
        df[f"{task}_H1H2_resid_f0_loud"] = both.residual

    # 1) Proxy validation against measured PdG.
    val = df[df["pdg"].notna() & df["pdg_proxy"].notna()]
    proxy_rho, proxy_p, proxy_n = _spearman(val, "pdg_proxy", "pdg")

    # 2a) Residual H1-H2 vs proxy, pooled over ALL voice days (all cycles) vs
    #     restricted to the hormone window, for comparison.
    pooled_rows = []
    for task in TASKS:
        resid = f"{task}_H1H2_resid_f0_loud"
        all_voice = df[df["has_voice"] & df["pdg_proxy"].notna()]
        horm_voice = df[df["has_voice"] & df["has_hormones"]]
        rho_all, p_all, n_all = _spearman(all_voice, resid, "pdg_proxy")
        # partial out date to strip shared drift, as in the main report
        partial_all, _ = st.partial_spearman(all_voice, resid, "pdg_proxy", "date_ord")
        rho_h, p_h, n_h = _spearman(horm_voice, resid, "pdg")
        pooled_rows.append(dict(
            task=task,
            rho_proxy_all_cycles=rho_all, p_proxy_all_cycles=p_all, n_all=n_all,
            partial_rho_proxy_date=partial_all,
            rho_measured_pdg_hormone_window=rho_h, n_hormone=n_h,
        ))
    pooled = pd.DataFrame(pooled_rows)

    # 2b) Per-cycle luteal-vs-follicular contrast on the residual (and raw).
    percycle_rows = []
    labeled = df[df["phase_label"].notna() & df["has_voice"]]
    for cs, g in labeled.groupby("cycle_start_date"):
        for task in TASKS:
            raw_col, resid_col = _col(H1H2, task), f"{task}_H1H2_resid_f0_loud"
            foll_raw = pd.to_numeric(g.loc[g.phase_label == "follicular", raw_col], errors="coerce").dropna()
            lut_raw = pd.to_numeric(g.loc[g.phase_label == "luteal", raw_col], errors="coerce").dropna()
            foll_res = pd.to_numeric(g.loc[g.phase_label == "follicular", resid_col], errors="coerce").dropna()
            lut_res = pd.to_numeric(g.loc[g.phase_label == "luteal", resid_col], errors="coerce").dropna()
            percycle_rows.append(dict(
                cycle_start=pd.Timestamp(cs).date(), task=task,
                n_foll=len(foll_res), n_lut=len(lut_res),
                has_hormones=bool(g["has_hormones"].any()),
                raw_lut_minus_foll=(float(lut_raw.median() - foll_raw.median())
                                    if len(foll_raw) and len(lut_raw) else np.nan),
                resid_lut_minus_foll=(float(lut_res.median() - foll_res.median())
                                      if len(foll_res) and len(lut_res) else np.nan),
                resid_cliffs_delta=(st.cliffs_delta(lut_res.to_numpy(), foll_res.to_numpy())
                                    if len(foll_res) and len(lut_res) else np.nan),
            ))
    percycle = pd.DataFrame(percycle_rows)

    context = dict(proxy_rho=proxy_rho, proxy_p=proxy_p, proxy_n=proxy_n)
    return df, {"pooled": pooled, "percycle": percycle, "context": context}


def _style() -> None:
    plt.rcParams.update({
        "figure.dpi": 150, "savefig.dpi": 150, "font.size": 11,
        "axes.titlesize": 12, "axes.titleweight": "bold", "axes.labelsize": 10,
        "axes.edgecolor": "#9AA3B2", "axes.linewidth": 0.8, "axes.grid": True,
        "grid.color": GRID, "grid.linewidth": 0.7, "axes.axisbelow": True,
        "text.color": INK, "axes.labelcolor": INK, "xtick.color": INK,
        "ytick.color": INK, "figure.facecolor": "white", "axes.facecolor": "white",
    })


def render_figure(df: pd.DataFrame, res: dict, out: Path) -> Path:
    _style()
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.6))
    ctx = res["context"]

    # Panel A: proxy validation against measured PdG.
    ax = axes[0]
    val = df[df["pdg"].notna() & df["pdg_proxy"].notna()]
    ax.scatter(val["pdg_proxy"], val["pdg"], color=PROGESTERONE, s=28, alpha=0.8)
    ax.set_xlabel("Cycle-position progesterone proxy (0..1)")
    ax.set_ylabel("Measured PdG (Inito)")
    ax.set_title("Proxy tracks measured progesterone")
    ax.text(0.04, 0.95, f"rho = {ctx['proxy_rho']:+.2f}\n(n = {ctx['proxy_n']})",
            transform=ax.transAxes, va="top", fontsize=9,
            bbox=dict(boxstyle="round", fc="white", ec="#9AA3B2", alpha=0.9))

    # Panel B: residual H1-H2 (prosody) vs proxy across ALL cycles, colored by cycle.
    ax = axes[1]
    task = "prosody"
    resid_col = f"{task}_H1H2_resid_f0_loud"
    sub = df[df["has_voice"] & df["pdg_proxy"].notna() & df[resid_col].notna()]
    cycles = sorted(sub["cycle_start_date"].dropna().unique())
    for i, cs in enumerate(cycles):
        gg = sub[sub["cycle_start_date"] == cs]
        horm = gg["has_hormones"].any()
        ax.scatter(gg["pdg_proxy"], gg[resid_col],
                   color=CYCLE_COLORS[i % len(CYCLE_COLORS)], s=34,
                   alpha=0.85, edgecolors=INK if horm else "none", linewidths=0.8,
                   label=f"{pd.Timestamp(cs).date()}{' *' if horm else ''}")
    pooled = res["pooled"]
    rho = pooled.loc[pooled.task == task, "rho_proxy_all_cycles"].iloc[0]
    n = int(pooled.loc[pooled.task == task, "n_all"].iloc[0])
    ax.set_xlabel("Progesterone proxy (all cycles)")
    ax.set_ylabel("Residual H1-H2 (connected speech)")
    ax.set_title("Residual H1-H2 rises with proxy across cycles")
    ax.text(0.04, 0.95, f"rho = {rho:+.2f}\n(n = {n})", transform=ax.transAxes,
            va="top", fontsize=9, bbox=dict(boxstyle="round", fc="white", ec="#9AA3B2", alpha=0.9))
    ax.legend(fontsize=7, loc="lower right", title="cycle (* = hormones)", title_fontsize=7)

    # Panel C: per-cycle luteal-minus-follicular residual H1-H2 (prosody + vowel).
    ax = axes[2]
    pc = res["percycle"].copy()
    pc = pc[pc["resid_lut_minus_foll"].notna()]
    order = sorted(pc["cycle_start"].unique())
    width = 0.38
    for j, task in enumerate(TASKS):
        block = pc[pc["task"] == task].set_index("cycle_start").reindex(order)
        y = np.arange(len(order))
        vals = block["resid_lut_minus_foll"].to_numpy(dtype=float)
        ax.barh(y + (width/2 if j == 0 else -width/2), vals, height=width,
                color=FOLLICULAR if task == "vowel" else LUTEAL, label=task.capitalize())
    ax.axvline(0, color=INK, lw=0.8)
    ax.set_yticks(np.arange(len(order)))
    ax.set_yticklabels([str(c) for c in order], fontsize=8)
    ax.set_xlabel("Luteal - follicular residual H1-H2")
    ax.set_title("Per-cycle: luteal > follicular?")
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(axis="y", visible=False)

    fig.suptitle("Residualized H1-H2 vs cycle position: directionally consistent across cycles, but limited by phase coverage outside the hormone window",
                 fontsize=11.5, fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def main() -> None:
    from .config import default_paths

    paths = default_paths()
    df, res = build()

    tables_dir = paths.outputs_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    res["pooled"].to_csv(tables_dir / "h1h2_proxy_pooled.csv", index=False)
    res["percycle"].to_csv(tables_dir / "h1h2_proxy_percycle.csv", index=False)

    fig_path = render_figure(df, res, paths.figures_dir / "fig10_h1h2_across_cycles.png")

    ctx = res["context"]
    pd.set_option("display.width", 170)
    pd.set_option("display.max_columns", 30)
    print(f"proxy vs measured PdG: rho={ctx['proxy_rho']:+.3f}  p={ctx['proxy_p']:.4f}  n={ctx['proxy_n']}")
    print("\n=== POOLED: residual H1-H2 vs progesterone proxy ===")
    print(res["pooled"].to_string(index=False))
    print("\n=== PER CYCLE: luteal-vs-follicular residual H1-H2 ===")
    print(res["percycle"].to_string(index=False))
    print(f"\nfigure: {fig_path}")


if __name__ == "__main__":
    main()
