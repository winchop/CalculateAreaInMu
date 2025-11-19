# -*- coding: utf-8 -*-
import os
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QVariant, QMetaType
from qgis.core import (
    QgsVectorLayer,
    QgsField,
    QgsMapLayer,
    QgsWkbTypes,
    Qgis
)
from qgis.utils import iface


class CalculateAreaInMuPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_act = None
        # 获取当前插件目录路径
        self.plugin_dir = os.path.dirname(__file__)

    def initGui(self):
        # 构建图标路径
        icon_path = os.path.join(self.plugin_dir, "icon.svg")
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()

        plugin_name = "计算面积（亩）"
        self.plugin_act = QAction(icon, plugin_name + "…", self.iface.mainWindow())
        self.plugin_act.triggered.connect(self.run)

        self.iface.addCustomActionForLayerType(
            self.plugin_act,
            None,
            QgsMapLayer.VectorLayer,
            True
        )

    def unload(self):
        if self.plugin_act:
            self.iface.removeCustomActionForLayerType(self.plugin_act)

    def run(self):
        layer = iface.layerTreeView().currentLayer()
        if not isinstance(layer, QgsVectorLayer):
            iface.messageBar().pushCritical("错误", "所选图层不是矢量图层。")
            return

        if layer.geometryType() != QgsWkbTypes.PolygonGeometry:
            iface.messageBar().pushWarning("警告", "仅支持面图层（Polygon）。")
            return

        field_name = "Mu"

        if field_name not in [f.name() for f in layer.fields()]:
            if not layer.isEditable():
                layer.startEditing()
            field = QgsField(
                field_name,
                QMetaType.Double if Qgis.QGIS_VERSION_INT >= 33800 else QVariant.Double,
                "double",
                20,
                6
            )
            if not layer.addAttribute(field):
                iface.messageBar().pushCritical("错误", f"无法添加字段 '{field_name}'。")
                return
            iface.messageBar().pushInfo("提示", f"已添加字段 '{field_name}'。")

        mu_index = layer.fields().indexOf(field_name)
        if mu_index == -1:
            iface.messageBar().pushCritical("错误", "字段索引异常。")
            return

        layer.undoStack().beginMacro("计算面积（亩）")
        updated_count = 0
        invalid_count = 0

        try:
            for feat in layer.getFeatures():
                geom = feat.geometry()
                if geom and geom.isGeosValid() and not geom.isEmpty():
                    area_sqm = geom.area()
                    mu_value = area_sqm * 0.0015  # 1 平方米 = 0.0015 亩
                    layer.changeAttributeValue(feat.id(), mu_index, mu_value)
                    updated_count += 1
                else:
                    layer.changeAttributeValue(feat.id(), mu_index, None)
                    invalid_count += 1
        except Exception as e:
            layer.undoStack().undo()
            iface.messageBar().pushCritical("错误", f"计算失败: {str(e)}")
            return
        finally:
            layer.undoStack().endMacro()

        msg = f"成功更新 {updated_count} 个要素的 'Mu' 字段（亩）。"
        if invalid_count > 0:
            msg += f"另有 {invalid_count} 个要素因几何无效设为 NULL。"
        iface.messageBar().pushInfo("完成", msg)