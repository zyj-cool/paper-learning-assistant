from __future__ import annotations

import json
import traceback
from pathlib import Path

import matplotlib.pyplot as plt

from export_utils import OUTPUT_ROOT, export_figure
from figures import (
    fig01_graphcast,
    fig02_alphago_zero,
    fig03_recovery,
    fig04_step5,
    fig05_alphafold,
    fig06_anthropogenic_mass,
    fig07_rationality,
    fig08_moral_machine,
)
from validation import write_validation_report


ROOT = Path(__file__).resolve().parent


FIGURE_JOBS = [
    ("fig01_graphcast_structural", fig01_graphcast.make_figure),
    ("fig02_alphago_zero_structural", fig02_alphago_zero.make_figure),
    ("fig03_recovery_structural", fig03_recovery.make_figure),
    ("fig04_step5_structural", fig04_step5.make_figure),
    ("fig05_alphafold_structural", fig05_alphafold.make_figure),
    ("fig06_anthropogenic_mass_structural", fig06_anthropogenic_mass.make_figure),
    ("fig07_rationality_structural", fig07_rationality.make_figure),
    ("fig08_moral_machine_structural", fig08_moral_machine.make_structural_figure),
    ("fig08_moral_machine_enhanced", fig08_moral_machine.make_enhanced_figure),
]


def main() -> None:
    manifest: dict[str, object] = {"figures": {}, "errors": {}}
    warnings: dict[str, list[str]] = {}
    for stem, factory in FIGURE_JOBS:
        try:
            fig = factory()
            result = export_figure(fig, stem)
            plt.close(fig)
            manifest["figures"][stem] = result
            warnings[stem] = list(result.get("warnings", []))
            print(f"generated {stem}")
        except Exception as exc:  # pragma: no cover - useful for batch runs.
            manifest["errors"][stem] = {
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
            warnings[stem] = [str(exc)]
            print(f"failed {stem}: {exc}")
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUTPUT_ROOT / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    write_validation_report(OUTPUT_ROOT / "validation_report.json", warnings)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()

