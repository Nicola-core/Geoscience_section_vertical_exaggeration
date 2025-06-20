# task1.py
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDialogButtonBox,
    QDoubleSpinBox
)
from PyQt5.QtCore import QVariant
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsPointXY,
    QgsFeature,
    QgsField,
    QgsGeometry
)
from qgis.core import (
    QgsMarkerSymbol,
    QgsSingleSymbolRenderer,
    QgsTextFormat,
    QgsTextBufferSettings,
    QgsPalLayerSettings,
    QgsVectorLayerSimpleLabeling
)
from PyQt5.QtGui import QColor, QFont


class PointInputDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generate vertical section scale (1:1)")

        layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.x_input = QDoubleSpinBox()
        self.x_input.setDecimals(6)
        self.x_input.setRange(-1e10, 1e10)
        self.x_input.setValue(0)

        self.y_min_input = QDoubleSpinBox()
        self.y_min_input.setDecimals(6)
        self.y_min_input.setRange(-1e10, 1e10)
        self.y_min_input.setValue(0)

        self.y_max_input = QDoubleSpinBox()
        self.y_max_input.setDecimals(6)
        self.y_max_input.setRange(-1e10, 1e10)
        self.y_max_input.setValue(10)

        self.y_interval_input = QDoubleSpinBox()
        self.y_interval_input.setDecimals(6)
        self.y_interval_input.setRange(0.000001, 1e10)
        self.y_interval_input.setValue(1)

        form_layout.addRow("X Position:", self.x_input)
        form_layout.addRow("Y Min:", self.y_min_input)
        form_layout.addRow("Y Max:", self.y_max_input)
        form_layout.addRow("Y Interval:", self.y_interval_input)

        layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def get_values(self):
        return (
            self.x_input.value(),
            self.y_min_input.value(),
            self.y_max_input.value(),
            self.y_interval_input.value()
        )


def run(iface):
    dialog = PointInputDialog()
    if dialog.exec_() == QDialog.Accepted:
        x_position, y_min, y_max, y_interval = dialog.get_values()

        project_crs = QgsProject.instance().crs().authid()
        layer = QgsVectorLayer(f"Point?crs={project_crs}", "Section scale", "memory")
        provider = layer.dataProvider()

        provider.addAttributes([QgsField("Depth", QVariant.Double)])
        layer.updateFields()

        features = []
        y = y_min
        while y <= y_max:
            point = QgsPointXY(x_position, y)
            feature = QgsFeature()
            feature.setGeometry(QgsGeometry.fromPointXY(point))
            feature.setAttributes([y])  # Set 'Depth' as y-coordinate
            features.append(feature)
            y += y_interval

        provider.addFeatures(features)
        layer.updateExtents()
        QgsProject.instance().addMapLayer(layer)

        # Symbol styling
        symbol = QgsMarkerSymbol.createSimple({
            'name': 'cross',
            'color': '183,72,75',
            'size': '2',
            'size_unit': 'MM',
            'outline_color': '35,35,35',
            'outline_width': '0',
            'outline_style': 'solid'
        })
        renderer = QgsSingleSymbolRenderer(symbol)
        layer.setRenderer(renderer)

        label_settings = QgsPalLayerSettings()
        label_settings.fieldName = 'Depth'

        text_format = QgsTextFormat()
        text_format.setFont(QFont('Arial', 10))
        text_format.setSize(10)
        text_format.setColor(QColor(50, 50, 50))

        buffer_settings = QgsTextBufferSettings()
        buffer_settings.setEnabled(False)
        buffer_settings.setSize(1)
        buffer_settings.setColor(QColor(250, 250, 250))
        text_format.setBuffer(buffer_settings)

        label_settings.setFormat(text_format)

        layer.setLabelsEnabled(True)
        layer.setLabeling(QgsVectorLayerSimpleLabeling(label_settings))
        layer.triggerRepaint()

        iface.messageBar().pushMessage(f"{len(features)} points created.", level=0)  # Info message

    else:
        iface.messageBar().pushMessage("Operation cancelled.", level=1)  # Warning message

