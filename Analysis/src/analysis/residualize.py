"""Ordinary-least-squares residualization for confound control.

Single responsibility: given a target column and one or more nuisance covariates,
fit a linear model on the rows where all are observed and return the residuals
(target minus the part linearly predictable from the covariates), together with
the variance explained.

This is the "regress out F0 and loudness, keep what is left" operation used to
test whether the H1-H2 cycle signal is a mechanical artifact of pitch/intensity.
The nuisance model is fit on *all* available voice days (not just hormone days)
so the F0/loudness coefficients are estimated from as much data as possible.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Residualization:
    residual: pd.Series          # index-aligned to the input frame (NaN where unused)
    n: int                       # observations used to fit the model
    r_squared: float             # variance of target explained by covariates
    coefficients: dict[str, float]  # covariate -> slope (intercept under "_intercept")


def residualize(df: pd.DataFrame, target: str, covariates: list[str]) -> Residualization:
    """Regress `target` on `covariates` (OLS) and return the residuals.

    Rows missing the target or any covariate are dropped from the fit and receive
    a NaN residual. R-squared is the ordinary coefficient of determination.
    """
    cols = [target, *covariates]
    sub = df[cols].apply(pd.to_numeric, errors="coerce").dropna()
    n = len(sub)
    if n <= len(covariates) + 1:
        return Residualization(pd.Series(np.nan, index=df.index), n, np.nan, {})

    y = sub[target].to_numpy(dtype=float)
    X = np.column_stack([np.ones(n), sub[covariates].to_numpy(dtype=float)])

    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    fitted = X @ beta
    resid = y - fitted

    ss_res = float(np.sum(resid**2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan

    out = pd.Series(np.nan, index=df.index, dtype=float)
    out.loc[sub.index] = resid

    coeffs = {"_intercept": float(beta[0])}
    coeffs.update({cov: float(b) for cov, b in zip(covariates, beta[1:])})
    return Residualization(out, n, float(r2), coeffs)
