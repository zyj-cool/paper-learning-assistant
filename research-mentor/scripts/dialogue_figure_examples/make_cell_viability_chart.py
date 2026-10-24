from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager


OUT_DIR = Path("outputs") / "cell_viability_reference_style"
OUT_DIR.mkdir(parents=True, exist_ok=True)

groups = ["PBS", "Gel-0", "Gel-1", "Gel-2", "Gel-3"]
means = np.array([100.0, 97.4, 95.1, 96.7, 98.4])
sems = np.array([1.62, 1.90, 1.75, 1.68, 1.82])

colors = ["#218293", "#98C96E", "#B789BD", "#F0841C", "#D83C2A"]


def use_calibri():
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


def make_chart():
    x = np.arange(len(groups))
    fig, ax = plt.subplots(figsize=(4.45, 3.9), dpi=300)

    bars = ax.bar(
        x,
        means,
        width=0.66,
        color=colors,
        edgecolor="none",
        zorder=2,
    )

    for xpos, mean, sem, color in zip(x, means, sems, colors):
        ax.errorbar(
            xpos,
            mean,
            yerr=sem,
            fmt="none",
            ecolor=color,
            elinewidth=0.9,
            capsize=5.0,
            capthick=0.9,
            zorder=3,
        )

    ax.set_ylabel("RAW264.7 Cell viability(%)", fontsize=14, labelpad=10)
    ax.set_ylim(0, 125)
    ax.set_yticks(np.arange(0, 126, 25))
    ax.set_xticks([])
    ax.tick_params(axis="y", labelsize=10, width=1.25, length=5, direction="out")
    ax.tick_params(axis="x", width=1.25, length=0)

    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_linewidth(1.25)

    ax.set_xlim(-0.7, len(groups) - 0.3)
    fig.subplots_adjust(left=0.18, right=0.98, bottom=0.12, top=0.98)

    png_path = OUT_DIR / "raw264_7_cell_viability_bar.png"
    svg_path = OUT_DIR / "raw264_7_cell_viability_bar.svg"
    csv_path = OUT_DIR / "raw264_7_cell_viability_summary.csv"

    fig.savefig(png_path, transparent=False)
    fig.savefig(svg_path, transparent=False)
    plt.close(fig)

    rows = ["group,mean,sem"]
    rows.extend(
        f"{group},{mean:.2f},{sem:.2f}"
        for group, mean, sem in zip(groups, means, sems)
    )
    csv_path.write_text("\n".join(rows), encoding="utf-8")

    print(f"PNG: {png_path}")
    print(f"SVG: {svg_path}")
    print(f"CSV: {csv_path}")
    for group, mean, sem in zip(groups, means, sems):
        print(f"{group}: mean={mean:.2f}, SEM={sem:.2f}")


if __name__ == "__main__":
    use_calibri()
    make_chart()
