# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LizardDownloader
                                 A QGIS plugin
 Download GGMN data from lizard, interpolate and add new points
                             -------------------
        begin                : 2016-01-08
        copyright            : (C) 2016 by Reinout van Rees, Nelen & Schuurmans
        email                : reinout@vanrees.org
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load LizardDownloader class from file LizardDownloader.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .lizard_downloader import LizardDownloader
    return LizardDownloader(iface)
