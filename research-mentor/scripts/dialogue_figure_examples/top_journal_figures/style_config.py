from __future__ import annotations

from dataclasses import dataclass

import matplotlib.pyplot as plt


GLOBAL_SEED = 20260731

DOUBLE_COLUMN_WIDTH_MM = 180
DOUBLE_COLUMN_WIDTH_IN = 7.0866

FONT_PANEL_LABEL = 8.5
FONT_AXIS_LABEL = 7.5
FONT_TICK = 6.5
FONT_LEGEND = 6.5
FONT_ANNOTATION = 6.5
FONT_SMALL = 5.8
FONT_TITLE_DEBUG = 8

LINE_MAIN = 1.15
LINE_SECONDARY = 0.85
LINE_THIN = 0.6
SPINE_WIDTH = 0.6
ERRORBAR_WIDTH = 0.75
CAP_SIZE = 2.0
MARKER_SIZE = 2.8

BLUE = "#2F6B9A"
ORANGE = "#D97732"
GRAY = "#777777"
LIGHT_GRAY = "#B8B8B8"
DARK_GRAY = "#444444"
GREEN = "#2E7D59"
RED = "#B94A48"
PURPLE = "#76569A"
GOLD = "#B58A35"

CLUSTER_COLORS = {
    "Western-like": BLUE,
    "Eastern-like": ORANGE,
    "Southern-like": GREEN,
}

FONT_FAMILY = ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"]


@dataclass(frozen=True)
class FigureSpec:
    stem: str
    width_mm: float
    height_mm: float
    required_panels: tuple[str, ...] = ()

    @property
    def size_in(self) -> tuple[float, float]:
        return (self.width_mm / 25.4, self.height_mm / 25.4)


FIGURE_SPECS = {
    "fig01_graphcast_structural": FigureSpec(
        "fig01_graphcast_structural", 180, 75, ("a", "b", "c", "d")
    ),
    "fig02_alphago_zero_structural": FigureSpec(
        "fig02_alphago_zero_structural", 180, 62, ("a", "b", "c")
    ),
    "fig03_recovery_structural": FigureSpec(
        "fig03_recovery_structural", 180, 135, ("a", "b", "c", "d")
    ),
    "fig04_step5_structural": FigureSpec(
        "fig04_step5_structural", 180, 78, ("a", "b")
    ),
    "fig05_alphafold_structural": FigureSpec(
        "fig05_alphafold_structural", 125, 105, ("a",)
    ),
    "fig06_anthropogenic_mass_structural": FigureSpec(
        "fig06_anthropogenic_mass_structural", 180, 100, ("a",)
    ),
    "fig07_rationality_structural": FigureSpec(
        "fig07_rationality_structural", 180, 145, tuple("abcdefghijklmnop")
    ),
    "fig08_moral_machine_structural": FigureSpec(
        "fig08_moral_machine_structural", 180, 100, ("a", "b")
    ),
    "fig08_moral_machine_enhanced": FigureSpec(
        "fig08_moral_machine_enhanced", 180, 100, ("a", "b")
    ),
}


def apply_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": FONT_FAMILY,
            "font.size": FONT_TICK,
            "axes.labelsize": FONT_AXIS_LABEL,
            "axes.titlesize": FONT_TITLE_DEBUG,
            "axes.linewidth": SPINE_WIDTH,
            "xtick.labelsize": FONT_TICK,
            "ytick.labelsize": FONT_TICK,
            "legend.fontsize": FONT_LEGEND,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "savefig.transparent": False,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.grid": False,
            "lines.linewidth": LINE_MAIN,
            "patch.linewidth": LINE_THIN,
        }
    )


def format_axis(ax, *, left: bool = True, bottom: bool = True) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(left)
    ax.spines["bottom"].set_visible(bottom)
    for spine in ax.spines.values():
        spine.set_linewidth(SPINE_WIDTH)
    ax.tick_params(direction="out", width=SPINE_WIDTH, length=2.8, pad=1.5)
    ax.xaxis.labelpad = 2.0
    ax.yaxis.labelpad = 2.0


def add_panel_label(ax, label: str, x: float = -0.16, y: float = 1.04) -> None:
    ax.text(
        x,
        y,
        label,
        transform=ax.transAxes,
        fontsize=FONT_PANEL_LABEL,
        fontweight="bold",
        ha="left",
        va="bottom",
        clip_on=False,
    )

