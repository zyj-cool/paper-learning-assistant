from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.patches import Patch


OUT_DIR = Path("outputs") / "hemolysis_rate_reference_style"
OUT_DIR.mkdir(parents=True, exist_ok=True)

groups = ["PBS", "Gel-0", "Gel-1", "Gel-2", "Gel-3"]
means = np.array([100.0, 0.29, 0.316, 0.365, 0.28])
errors = np.array([5.64, 0.032, 0.035, 0.048, 0.029])

colors = {
    "PBS": "#2F7F91",
    "Gel-0": "#A7CB7F",
    "Gel-1": "#B398BC",
    "Gel-2": "#F0951A",
    "Gel-3": "#CF4D22",
}


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


def add_significance_bracket(ax, x_left, x_vertical, x_bottom_left, x_bottom_right):
    y_top = 113
    y_left_drop = 108
    y_bottom = 5.5

    ax.plot(
        [x_left, x_left, x_vertical],
        [y_left_drop, y_top, y_top],
        color="black",
        linewidth=1.8,
        solid_capstyle="butt",
        clip_on=False,
        zorder=4,
    )
    ax.plot(
        [x_vertical, x_vertical],
        [y_top, y_bottom],
        color="black",
        linewidth=1.8,
        solid_capstyle="butt",
        clip_on=False,
        zorder=4,
    )
    ax.plot(
        [x_bottom_left, x_bottom_right],
        [y_bottom, y_bottom],
        color="black",
        linewidth=1.8,
        solid_capstyle="butt",
        clip_on=False,
        zorder=4,
    )
    ax.text(
        (x_left + x_vertical) / 2,
        y_top + 1.8,
        "***",
        ha="center",
        va="bottom",
        fontsize=17,
        fontweight="bold",
        color="black",
    )


def make_chart():
    x = np.arange(len(groups))
    bar_width = 0.58
    fig, ax = plt.subplots(figsize=(5.35, 3.7), dpi=300)

    ax.bar(
        x,
        means,
        width=bar_width,
        color=[colors[group] for group in groups],
        edgecolor="none",
        zorder=2,
    )

    for xpos, mean, error, group in zip(x, means, errors, groups):
        ax.errorbar(
            xpos,
            mean,
            yerr=error,
            fmt="none",
            ecolor=colors[group],
            elinewidth=1.0,
            capsize=6.0,
            capthick=1.0,
            zorder=3,
        )

    add_significance_bracket(
        ax,
        x_left=0.0,
        x_vertical=2.55,
        x_bottom_left=1.05,
        x_bottom_right=4.1,
    )

    ax.set_ylabel("Hemolysis rate (%)", fontsize=15, labelpad=11)
    ax.set_ylim(0, 120)
    ax.set_yticks(np.arange(0, 121, 30))
    ax.set_xticks([])
    ax.tick_params(axis="y", labelsize=12, width=1.6, length=6, direction="out")
    ax.tick_params(axis="x", width=1.6, length=0)

    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_linewidth(1.6)

    ax.set_xlim(-0.75, 4.75)

    handles = [Patch(facecolor=colors[group], edgecolor="none") for group in groups]
    ax.legend(
        handles,
        groups,
        loc="center left",
        bbox_to_anchor=(1.02, 0.62),
        frameon=False,
        fontsize=14,
        handlelength=1.2,
        handleheight=1.0,
        labelspacing=0.85,
        borderaxespad=0,
    )

    fig.subplots_adjust(left=0.15, right=0.67, bottom=0.16, top=0.95)

    png_path = OUT_DIR / "hemolysis_rate_bar.png"
    svg_path = OUT_DIR / "hemolysis_rate_bar.svg"
    csv_path = OUT_DIR / "hemolysis_rate_summary.csv"

    fig.savefig(png_path, transparent=False)
    fig.savefig(svg_path, transparent=False)
    plt.close(fig)

    rows = ["group,mean,error"]
    rows.extend(
        f"{group},{mean:.3f},{error:.3f}"
        for group, mean, error in zip(groups, means, errors)
    )
    csv_path.write_text("\n".join(rows), encoding="utf-8")

    print(f"PNG: {png_path}")
    print(f"SVG: {svg_path}")
    print(f"CSV: {csv_path}")
    for group, mean, error in zip(groups, means, errors):
        print(f"{group}: mean={mean:.3f}, error={error:.3f}")


if __name__ == "__main__":
    use_calibri()
    make_chart()
