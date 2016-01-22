# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LizardDownloader
                                 A QGIS plugin
 Download GGMN data from lizard and add new points
                              -------------------
        begin                : 2016-01-08
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Reinout van Rees, Nelen & Schuurmans
        email                : reinout@vanrees.org
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon, QMessageBox
from import_timeseries import QGisLizardImporter
from lizard_api import Organisations
from lizard_downloader_dialog import LizardDownloaderDialog
from login_dialog import LoginDialog
from qgis.core import QgsMessageLog

import os.path
import resources

resources  # Pyflakes


def pop_up_info(msg='', title='Information', parent=None):
    """Display an info message via Qt box"""
    QMessageBox.information(parent, title, '%s' % msg)


def log(msg, level='INFO'):
    """Shortcut for QgsMessageLog.logMessage function."""
    if level not in ['DEBUG', 'INFO', 'CRITICAL', 'WARNING']:
        level = 'INFO'
    loglevel = getattr(QgsMessageLog, level)
    QgsMessageLog.logMessage(msg, level=loglevel)


class LizardDownloader:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'LizardDownloader_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.login_dialog = LoginDialog()
        self.import_dialog = LizardDownloaderDialog()
        self.upload_dialog = LizardDownloaderDialog()  # TODO

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&GGMN lizard integration')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'LizardDownloader')
        self.toolbar.setObjectName(u'LizardDownloader')
        # Stored username/password, will be set by the login dialog.
        self.username = None
        self.password = None
        self.organisations = {}  # Will be filled after logging in.

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('LizardDownloader', message)

    def add_action(self,
                   icon_path,
                   text,
                   callback,
                   enabled_flag=True,
                   add_to_menu=True,
                   add_to_toolbar=True,
                   status_tip=None,
                   whats_this=None,
                   parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/LizardDownloader/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Log into Lizard'),
            callback=self.run_login,
            add_to_toolbar=False,
            parent=self.iface.mainWindow())
        self.add_action(
            icon_path,
            text=self.tr(u'Download from Lizard'),
            callback=self.run_import,
            add_to_toolbar=False,
            parent=self.iface.mainWindow())
        self.add_action(
            icon_path,
            text=self.tr(u'Add custom point'),
            callback=self.run_add_point,
            add_to_toolbar=True,
            enabled_flag=False,
            parent=self.iface.mainWindow())
        self.add_action(
            icon_path,
            text=self.tr(u'Upload custom points to Lizard'),
            callback=self.run_upload,
            add_to_toolbar=False,
            enabled_flag=False,
            parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&GGMN lizard integration'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def determine_organisations(self):
        if not (self.username and self.password):
            raise RuntimeError("Not logged in")

        organisations_api = Organisations()
        organisations_api.username = self.username
        organisations_api.password = self.password
        return organisations_api.as_dict()

    def run_login(self):
        """Show login dialog if the user isn't logged in yet."""
        # show the dialog
        self.login_dialog.show()
        ok_pressed = self.login_dialog.exec_()
        if ok_pressed:
            self.username = self.login_dialog.username.text()
            self.password = self.login_dialog.password.text()

        self.organisations = self.determine_organisations()
        return ok_pressed

    def run_import(self):
        """Run method that performs all the real work"""
        if not (self.username and self.password):
            ok_pressed = self.run_login()
            if not ok_pressed:
                # Then we don't want to do anything either!
                return

        # show the dialog
        self.import_dialog.show()

        # Run the dialog event loop
        result = self.import_dialog.exec_()
        # See if OK was pressed
        if result:
            organisation_id = self.import_dialog.organisation_id.text()

            # start_js_date = "-2208988800000"
            # end_js_date = "1452470400000"
            start = '1900-01-01T00:00:00Z'
            end = '2017-01-01T00:00:00Z'
            gw_info = QGisLizardImporter(username=username,
                                         password=password,
                                         organisation_id=organisation_id)

            self.iface.messageBar().pushMessage(
                "Lizard",
                "Downloading data (can take up to a minute)...")
            gw_info.download(
                south_west=[-65.80277639340238, -223.9453125],
                north_east=[81.46626086056541, 187.3828125],
                # ^^^ hardcoded
                start=start,
                end=end,
                groundwater_type='GWmMSL')
            if gw_info.data:
                self.iface.messageBar().pushMessage(
                    "Lizard",
                    "Creating and opening a shapefile...")
                gw_info.data_to_shape(directory=os.path.expanduser('~'),
                                      filename='ggmn_test.shp',
                                      overwrite=True)
                gw_info.load_shape()
            else:
                def _split_url(url):
                    return '\n&'.join(url.split('&'))
                msg = """
                No data found for period and extent.
                Technical debug info follows:

                Username: {username}

                Start date: {start}
                End date:   {end}

                Locations url: {locations_url}

                len(locations): {locations_len}

                Timeseries url: {timeseries_url}

                len(timeseries): {timeseries_len}
                """.format(username=username,
                           # y_min=y_min,
                           # y_max=y_max,
                           # x_min=x_min,
                           # x_max=x_max,
                           start=start,
                           end=end,
                           locations_url=_split_url(gw_info.groundwater.locs.url),
                           timeseries_url=_split_url(gw_info.groundwater.ts.url),
                           locations_len=len(gw_info.groundwater.locs.results),
                           timeseries_len=len(gw_info.groundwater.ts.results))
                pop_up_info(msg=msg, title='No data found')

    def run_add_point(self):
        """Run method that performs all the real work"""
        pop_up_info("To be implemented")

    def run_upload(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.upload_dialog.show()
        # Run the dialog event loop
        result = self.upload_dialog.exec_()
        # See if OK was pressed
        if result:
            pop_up_info("To be implemented")
