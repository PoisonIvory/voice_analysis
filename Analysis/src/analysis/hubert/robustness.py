"""Architecture robustness: is the result a HuBERT artifact?

Single responsibility: quantify cross-backbone agreement so any cycle finding
(or null) can be shown to hold across three SSL training objectives - HuBERT
(masked unit prediction), WavLM (masked + denoising), wav2vec2 (contrastive) -
all 768-d and pre-trained on English LibriSpeech 960h. Two views, following the
paper's cross-model section: inter-model Spearman on the per-recording composite
(ranking agreement) and cosine similarity of the mean consonant d-prime profile
(shape agreement). Absolute magnitudes are not comparable across architectures,
so both measures are scale-free by construction.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from .taxonomy import COMPOSITE_CONSONANT, CONSONANT_CONTRASTS, dprime_col


def _backbone_pairs(backbones: list[str]) -> list[tuple[str, str]]:
    return [
        (backbones[i], backbones[j])
        for i in range(len(backbones))
        for j in range(i + 1, len(backbones))
    ]


def inter_backbone_rho(df: pd.DataFrame) -> pd.DataFrame:
    """Spearman rho between backbones on per-recording composite consonant d-prime."""
    wide = df.pivot_table(index="recordingId", columns="backbone", values=COMPOSITE_CONSONANT)
    rows: list[dict[str, object]] = []
    for a, b in _backbone_pairs(sorted(wide.columns)):
        sub = wide[[a, b]].dropna()
        rho = stats.spearmanr(sub[a], sub[b]).statistic if len(sub) >= 3 else float("nan")
        rows.append({"backbone_a": a, "backbone_b": b, "n": len(sub), "spearman_rho": round(float(rho), 3)})
    return pd.DataFrame(rows)


def profile_cosine(df: pd.DataFrame) -> pd.DataFrame:
    """Cosine similarity of mean 5-consonant d-prime profiles across backbones."""
    cols = [dprime_col(k) for k in CONSONANT_CONTRASTS]
    profiles = df.groupby("backbone")[cols].mean()
    rows: list[dict[str, object]] = []
    for a, b in _backbone_pairs(sorted(profiles.index)):
        va, vb = profiles.loc[a].to_numpy(), profiles.loc[b].to_numpy()
        cos = float(np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb)))
        rows.append({"backbone_a": a, "backbone_b": b, "profile_cosine": round(cos, 4)})
    return pd.DataFrame(rows)
