from __future__ import annotations

from pathlib import Path

from style_config import FIGURE_SPECS
from validation import make_half_scale_preview, validate_exported_png, validate_figure_object


ROOT = Path(__file__).resolve().parent
OUTPUT_ROOT = ROOT / "outputs"


def ensure_output_dirs() -> None:
    for name in ["svg", "pdf", "png_600dpi", "preview"]:
        (OUTPUT_ROOT / name).mkdir(parents=True, exist_ok=True)


def export_figure(fig, stem: str) -> dict[str, str | list[str]]:
    ensure_output_dirs()
    spec = FIGURE_SPECS[stem]
    warnings = validate_figure_object(fig, spec)

    svg_path = OUTPUT_ROOT / "svg" / f"{stem}.svg"
    pdf_path = OUTPUT_ROOT / "pdf" / f"{stem}.pdf"
    png_path = OUTPUT_ROOT / "png_600dpi" / f"{stem}_600dpi.png"
    preview_path = OUTPUT_ROOT / "preview" / f"{stem}_preview.png"
    half_preview_path = OUTPUT_ROOT / "preview" / f"{stem}_50pct_preview.png"

    fig.savefig(svg_path)
    fig.savefig(pdf_path)
    fig.savefig(png_path, dpi=600, facecolor="white")
    fig.savefig(preview_path, dpi=160, facecolor="white")
    make_half_scale_preview(png_path, half_preview_path)

    warnings.extend(validate_exported_png(png_path, spec, dpi=600))
    return {
        "svg": str(svg_path),
        "pdf": str(pdf_path),
        "png_600dpi": str(png_path),
        "preview": str(preview_path),
        "preview_50pct": str(half_preview_path),
        "warnings": warnings,
    }
