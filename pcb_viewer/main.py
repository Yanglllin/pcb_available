from __future__ import annotations

from pathlib import Path
from typing import List

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from .gerber_utils import load_gerber_directory, parse_drill_file, export_gcode, GerberLayer


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Gerber Viewer")
        self.open_button = QPushButton("Open Gerber Folder")
        self.export_svg_button = QPushButton("Export SVGs")
        self.export_gcode_button = QPushButton("Export Drill G-code")
        self.layer_list = QListWidget()

        layout = QVBoxLayout()
        layout.addWidget(self.open_button)
        layout.addWidget(self.layer_list)
        layout.addWidget(self.export_svg_button)
        layout.addWidget(self.export_gcode_button)
        self.setLayout(layout)

        self.open_button.clicked.connect(self.open_folder)
        self.export_svg_button.clicked.connect(self.export_svgs)
        self.export_gcode_button.clicked.connect(self.export_drills)

        self.layers: List[GerberLayer] = []

    def open_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Gerber Folder")
        if not folder:
            return
        self.layers = load_gerber_directory(Path(folder))
        self.layer_list.clear()
        for layer in self.layers:
            self.layer_list.addItem(f"{layer.file_path.name} [{layer.file_type.name}]")
        QMessageBox.information(self, "Layers Loaded", f"Detected {len(self.layers)} files")

    def export_svgs(self) -> None:
        if not self.layers:
            return
        out_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if not out_dir:
            return
        for layer in self.layers:
            if layer.gerber is None:
                continue
            svg_path = Path(out_dir) / f"{layer.file_path.stem}.svg"
            layer.gerber.render_with_shapely().save_svg(svg_path)
        QMessageBox.information(self, "Done", "SVG export finished")

    def export_drills(self) -> None:
        drill_files = [l.file_path for l in self.layers if l.file_path.suffix.lower() in {".drl", ".txt"}]
        if not drill_files:
            QMessageBox.warning(self, "No Drill Files", "No drill files found")
            return
        drills = []
        for df in drill_files:
            drills.extend(parse_drill_file(df))
        path, _ = QFileDialog.getSaveFileName(self, "Save G-code", "drill.gcode", "GCODE Files (*.gcode)")
        if not path:
            return
        export_gcode(drills, Path(path))
        QMessageBox.information(self, "Done", "G-code exported")


def main() -> None:
    app = QApplication([])
    win = MainWindow()
    win.show()
    app.exec()


if __name__ == "__main__":
    main()
