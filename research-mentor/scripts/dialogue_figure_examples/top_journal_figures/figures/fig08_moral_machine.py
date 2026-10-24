from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage

from data_generators import generate_moral_machine_data, rng_for
from export_utils import export_figure
from style_config import (
    BLUE,
    CLUSTER_COLORS,
    DARK_GRAY,
    FIGURE_SPECS,
    FONT_SMALL,
    GRAY,
    LINE_MAIN,
    LINE_SECONDARY,
    add_panel_label,
    apply_style,
    format_axis,
)


STRUCTURAL_STEM = "fig08_moral_machine_structural"
ENHANCED_STEM = "fig08_moral_machine_enhanced"


def _clustered_data():
    generated = generate_moral_machine_data()
    df = generated["countries"].copy()
    features = generated["features"]
    z = df[features].to_numpy()
    Z = linkage(z, method="ward", metric="euclidean")
    raw_cluster = fcluster(Z, t=3, criterion="maxclust")
    mapping = {}
    for cluster_id in sorted(set(raw_cluster)):
        subset = df.loc[raw_cluster == cluster_id, features].mean()
        if subset["pedestrians"] > 0.30 and subset["humans"] > 0.15:
            mapping[cluster_id] = "Western-like"
        elif subset["female"] > 0.30:
            mapping[cluster_id] = "Southern-like"
        else:
            mapping[cluster_id] = "Eastern-like"
    df["cluster"] = [mapping[item] for item in raw_cluster]
    return df, features, Z


def _draw_dendrogram(ax, df: pd.DataFrame, features: list[str], Z) -> dict[str, object]:
    representative = {
        "United States",
        "Germany",
        "Japan",
        "China",
        "India",
        "Brazil",
        "Mexico",
        "South Africa",
        "Egypt",
        "Australia",
        "Turkey",
    }
    labels = [country if country in representative else "" for country in df["country"]]
    dendro = dendrogram(
        Z,
        labels=labels,
        leaf_rotation=90,
        leaf_font_size=FONT_SMALL,
        color_threshold=Z[-3, 2],
        above_threshold_color=GRAY,
        ax=ax,
    )
    ax.set_ylabel("Ward linkage distance")
    ax.set_xlabel("")
    format_axis(ax, bottom=False)
    ax.tick_params(axis="x", length=0, pad=1)
    for label in ax.get_xticklabels():
        if label.get_text():
            label.set_fontweight("bold")
    leaves = dendro["leaves"]
    for pos, leaf in enumerate(leaves):
        cluster = df.iloc[leaf]["cluster"]
        x = 5 + 10 * pos
        ax.plot([x, x], [-0.045, -0.015], transform=ax.get_xaxis_transform(), color=CLUSTER_COLORS[cluster], lw=2.0, clip_on=False)
    return dendro


def _draw_radar(ax, df: pd.DataFrame, features: list[str]) -> None:
    means = df.groupby("cluster")[features].mean().loc[list(CLUSTER_COLORS)]
    angles = np.linspace(0, 2 * np.pi, len(features), endpoint=False)
    closed_angles = np.r_[angles, angles[0]]
    for cluster, row in means.iterrows():
        values = np.r_[row.to_numpy(), row.to_numpy()[0]]
        ax.plot(closed_angles, values, color=CLUSTER_COLORS[cluster], lw=LINE_MAIN, label=cluster)
        ax.fill(closed_angles, values, color=CLUSTER_COLORS[cluster], alpha=0.10)
    ax.set_xticks(angles)
    ax.set_xticklabels(features, fontsize=FONT_SMALL)
    ax.tick_params(axis="x", pad=5)
    ax.set_yticks([-1.0, 0.0, 1.0])
    ax.set_yticklabels(["-1", "0", "1"], fontsize=FONT_SMALL)
    ax.set_ylim(-1.25, 1.25)
    ax.grid(color="#000000", alpha=0.13, lw=0.45)


def make_structural_figure():
    apply_style()
    df, features, Z = _clustered_data()
    spec = FIGURE_SPECS[STRUCTURAL_STEM]
    fig = plt.figure(figsize=spec.size_in)
    gs = fig.add_gridspec(
        1,
        2,
        width_ratios=[1.45, 1.0],
        left=0.07,
        right=0.94,
        top=0.90,
        bottom=0.16,
        wspace=0.32,
    )
    ax_tree = fig.add_subplot(gs[0, 0])
    ax_radar = fig.add_subplot(gs[0, 1], projection="polar")
    _draw_dendrogram(ax_tree, df, features, Z)
    _draw_radar(ax_radar, df, features)
    handles, labels = ax_radar.get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        frameon=False,
        loc="upper right",
        bbox_to_anchor=(0.985, 0.985),
        ncol=3,
        handlelength=1.2,
        columnspacing=1.0,
    )
    add_panel_label(ax_tree, "a", x=-0.11, y=1.02)
    add_panel_label(ax_radar, "b", x=-0.12, y=1.06)
    return fig


def _bootstrap_cluster_ci(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    rng = rng_for("moral_machine_bootstrap")
    rows = []
    for cluster, group in df.groupby("cluster"):
        values = group[features].to_numpy()
        n = len(values)
        idx = rng.integers(0, n, size=(1200, n))
        boot = values[idx].mean(axis=1)
        for j, feature in enumerate(features):
            rows.append(
                {
                    "cluster": cluster,
                    "feature": feature,
                    "mean": values[:, j].mean(),
                    "low": np.percentile(boot[:, j], 2.5),
                    "high": np.percentile(boot[:, j], 97.5),
                }
            )
    return pd.DataFrame(rows)


def make_enhanced_figure():
    apply_style()
    df, features, Z = _clustered_data()
    spec = FIGURE_SPECS[ENHANCED_STEM]
    fig = plt.figure(figsize=spec.size_in)
    gs = fig.add_gridspec(
        1,
        2,
        width_ratios=[1.45, 1.0],
        left=0.07,
        right=0.985,
        top=0.90,
        bottom=0.15,
        wspace=0.34,
    )
    ax_tree = fig.add_subplot(gs[0, 0])
    ax_dot = fig.add_subplot(gs[0, 1])
    _draw_dendrogram(ax_tree, df, features, Z)
    ci = _bootstrap_cluster_ci(df, features)
    ybase = np.arange(len(features))
    offsets = {"Western-like": -0.22, "Eastern-like": 0.0, "Southern-like": 0.22}
    for cluster in CLUSTER_COLORS:
        sub = ci.query("cluster == @cluster").set_index("feature").loc[features]
        y = ybase + offsets[cluster]
        x = sub["mean"].to_numpy()
        xerr = np.vstack([x - sub["low"].to_numpy(), sub["high"].to_numpy() - x])
        ax_dot.errorbar(
            x,
            y,
            xerr=xerr,
            fmt="o",
            color=CLUSTER_COLORS[cluster],
            ms=3.0,
            lw=LINE_SECONDARY,
            elinewidth=0.75,
            capsize=1.8,
            label=cluster,
        )
    ax_dot.axvline(0, color=DARK_GRAY, lw=0.55)
    ax_dot.set_yticks(ybase)
    ax_dot.set_yticklabels(features)
    ax_dot.invert_yaxis()
    ax_dot.set_xlabel("Standardized effect")
    ax_dot.set_xlim(-1.55, 1.55)
    ax_dot.grid(axis="x", color="#000000", alpha=0.10, lw=0.45)
    ax_dot.legend(frameon=False, loc="upper right", bbox_to_anchor=(1.02, 1.02), handlelength=1.4)
    format_axis(ax_dot)
    add_panel_label(ax_tree, "a", x=-0.11, y=1.02)
    add_panel_label(ax_dot, "b", x=-0.17, y=1.02)
    return fig


def main():
    print(export_figure(make_structural_figure(), STRUCTURAL_STEM))
    print(export_figure(make_enhanced_figure(), ENHANCED_STEM))


if __name__ == "__main__":
    main()
