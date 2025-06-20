from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsVectorFileWriter,
    QgsRasterLayer,
    QgsLayerTreeGroup, QgsLayerTreeLayer,
    QgsCoordinateTransformContext
)
import os
import shutil
import qgis.utils

def run(iface):
    project = QgsProject.instance()
    iface = qgis.utils.iface
    selected_nodes = iface.layerTreeView().selectedNodes()

    if not selected_nodes or not isinstance(selected_nodes[0], QgsLayerTreeGroup) or selected_nodes[0].name() == "Sections":
        QMessageBox.critical(None, "Error", "Please, select a group.")
        return

    selected_group = selected_nodes[0]

    folder = QFileDialog.getExistingDirectory(None, "Select Folder to Save Layers")
    if not folder:
        return

    def process_node(node):
        if isinstance(node, QgsLayerTreeLayer):
            input_layer = node.layer()
            if not input_layer or not input_layer.isValid():
                return

            provider_name = input_layer.dataProvider().name()

            if provider_name == 'memory' and input_layer.type() == QgsVectorLayer.VectorLayer:
                # Save memory vector layer as GeoPackage
                base_name = input_layer.name().replace(" ", "_")
                gpkg_path = os.path.join(folder, f"{base_name}.gpkg")

                options = QgsVectorFileWriter.SaveVectorOptions()
                options.driverName = 'GPKG'
                options.layerName = base_name
                options.fileEncoding = 'UTF-8'

                error = QgsVectorFileWriter.writeAsVectorFormatV2(
                    input_layer,
                    gpkg_path,
                    project.transformContext(),
                    options
                )

                if error[0] != QgsVectorFileWriter.NoError:
                    print(f"Failed to save vector layer '{input_layer.name()}': {error[1]}")
                    return

                new_layer = QgsVectorLayer(f"{gpkg_path}|layername={base_name}", base_name, "ogr")
                if not new_layer.isValid():
                    print(f"Failed to load saved vector layer for '{base_name}'")
                    return

                try:
                    new_layer.setRenderer(input_layer.renderer().clone())
                except Exception as e:
                    print(f"Failed to clone renderer for vector layer '{input_layer.name()}': {e}")

                # --- Preserve labeling for vector layers ---
                if input_layer.labelsEnabled():
                    labeling = input_layer.labeling()
                    if labeling is not None:
                        labeling_clone = labeling.clone()
                        new_layer.setLabeling(labeling_clone)
                        new_layer.setLabelsEnabled(True)
                    else:
                        new_layer.setLabelsEnabled(False)
                else:
                    new_layer.setLabelsEnabled(False)
                # --------------------------

                project.addMapLayer(new_layer, False)
                parent_group = node.parent()
                parent_group.insertChildNode(parent_group.children().index(node) + 1, QgsLayerTreeLayer(new_layer))

            elif provider_name == 'gdal' and input_layer.type() == QgsRasterLayer.RasterLayer:
                # Save temporary raster layer to GeoTIFF
                base_name = input_layer.name().replace(" ", "_")
                tif_path = os.path.join(folder, f"{base_name}.tif")

                src_path = input_layer.source()
                if os.path.isfile(src_path):
                    try:
                        shutil.copy(src_path, tif_path)
                        new_layer = QgsRasterLayer(tif_path, base_name)
                        if not new_layer.isValid():
                            print(f"Failed to load saved raster layer for '{base_name}'")
                            return

                        project.addMapLayer(new_layer, False)
                        parent_group = node.parent()
                        parent_group.insertChildNode(parent_group.children().index(node) + 1, QgsLayerTreeLayer(new_layer))

                    except Exception as e:
                        print(f"Failed to copy raster file '{src_path}': {e}")
                else:
                    print(f"Raster source is not a file, skipping layer '{input_layer.name()}'")

        elif isinstance(node, QgsLayerTreeGroup):
            for child in node.children():
                process_node(child)

    process_node(selected_group)

    QMessageBox.information(None, "Done", "Temporary layers saved as permanent files.")
