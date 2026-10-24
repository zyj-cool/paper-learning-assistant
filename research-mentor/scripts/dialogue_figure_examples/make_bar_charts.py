from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager


OUT_DIR = Path("outputs") / "bar_charts_reference_style"
OUT_DIR.mkdir(parents=True, exist_ok=True)

groups = ["PBS", "Gel-0", "Gel-1", "Gel-2", "Gel-3", "Pos"]

data = {
    "main_connection_points": {
        "ylabel": "Main connection points",
        "filename": "main_connection_points_bar",
        "values": {
            "PBS": [1, 0, 0],
            "Gel-0": [12, 14, 11],
            "Gel-1": [15, 18, 13],
            "Gel-2": [18, 22, 23],
            "Gel-3": [23, 21, 27],
            "Pos": [27, 24, 30],
        },
        "ylim": (0, 40),
        "yticks": np.arange(0, 41, 10),
    },
    "main_mesh_count": {
        "ylabel": "Main mesh count",
        "filename": "main_mesh_count_bar",
        "values": {
            "PBS": [1, 0, 0],
            "Gel-0": [24, 21, 27],
            "Gel-1": [37, 39, 33],
            "Gel-2": [41, 38, 44],
            "Gel-3": [54, 52, 47],
            "Pos": [54, 57, 49],
        },
        "ylim": (0, 80),
        "yticks": np.arange(0, 81, 20),
    },
}

# Palette follows the reference image and adds a close warm tone for Pos.
colors = {
    "PBS": "#2F7F91",
    "Gel-0": "#A7CB7F",
    "Gel-1": "#B398BC",
    "Gel-2": "#F0951A",
    "Gel-3": "#CF4D22",
    "Pos": "#A93A3C",
}


def mean_and_sd(values):
    arr = np.asarray(values, dtype=float)
    return arr.mean(), arr.std(ddof=1)


def plot_bar_chart(config):
    means = []
    sds = []
    for group in groups:
        mean, sd = mean_and_sd(config["values"][group])
        means.append(mean)
        sds.append(sd)

    x = np.arange(len(groups))
    fig, ax = plt.subplots(figsize=(7.6, 4.8), dpi=300)

    bars = ax.bar(
        x,
        means,
        width=0.68,
        color=[colors[group] for group in groups],
        edgecolor="none",
    )

    for xpos, mean, sd, group in zip(x, means, sds, groups):
        ax.errorbar(
            xpos,
            mean,
            yerr=sd,
            fmt="none",
            ecolor=colors[group],
            elinewidth=1.4,
            capsize=9,
            capthick=1.4,
            zorder=3,
        )

    ax.set_ylabel(config["ylabel"], fontsize=17, labelpad=14)
    ax.set_ylim(*config["ylim"])
    ax.set_yticks(config["yticks"])
    ax.set_xticks([])
    ax.tick_params(axis="y", labelsize=15, width=2.6, length=8, direction="out")
    ax.tick_params(axis="x", width=2.6, length=0)

    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_linewidth(2.6)

    ax.set_xlim(-0.65, len(groups) - 0.35)
    ax.legend(
        bars,
        groups,
        loc="center left",
        bbox_to_anchor=(1.05, 0.54),
        frameon=False,
        fontsize=16,
        handlelength=1.5,
        handleheight=1.0,
        labelspacing=0.9,
    )

    fig.subplots_adjust(left=0.16, right=0.73, bottom=0.18, top=0.94)

    png_path = OUT_DIR / f"{config['filename']}.png"
    svg_path = OUT_DIR / f"{config['filename']}.svg"
    fig.savefig(png_path, transparent=False)
    fig.savefig(svg_path, transparent=False)
    plt.close(fig)
    return png_path, svg_path, means, sds


def main():
    summary_rows = ["metric,group,rep1,rep2,rep3,mean,sd"]
    for metric, config in data.items():
        png_path, svg_path, means, sds = plot_bar_chart(config)
        print(f"{metric}:")
        print(f"  PNG: {png_path}")
        print(f"  SVG: {svg_path}")
        for group, mean, sd in zip(groups, means, sds):
            reps = config["values"][group]
            summary_rows.append(
                f"{metric},{group},{reps[0]},{reps[1]},{reps[2]},{mean:.2f},{sd:.2f}"
            )
            print(f"  {group}: mean={mean:.2f}, sd={sd:.2f}")

    summary_path = OUT_DIR / "summary_means_sd.csv"
    summary_path.write_text("\n".join(summary_rows), encoding="utf-8")
    print(f"Summary: {summary_path}")


if __name__ == "__main__":
    for font_path in (
        Path(r"C:\Windows\Fonts\calibri.ttf"),
        Path(r"C:\Windows\Fonts\arial.ttf"),
    ):
        if font_path.exists():
            font_manager.fontManager.addfont(font_path)
            plt.rcParams["font.family"] = font_manager.FontProperties(
                fname=font_path
            ).get_name()
            break
    plt.rcParams["svg.fonttype"] = "none"
    plt.rcParams["axes.unicode_minus"] = False
    main()
