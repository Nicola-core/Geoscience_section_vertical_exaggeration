from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject
import os
import tempfile

def run(iface):
    project = QgsProject.instance()

    selected_nodes = iface.layerTreeView().selectedNodes()
    if not selected_nodes or not isinstance(selected_nodes[0], QgsLayerTreeGroup):
        print("please, select a group")
        return

    selected_group = selected_nodes[0]

    reply = QMessageBox.question(
        None,
        "Confirm Deletion",
        f"Are you sure you want to remove all temporary and memory layers from group '{selected_group.name()}'?",
        QMessageBox.Yes | QMessageBox.No
    )

    if reply != QMessageBox.Yes:
        return

    def process_node(node):
        if isinstance(node, QgsLayerTreeLayer):
            layer = node.layer()
            if layer and layer.isValid():
                provider_name = layer.dataProvider().name().lower()
                datasource = layer.dataProvider().dataSourceUri().lower()
                temp_dirs = [tempfile.gettempdir().lower()]

                if provider_name == 'memory' or layer.isTemporary():
                    QgsProject.instance().removeMapLayer(layer.id())
                elif provider_name == 'gdal':
                    if any(datasource.startswith(tmp) for tmp in temp_dirs):
                        QgsProject.instance().removeMapLayer(layer.id())

        elif isinstance(node, QgsLayerTreeGroup):
            for child in list(node.children()):
                process_node(child)

    process_node(selected_group)

