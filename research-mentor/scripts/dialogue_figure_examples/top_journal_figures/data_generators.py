from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
from sklearn.preprocessing import StandardScaler

from style_config import GLOBAL_SEED


def rng_for(name: str) -> np.random.Generator:
    digest = hashlib.sha256(f"{GLOBAL_SEED}:{name}".encode("utf-8")).digest()
    seed = int.from_bytes(digest[:8], "little") % (2**32)
    return np.random.default_rng(seed)


def ar1_noise(rng: np.random.Generator, n: int, scale: float, rho: float = 0.72) -> np.ndarray:
    out = np.zeros(n)
    innovations = rng.normal(0, scale, n)
    for i in range(1, n):
        out[i] = rho * out[i - 1] + innovations[i]
    return out


def smooth_series(values: np.ndarray, window: int = 17, polyorder: int = 3) -> np.ndarray:
    window = min(window, len(values) - 1 if len(values) % 2 == 0 else len(values))
    if window % 2 == 0:
        window -= 1
    if window <= polyorder:
        return values.copy()
    return savgol_filter(values, window_length=window, polyorder=polyorder, mode="interp")


def generate_graphcast_data() -> dict[str, pd.DataFrame]:
    rng = rng_for("graphcast")
    days = np.arange(1, 11)
    early = 0.020 * np.log1p(days)
    mid = 0.026 * np.maximum(days - 3, 0) ** 1.22
    late = 0.018 * np.maximum(days - 7, 0) ** 1.45
    ref_rmse = 0.19 + early + mid + late + ar1_noise(rng, len(days), 0.004)
    improvement = 0.035 + 0.055 / (1 + np.exp(-(days - 5.2))) + 0.010 * np.sin(days / 1.7)
    graph_rmse = ref_rmse * (1 - improvement) + ar1_noise(rng, len(days), 0.002)
    rmse = pd.DataFrame(
        {
            "day": days,
            "GraphCast": graph_rmse,
            "Reference": ref_rmse,
            "GraphCast_ci": 0.011 + 0.002 * np.sqrt(days),
            "Reference_ci": 0.013 + 0.0023 * np.sqrt(days),
        }
    )
    rmse["relative_diff"] = (rmse["GraphCast"] - rmse["Reference"]) / rmse["Reference"]

    plateau = 0.998 - 0.00045 * np.minimum(days, 3)
    mid_drop = 0.0052 * np.maximum(days - 3, 0) ** 1.15
    late_drop = 0.0033 * np.maximum(days - 7, 0) ** 1.55
    ref_acc = plateau - mid_drop - late_drop + ar1_noise(rng, len(days), 0.0007)
    acc_gain = 0.006 + 0.006 / (1 + np.exp(-(days - 5))) + 0.0015 * np.cos(days / 2.2)
    graph_acc = np.minimum(1.0, ref_acc + acc_gain + ar1_noise(rng, len(days), 0.0005))
    acc = pd.DataFrame({"day": days, "GraphCast": graph_acc, "Reference": ref_acc})

    variables = ["u", "v", "z", "t", "q", "t2m", "u10", "v10", "msl"]
    rows = []
    base_patterns = {
        "u": (-0.08, -0.12, 0.018),
        "v": (-0.075, -0.115, 0.016),
        "z": (-0.11, -0.135, 0.010),
        "t": (-0.10, -0.125, 0.012),
        "q": (-0.065, -0.095, 0.035),
        "t2m": (-0.055, -0.070, 0.015),
        "u10": (-0.035, -0.120, 0.018),
        "v10": (-0.040, -0.118, 0.019),
        "msl": (-0.070, -0.098, 0.012),
    }
    for idx, variable in enumerate(variables):
        start, end, volatility = base_patterns[variable]
        curvature = start + (end - start) * (1 - np.exp(-days / (3.2 + 0.18 * idx)))
        wave = volatility * np.sin(days * (0.7 + 0.05 * idx) + idx)
        correlated = ar1_noise(rng, len(days), volatility * 0.25)
        values = np.clip(curvature + wave + correlated, -0.18, 0.18)
        for day, value in zip(days, values):
            rows.append({"variable": variable, "day": day, "skill": value})
    heatmap = pd.DataFrame(rows)
    return {"rmse": rmse, "acc": acc, "heatmap": heatmap}


def generate_alphago_data() -> pd.DataFrame:
    rng = rng_for("alphago")
    hours = np.arange(0, 73, 2)
    rows = []
    for variant in ["Reinforcement learning", "Supervised learning"]:
        h = hours.astype(float)
        if variant.startswith("Reinforcement"):
            elo = (
                150 * h
                - 1.95 * np.maximum(h - 15, 0) ** 1.35
                + 820 * (1 - np.exp(-np.maximum(h - 15, 0) / 16))
                + 420 * np.tanh((h - 38) / 12)
            )
            elo = 5200 * (elo - elo.min()) / (elo.max() - elo.min())
            acc = 0.225 + 0.045 * (1 - np.exp(-h / 45)) + 0.008 * np.tanh((h - 35) / 18)
            mse = 0.285 - 0.115 * (1 - np.exp(-h / 10)) - 0.070 * (1 - np.exp(-np.maximum(h - 18, 0) / 36))
        else:
            elo = (
                135 * h
                - 2.35 * np.maximum(h - 14, 0) ** 1.32
                + 450 * (1 - np.exp(-np.maximum(h - 18, 0) / 20))
            )
            elo = 3750 * (elo - elo.min()) / (elo.max() - elo.min())
            acc = 0.505 + 0.035 * (1 - np.exp(-h / 18)) - 0.005 * np.tanh((h - 55) / 12)
            mse = 0.280 - 0.105 * (1 - np.exp(-h / 12)) - 0.050 * (1 - np.exp(-np.maximum(h - 20, 0) / 42))
        taper = np.linspace(1.0, 0.45, len(h))
        elo += ar1_noise(rng, len(h), 38) + 22 * np.sin(h / 7)
        acc += ar1_noise(rng, len(h), 0.0025)
        mse += ar1_noise(rng, len(h), 0.004) * taper
        for hour, e, a, m in zip(hours, elo, acc, mse):
            rows.append(
                {
                    "hour": hour,
                    "variant": variant,
                    "elo": e,
                    "move_accuracy": np.clip(a, 0.18, 0.57),
                    "value_mse": np.clip(m, 0.08, 0.30),
                }
            )
    return pd.DataFrame(rows)


def generate_recovery_patient_data() -> pd.DataFrame:
    rng = rng_for("recovery")
    design = {
        ("Invasive mechanical ventilation", "Dexamethasone"): (324, 0.285, 1.40),
        ("Invasive mechanical ventilation", "Usual care"): (683, 0.410, 1.25),
        ("Oxygen only", "Dexamethasone"): (1279, 0.225, 1.32),
        ("Oxygen only", "Usual care"): (2604, 0.265, 1.25),
        ("No respiratory support", "Dexamethasone"): (501, 0.155, 1.35),
        ("No respiratory support", "Usual care"): (1034, 0.135, 1.30),
    }
    rows = []
    patient_id = 1
    for (subgroup, treatment), (n, p28, shape) in design.items():
        scale = 28 / (-np.log(1 - p28)) ** (1 / shape)
        frailty = rng.lognormal(mean=-0.5 * 0.28**2, sigma=0.28, size=n)
        event_time = scale * (-np.log(rng.uniform(size=n)) / frailty) ** (1 / shape)
        censor_time = np.full(n, 28.0)
        early_censor = rng.random(n) < 0.025
        censor_time[early_censor] = rng.uniform(23.5, 28.0, early_censor.sum())
        observed = np.minimum(event_time, censor_time)
        event = (event_time <= censor_time).astype(int)
        for et, ct, ot, ev in zip(event_time, censor_time, observed, event):
            rows.append(
                {
                    "patient_id": patient_id,
                    "treatment_group": treatment,
                    "subgroup": subgroup,
                    "event_time": float(et),
                    "censor_time": float(ct),
                    "observed_time": float(ot),
                    "event_indicator": int(ev),
                }
            )
            patient_id += 1
    return pd.DataFrame(rows)


def km_estimate(durations: np.ndarray, events: np.ndarray, max_time: float = 28.0) -> pd.DataFrame:
    durations = np.asarray(durations, dtype=float)
    events = np.asarray(events, dtype=int)
    event_times = np.unique(durations[events == 1])
    times = [0.0]
    survival = [1.0]
    current = 1.0
    for time in event_times:
        at_risk = np.sum(durations >= time)
        deaths = np.sum((durations == time) & (events == 1))
        if at_risk > 0:
            current *= 1 - deaths / at_risk
        times.append(float(time))
        survival.append(float(current))
    if times[-1] < max_time:
        times.append(max_time)
        survival.append(float(current))
    return pd.DataFrame({"time": times, "survival": survival, "mortality": 1 - np.array(survival)})


def at_risk_counts(df: pd.DataFrame, times: list[int]) -> dict[str, list[int]]:
    counts = {}
    for treatment, group in df.groupby("treatment_group"):
        counts[treatment] = [int((group["observed_time"] >= time).sum()) for time in times]
    return counts


def generate_step5_data() -> dict[str, pd.DataFrame]:
    rng = rng_for("step5")
    weeks = np.array([0, 4, 8, 12, 16, 20, 28, 36, 44, 52, 68, 84, 92, 104])
    early = 1 - np.exp(-np.minimum(weeks, 20) / 9)
    mid = 1 - np.exp(-np.maximum(np.minimum(weeks, 60) - 20, 0) / 24)
    late = 1 - np.exp(-np.maximum(weeks - 60, 0) / 40)
    sema = -9.0 * early / early.max() - 4.8 * mid - 1.4 * late
    sema += 0.22 * np.sin(weeks / 14) + ar1_noise(rng, len(weeks), 0.05)
    sema -= sema[-1] + 15.2
    placebo = -1.45 * early / early.max() - 0.9 * mid + 0.25 * late
    placebo += 0.14 * np.sin(weeks / 16 + 1.5) + ar1_noise(rng, len(weeks), 0.04)
    placebo -= placebo[-1] + 2.6
    rows = []
    for treatment, values, n_start in [
        ("Semaglutide", sema, 152),
        ("Placebo", placebo, 152),
    ]:
        n = np.round(n_start - np.linspace(0, 22, len(weeks)) + rng.normal(0, 1, len(weeks))).astype(int)
        sem = (0.28 + 0.16 * (1 - n / n_start)) * (1.10 if treatment == "Semaglutide" else 0.86)
        for week, value, se, nn in zip(weeks, values, sem, n):
            rows.append(
                {
                    "week": int(week),
                    "treatment": treatment,
                    "mean_change_pct": float(value),
                    "sem": float(se),
                    "n": int(nn),
                }
            )
    endpoint = pd.DataFrame(
        {
            "treatment": ["Semaglutide", "Placebo"],
            "percent": [77.1, 34.4],
        }
    )
    return {"trajectory": pd.DataFrame(rows), "endpoint": endpoint}


def generate_alphafold_data() -> pd.DataFrame:
    rng = rng_for("alphafold")
    names = [
        "AlphaFold",
        "Baker",
        "Zhang",
        "BAKER-ROSETTASERVER",
        "MULTICOM",
        "tFold",
        "Yang-Server",
        "FALCON",
        "RaptorX",
        "QUARK",
        "D-I-TASSER",
        "MULTICOM-CLUSTER",
        "Bhattacharya",
        "Seder",
        "Jones-UCL",
        "ProQ",
        "IntFOLD",
    ]
    medians = np.array([89.2, 80.5, 76.8, 72.6, 70.1, 68.2, 66.8, 64.5, 62.2, 60.5, 58.6, 56.9, 55.2, 53.8, 52.1, 50.5, 48.8])
    medians += np.r_[0, ar1_noise(rng, len(names) - 1, 0.65, rho=0.35)]
    widths = rng.uniform(1.2, 4.8, len(names))
    asym = rng.uniform(-0.8, 0.8, len(names))
    low = medians - widths * (1.0 + np.maximum(asym, 0))
    high = medians + widths * (1.0 + np.maximum(-asym, 0))
    return pd.DataFrame(
        {
            "group_name": names,
            "median_score": medians,
            "ci_low": low,
            "ci_high": high,
            "highlight": [name == "AlphaFold" for name in names],
        }
    )


def interpolate_intersection(years: np.ndarray, total: np.ndarray, biomass: np.ndarray) -> tuple[float, float]:
    diff = total - biomass
    idx = np.where(np.sign(diff[:-1]) != np.sign(diff[1:]))[0]
    if len(idx) == 0:
        return float("nan"), float("nan")
    i = idx[0]
    x0, x1 = years[i], years[i + 1]
    y0, y1 = diff[i], diff[i + 1]
    year = x0 - y0 * (x1 - x0) / (y1 - y0)
    value = np.interp(year, years, total)
    return float(year), float(value)


def generate_anthropogenic_mass_data() -> tuple[pd.DataFrame, tuple[float, float]]:
    years = np.arange(1900, 2026)
    x = years - 1900
    concrete = 0.012 * np.exp(0.0392 * x) * (1 + 0.13 / (1 + np.exp(-(years - 1955) / 11)))
    aggregates = 0.010 * np.exp(0.0382 * x) * (1 + 0.10 / (1 + np.exp(-(years - 1965) / 9)))
    bricks = 0.006 * np.exp(0.0305 * x) * (1 + 0.05 * np.sin(x / 23))
    asphalt = 0.0025 * np.exp(0.0375 * x) * (1 + 0.18 / (1 + np.exp(-(years - 1970) / 7)))
    metals = 0.0018 * np.exp(0.0365 * x) * (1 + 0.12 * np.sin(x / 31 + 0.4))
    other = 0.0014 * np.exp(0.0345 * x) * (1 + 0.08 * np.cos(x / 25))
    total = concrete + aggregates + bricks + asphalt + metals + other
    target_total_2020 = 1.04
    scale = target_total_2020 / total[np.where(years == 2020)[0][0]]
    values = [series * scale for series in [concrete, aggregates, bricks, asphalt, metals, other]]
    biomass = 1.17 - 0.00125 * x + 0.025 * np.sin(x / 34) - 0.020 / (1 + np.exp(-(years - 1975) / 12))
    biomass_sd = biomass * (0.115 + 0.018 * np.sin(x / 27 + 0.6) + 0.012 * (x / x.max()))
    df = pd.DataFrame(
        {
            "year": years,
            "Concrete": values[0],
            "Aggregates": values[1],
            "Bricks": values[2],
            "Asphalt": values[3],
            "Metals": values[4],
            "Other": values[5],
            "biomass_mean": biomass,
            "biomass_low": biomass - biomass_sd,
            "biomass_high": biomass + biomass_sd,
            "extrapolated": years > 2015,
        }
    )
    cross = interpolate_intersection(years, df[["Concrete", "Aggregates", "Bricks", "Asphalt", "Metals", "Other"]].sum(axis=1).to_numpy(), biomass)
    return df, cross


@dataclass
class RationalityPanel:
    raw: np.ndarray
    smooth: np.ndarray
    lower: np.ndarray
    upper: np.ndarray


def generate_rationality_data() -> dict[str, object]:
    rng = rng_for("rationality")
    years = np.arange(1800, 2021)
    corpora = ["English corpus", "Spanish corpus", "German corpus", "Italian corpus"]
    configs = [
        (1850, 1982, 0.85, 0.23, 0.18),
        (1900, 1975, 0.65, 0.31, 0.25),
        (1875, 1990, 0.44, 0.18, 0.14),
        (1930, 1968, 0.74, 0.38, 0.30),
    ]
    data = {}
    for idx, (corpus, (rise_year, fall_year, amp, noise, ci_width)) in enumerate(zip(corpora, configs)):
        y = years.astype(float)
        rise = 2 / (1 + np.exp(-(y - rise_year) / (22 + 3 * idx))) - 1
        fall = 2 / (1 + np.exp(-(y - fall_year) / (9 + idx))) - 1
        pc_base = amp * (rise - 0.85 * fall)
        pc_base += 0.13 * np.sin((y - 1800) / (20 + 2 * idx)) + 0.06 * np.sin((y - 1840) / 7.5)
        if idx == 1:
            pc_base += -0.24 / (1 + np.exp(-(y - 1935) / 5))
        if idx == 3:
            pc_base += 0.28 * np.exp(-0.5 * ((y - 1970) / 13) ** 2)
        pc_raw = pc_base + ar1_noise(rng, len(years), noise, rho=0.62)
        pc_smooth = smooth_series(pc_raw, 19, 3)

        intuition_base = -0.50 * pc_base + 0.18 * np.sin((y - 1810) / (15 + idx))
        intuition_raw = intuition_base + ar1_noise(rng, len(years), noise * 0.55, rho=0.66)
        intuition_smooth = smooth_series(intuition_raw, 17, 3)

        rational_base = 0.55 * pc_base - 0.18 * np.exp(-0.5 * ((y - (fall_year + 8)) / 18) ** 2)
        rational_raw = rational_base + ar1_noise(rng, len(years), noise * 0.50, rho=0.65)
        rational_smooth = smooth_series(rational_raw, 17, 3)

        sentiment = pd.DataFrame(
            {
                "positive": 0.42 + 0.055 * np.sin((y - 1810) / (32 - idx)) + 0.035 * rise,
                "neutral": 0.52 + 0.035 * np.cos((y - 1835) / (38 + 2 * idx)) - 0.012 * fall,
                "negative": 0.30 + 0.050 * np.sin((y - 1875) / (26 + idx) + 1.7) + 0.025 * fall,
            },
            index=years,
        )
        sentiment += rng.normal(0, [0.004, 0.003, 0.004], sentiment.shape)

        def panel(raw, smooth, multiplier=1.0):
            width = ci_width * multiplier * (0.9 + 0.25 * np.sin((y - 1800) / 40 + idx))
            return RationalityPanel(raw=raw, smooth=smooth, lower=smooth - width, upper=smooth + width)

        data[corpus] = {
            "pc2": panel(pc_raw, pc_smooth, 0.95),
            "sentiment": sentiment,
            "intuition": panel(intuition_raw, intuition_smooth, 0.70),
            "rationality": panel(rational_raw, rational_smooth, 0.65),
        }
    return {"years": years, "corpora": corpora, "data": data}


def generate_moral_machine_data() -> dict[str, object]:
    rng = rng_for("moral_machine")
    features = [
        "humans",
        "young",
        "female",
        "lawful",
        "pedestrians",
        "fit",
        "high status",
        "more lives",
        "inaction",
    ]
    clusters = {
        "Western-like": np.array([0.80, 0.12, -0.10, 0.55, 0.68, 0.10, -0.28, 0.70, -0.20]),
        "Eastern-like": np.array([0.40, 0.42, 0.05, 0.20, -0.05, 0.18, 0.32, 0.35, 0.26]),
        "Southern-like": np.array([0.55, 0.22, 0.62, 0.08, 0.35, -0.18, 0.05, 0.52, 0.08]),
    }
    countries = {
        "Western-like": [
            "United States",
            "Canada",
            "United Kingdom",
            "France",
            "Germany",
            "Netherlands",
            "Sweden",
            "Norway",
            "Denmark",
            "Australia",
            "New Zealand",
            "Ireland",
            "Belgium",
            "Switzerland",
            "Austria",
            "Spain",
            "Portugal",
            "Italy",
            "Finland",
            "Iceland",
            "Luxembourg",
            "Czechia",
            "Slovenia",
            "Estonia",
        ],
        "Eastern-like": [
            "Japan",
            "South Korea",
            "China",
            "Taiwan",
            "Singapore",
            "Thailand",
            "Vietnam",
            "Malaysia",
            "Indonesia",
            "Philippines",
            "India",
            "Pakistan",
            "Bangladesh",
            "Sri Lanka",
            "Nepal",
            "Kazakhstan",
            "Turkey",
            "Russia",
            "Ukraine",
            "Poland",
            "Hungary",
            "Romania",
            "Bulgaria",
            "Greece",
        ],
        "Southern-like": [
            "Brazil",
            "Mexico",
            "Argentina",
            "Chile",
            "Colombia",
            "Peru",
            "Venezuela",
            "Ecuador",
            "Uruguay",
            "South Africa",
            "Nigeria",
            "Kenya",
            "Egypt",
            "Morocco",
            "Tunisia",
            "Saudi Arabia",
            "Iran",
            "Israel",
            "United Arab Emirates",
            "Qatar",
            "Jordan",
            "Lebanon",
            "Ghana",
            "Ethiopia",
        ],
    }
    rows = []
    for cluster, names in countries.items():
        center = clusters[cluster]
        region_noise = rng.normal(0, 0.08, len(features))
        for name in names:
            values = center + region_noise + rng.normal(0, 0.22, len(features))
            rows.append({"country": name, "region": cluster, **dict(zip(features, values))})
    df = pd.DataFrame(rows)
    z = df[features]
    z = pd.DataFrame(StandardScaler().fit_transform(z), columns=features)
    for feature in features:
        df[feature] = z[feature]
    Z = None
    return {"countries": df, "features": features, "linkage": Z}
