from qgis.core import (
    QgsProject,
    QgsFeature,
    QgsGeometry,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsPoint,
    QgsPointXY,
    QgsWkbTypes,
    QgsMapLayer
)
from qgis.gui import QgsMapCanvas
from PyQt5.QtWidgets import QApplication, QInputDialog
from osgeo import gdal
import tempfile
import os


def run(iface):
    # === Ask user for exaggeration factor ===
    ex_factor, ok = QInputDialog.getDouble(
        iface.mainWindow(),
        "Vertical Exaggeration",
        "Enter exaggeration factor:",
        value=2.0,
        min=0.1,
        decimals=2
    )

    if not ok:
        iface.messageBar().pushWarning("Cancelled", "Operation cancelled by user.")
        return

    # --- Transformation function ---
    def transform_vertex(x, y):
        return x, y * ex_factor

    # --- Access selected group from Layer Tree ---
    selected_node = iface.layerTreeView().currentNode()

    if selected_node is None or selected_node.nodeType() != 0:
        iface.messageBar().pushCritical("Error", "Please select a group in the Layers panel.")
        return

    if selected_node.name() == "Sections":
        iface.messageBar().pushCritical("Error", "Please, select a specific section.")
        return

    group = selected_node
    group_name = group.name()

    # --- Create output group ---
    project = QgsProject.instance()
    layer_tree = project.layerTreeRoot()
    output_group_name = f"{group_name}_x{ex_factor}"
    output_group = layer_tree.insertGroup(0, output_group_name)

    project.blockSignals(True)

    # --- Process each layer in the group ---
    for child in group.findLayers():
        input_layer = child.layer()

        if not input_layer or not input_layer.isValid():
            continue

        # === 1. VECTOR LAYERS ===
        if input_layer.type() == QgsMapLayer.VectorLayer:
            geometry_type = input_layer.geometryType()

            if geometry_type == QgsWkbTypes.PointGeometry:
                geom_type_str = "Point"
            elif geometry_type == QgsWkbTypes.LineGeometry:
                geom_type_str = "LineString"
            elif geometry_type == QgsWkbTypes.PolygonGeometry:
                geom_type_str = "Polygon"
            else:
                print(f"Unsupported geometry type in layer: {input_layer.name()}")
                continue

            output_layer = QgsVectorLayer(
                f"{geom_type_str}?crs={input_layer.crs().authid()}",
                f"{input_layer.name()}_x{ex_factor}",
                "memory"
            )

            output_provider = output_layer.dataProvider()
            output_provider.addAttributes(input_layer.fields())
            output_layer.updateFields()

            for i, feature in enumerate(input_layer.getFeatures()):
                try:
                    geom = feature.geometry()

                    if geometry_type == QgsWkbTypes.PointGeometry:
                        pt = geom.asPoint()
                        new_geom = QgsGeometry.fromPointXY(QgsPointXY(*transform_vertex(pt.x(), pt.y())))

                    elif geometry_type == QgsWkbTypes.LineGeometry:
                        line = geom.asPolyline()
                        new_line = [QgsPointXY(*transform_vertex(pt.x(), pt.y())) for pt in line]
                        new_geom = QgsGeometry.fromPolylineXY(new_line)

                    elif geometry_type == QgsWkbTypes.PolygonGeometry:
                        if geom.isMultipart():
                            continue  # optionally handle multipart

                        polygon = geom.asPolygon()
                        new_exterior = [QgsPointXY(*transform_vertex(pt.x(), pt.y())) for pt in polygon[0]]
                        new_interiors = [
                            [QgsPointXY(*transform_vertex(pt.x(), pt.y())) for pt in ring]
                            for ring in polygon[1:]
                        ]
                        new_geom = QgsGeometry.fromPolygonXY([new_exterior] + new_interiors)

                    new_feature = QgsFeature()
                    new_feature.setGeometry(new_geom)
                    new_feature.setAttributes(feature.attributes())
                    output_provider.addFeature(new_feature)

                except Exception as e:
                    print(f"Error processing feature {i} in {input_layer.name()}: {e}")

                if i % 100 == 0:
                    QApplication.processEvents()

            # Clone symbology and labeling
            try:
                output_layer.setRenderer(input_layer.renderer().clone())
            except Exception as e:
                print(f"Failed to clone renderer: {e}")

            if input_layer.labelsEnabled():
                labeling = input_layer.labeling()
                if labeling:
                    try:
                        output_layer.setLabeling(labeling.clone())
                        output_layer.setLabelsEnabled(True)
                    except Exception as e:
                        print(f"Failed to clone labeling: {e}")

            project.addMapLayer(output_layer, False)
            output_group.addLayer(output_layer)

        # === 2. RASTER LAYERS ===
        elif input_layer.type() == QgsMapLayer.RasterLayer and input_layer.isValid():
            input_path = input_layer.source()
            ds = gdal.Open(input_path, gdal.GA_ReadOnly)
            if ds is None:
                print(f"Could not open raster: {input_layer.name()}")
                continue

            # Read dimensions and geotransform
            gt = ds.GetGeoTransform()
            ph = gt[5]  # pixel height (usually negative)
            height = ds.RasterYSize
            orig_top_y = gt[3]
            orig_bottom_y = orig_top_y + ph * height

            # Apply transformation
            new_ph = ph * ex_factor
            new_bottom_y = orig_bottom_y * ex_factor
            new_top_y = new_bottom_y - (new_ph * height)

            # Build new geotransform
            new_gt = (gt[0], gt[1], gt[2], new_top_y, gt[4], new_ph)

            # Create output raster path
            tmp_dir = tempfile.gettempdir()
            output_path = os.path.join(tmp_dir, f"{input_layer.name()}_x{ex_factor}.tif")

            driver = gdal.GetDriverByName('GTiff')
            out_ds = driver.Create(
                output_path,
                ds.RasterXSize,
                ds.RasterYSize,
                ds.RasterCount,
                ds.GetRasterBand(1).DataType
            )
            out_ds.SetGeoTransform(new_gt)
            out_ds.SetProjection(ds.GetProjection())

            for i in range(1, ds.RasterCount + 1):
                data = ds.GetRasterBand(i).ReadAsArray()
                out_ds.GetRasterBand(i).WriteArray(data)

            out_ds.FlushCache()
            ds = None
            out_ds = None

            # Load into QGIS
            new_raster = QgsRasterLayer(output_path, f"{input_layer.name()}_x{ex_factor}")
            if new_raster.isValid():
                project.addMapLayer(new_raster, False)
                output_group.addLayer(new_raster)
            else:
                print(f"Failed to load transformed raster: {output_path}")

    project.blockSignals(False)

    # --- Zoom to output group ---
    def zoom_to_group(group_name: str, iface):
        group = QgsProject.instance().layerTreeRoot().findGroup(group_name)
        if not group:
            iface.messageBar().pushWarning("Zoom Failed", f"Group '{group_name}' not found.")
            return

        extent = None
        for child in group.findLayers():
            layer = child.layer()
            if layer and layer.isValid():
                try:
                    if extent:
                        extent.combineExtentWith(layer.extent())
                    else:
                        extent = layer.extent()
                except Exception as e:
                    print(f"Error getting extent from {layer.name()}: {e}")

        if extent:
            iface.mapCanvas().setExtent(extent)
            iface.mapCanvas().refresh()
            iface.messageBar().pushMessage("Zoom", f"Zoomed to group '{group_name}'", level=0)
        else:
            iface.messageBar().pushWarning("Zoom Failed", "No valid extents found.")

    zoom_to_group(output_group_name, iface)

    iface.messageBar().pushMessage(
        "Success",
        f"Processed group '{group_name}' with vertical exaggeration ×{ex_factor}. Output group: '{output_group_name}'",
        level=0
    )
    print(f"✅ All layers in '{group_name}' processed with exaggeration ×{ex_factor}.")
