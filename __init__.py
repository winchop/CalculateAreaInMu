# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CalculateAreaInMu
                                 A QGIS plugin
 Calculate polygon area in Chinese "Mu" (1 Mu = 666.67 m²)
 ***************************************************************************/
"""

from .calculate_area_in_mu import CalculateAreaInMuPlugin


def classFactory(iface):
    return CalculateAreaInMuPlugin(iface)