from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from style_config import FONT_SMALL


BANNED_FORMAL_TEXT = (
    "structural reproduction",
    "simulated",
    "graphcast_figure",
    "alphago_zero",
    "recovery_figure",
    "step5_figure",
    "alphafold_figure",
    "anthropogenic_mass",
    "rationality_figure",
    "moral_machine",
)


def validate_figure_object(fig, spec) -> list[str]:
    warnings: list[str] = []
    width, height = fig.get_size_inches()
    expected_width, expected_height = spec.size_in
    if abs(width - expected_width) > 0.03:
        warnings.append(f"{spec.stem}: width {width:.3f} in != {expected_width:.3f} in")
    if abs(height - expected_height) > 0.03:
        warnings.append(f"{spec.stem}: height {height:.3f} in != {expected_height:.3f} in")

    texts = [text for ax in fig.axes for text in ax.texts]
    texts += list(fig.texts)
    found_panels = {text.get_text() for text in texts if text.get_text() in spec.required_panels}
    for panel in spec.required_panels:
        if panel not in found_panels:
            warnings.append(f"{spec.stem}: missing panel label {panel}")

    for text in texts:
        label = text.get_text()
        if text.get_fontsize() < FONT_SMALL - 1e-6:
            warnings.append(f"{spec.stem}: text below {FONT_SMALL} pt: {label!r}")
        lower = label.lower()
        for banned in BANNED_FORMAL_TEXT:
            if banned in lower:
                warnings.append(f"{spec.stem}: banned formal text remains: {label!r}")
                break

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    fig_bbox = fig.bbox
    for text in texts:
        if not text.get_visible() or not text.get_text():
            continue
        bbox = text.get_window_extent(renderer=renderer)
        if bbox.width == 0 or bbox.height == 0:
            continue
        margin = 5
        if (
            bbox.x1 < -margin
            or bbox.y1 < -margin
            or bbox.x0 > fig_bbox.width + margin
            or bbox.y0 > fig_bbox.height + margin
        ):
            warnings.append(f"{spec.stem}: text outside canvas: {text.get_text()!r}")
    return warnings


def validate_exported_png(path: Path, spec, dpi: int = 600) -> list[str]:
    warnings: list[str] = []
    image = Image.open(path)
    if image.mode in {"RGBA", "LA"}:
        alpha = image.getchannel("A")
        if alpha.getextrema()[0] < 255:
            warnings.append(f"{path.name}: unexpected transparent pixels")
    expected_width = round(spec.size_in[0] * dpi)
    if abs(image.size[0] - expected_width) > 8:
        warnings.append(f"{path.name}: width {image.size[0]} px != expected {expected_width} px")
    rgb = image.convert("RGB")
    corners = [
        rgb.getpixel((0, 0)),
        rgb.getpixel((rgb.width - 1, 0)),
        rgb.getpixel((0, rgb.height - 1)),
        rgb.getpixel((rgb.width - 1, rgb.height - 1)),
    ]
    if any(max(abs(channel - 255) for channel in corner) > 3 for corner in corners):
        warnings.append(f"{path.name}: corner background is not white")
    return warnings


def make_half_scale_preview(src: Path, out: Path) -> None:
    image = Image.open(src).convert("RGB")
    image = image.resize((image.width // 2, image.height // 2), Image.Resampling.LANCZOS)
    image.save(out)


def write_validation_report(report_path: Path, warnings: dict[str, list[str]]) -> None:
    report_path.write_text(
        json.dumps({"warnings": warnings, "ok": not any(warnings.values())}, indent=2),
        encoding="utf-8",
    )

