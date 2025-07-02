from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Iterable

from pygerber.gerber.api import GerberFile, FileTypeEnum
import gerber.excellon as excellon


@dataclass
class GerberLayer:
    file_path: Path
    gerber: GerberFile
    file_type: FileTypeEnum


def load_gerber_directory(path: Path) -> List[GerberLayer]:
    """Load all Gerber files from directory."""
    layers: List[GerberLayer] = []
    for p in sorted(path.iterdir()):
        if not p.is_file():
            continue
        if p.suffix.lower() in {".gbr", ".grb", ".gtl", ".gbl", ".gts", ".gbs", ".gto", ".gbo", ".gtp", ".gbp", ".drl", ".txt"}:
            # Drill files are also collected but not parsed as Gerber
            if p.suffix.lower() in {".drl", ".txt"}:
                # store as None for gerber
                gf = None
                file_type = FileTypeEnum.OTHER
            else:
                gf = GerberFile.from_file(p, file_type=FileTypeEnum.INFER)
                file_type = gf.file_type
            layers.append(GerberLayer(p, gf, file_type))
    return layers


def parse_drill_file(path: Path):
    """Parse Excellon drill file and return list of (x, y, diameter) in mm."""
    ef = excellon.read(str(path))
    ef.to_metric()
    drills = []
    for hit in ef.hits:
        if isinstance(hit, excellon.DrillHit):
            drills.append((hit.position[0], hit.position[1], hit.tool.diameter))
    return drills


def export_gcode(drills: Iterable[tuple[float, float, float]], out_path: Path, depth: float = -1.0) -> None:
    """Export drill hits to a very simple G-code program."""
    with out_path.open("w", encoding="utf-8") as f:
        f.write("G90\n")  # absolute
        f.write("G21\n")  # mm units
        f.write("G0 Z5\n")
        f.write("M3\n")
        for x, y, _diam in drills:
            f.write(f"G0 X{x:.4f} Y{y:.4f}\n")
            f.write(f"G1 Z{depth} F200\n")
            f.write("G0 Z5\n")
        f.write("M5\nM30\n")
