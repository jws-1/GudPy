import os
from PySide6.QtWidgets import QFileDialog

from core import config
from core.enums import (
    CrossSectionSource, FTModes, UnitsOfDensity, Geometry
)
from core.utils import nthfloat


class ContainerSlots():

    def __init__(self, widget, parent):
        self.widget = widget
        self.parent = parent
        self.setupContainerSlots()

    def setContainer(self, container):
        self.container = container
        # Acquire the lock
        self.widgetsRefreshing = True
        # Populate the period number.
        self.widget.containerPeriodNoSpinBox.setValue(
            self.container.periodNumber
        )

        # Populate the data files list.
        self.widget.containerDataFilesList.makeModel(
            self.container.dataFiles.dataFiles
        )

        self.widget.containerDataFilesList.model().dataChanged.connect(
            self.handleDataFilesAltered
        )
        self.widget.containerDataFilesList.model().rowsRemoved.connect(
            self.handleDataFilesAltered
        )

        # Populate geometry data.
        self.widget.containerGeometryComboBox.setCurrentIndex(
            self.container.geometry.value
        )

        # Ensure the correct attributes are being
        # shown for the correct geometry.
        self.widget.containerGeometryInfoStack.setCurrentIndex(
            config.geometry.value
        )

        # Populate geometry specific attributes.
        # Flatplate
        self.widget.containerUpstreamSpinBox.setValue(
            self.container.upstreamThickness
        )
        self.widget.containerDownStreamSpinBox.setValue(
            self.container.downstreamThickness
        )

        total = (
            self.container.upstreamThickness +
            self.container.downstreamThickness
        )
        self.widget.totalContainerThicknessLabel.setText(
            f"Total: {total} cm"
        )

        self.widget.containerAngleOfRotationSpinBox.setValue(
            self.container.angleOfRotation
        )
        self.widget.containerSampleWidthSpinBox.setValue(
            self.container.sampleWidth
        )

        # Cylindrical
        self.widget.containerInnerRadiiSpinBox.setValue(
            self.container.innerRadius
        )
        self.widget.containerOuterRadiiSpinBox.setValue(
            self.container.outerRadius
        )

        self.widget.containerSampleHeightSpinBox.setValue(
            self.container.sampleHeight
        )

        # Populate density data.
        self.widget.containerDensitySpinBox.setValue(self.container.density)
        self.widget.containerDensityUnitsComboBox.setCurrentIndex(
            self.container.densityUnits.value
        )

        # Populate other container configuration data.
        self.widget.containerTotalCrossSectionComboBox.setCurrentIndex(
            self.container.totalCrossSectionSource.value
        )
        self.widget.containerCrossSectionFileLineEdit.setText(
            self.container.crossSectionFilename
        )
        self.widget.containerCrossSectionFileWidget.setVisible(
            self.container.totalCrossSectionSource == CrossSectionSource.FILE
        )
        # Set the tweak factor and packing fraction
        # (reciprocal of tweak factor).
        self.widget.containerTweakFactorSpinBox.setValue(
            self.container.tweakFactor
        )
        if self.container.tweakFactor > 0.0:
            self.widget.containerPackingFractionSpinBox.setValue(
                1.0 / self.container.tweakFactor
            )
        else:
            self.widget.containerPackingFractionSpinBox.setValue(0.0)

        self.packingFractionChanging = False

        self.widget.containerScatteringFractionSpinBox.setValue(
            self.container.scatteringFraction
        )

        self.widget.containerAttenuationCoefficientSpinBox.setValue(
            self.container.attenuationCoefficient
        )

        self.widget.runAsSampleGroupBox.setChecked(
            self.container.runAsSample
        )

        # Populate composition table.
        self.updateCompositionTable()

        # Calculate the expected DCS level.
        self.updateExpectedDCSLevel()

        self.connectToModelSignals()
        self.widget.containerCompositionTable.modelChanged.connect(
            self.connectToModelSignals
        )

        # Populate Fourier Transform parameters.

        self.widget.containerTopHatWidthSpinBox.setValue(
            self.container.topHatW
        )
        self.widget.containerFTModeComboBox.setCurrentIndex(
            self.container.FTMode.value
        )

        self.widget.containerMinSpinBox.setValue(self.container.minRadFT)
        self.widget.containerMaxSpinBox.setValue(self.container.maxRadFT)

        self.widget.containerBroadeningFunctionSpinBox.setValue(
            self.container.grBroadening
        )
        self.widget.containerBroadeningPowerSpinBox.setValue(
            self.container.powerForBroadening
        )
        self.widget.containerStepSizeSpinBox.setValue(self.container.stepSize)

        # Release the lock
        self.widgetsRefreshing = False

    def setupContainerSlots(self):
        # Setup slot for period number.
        self.widget.containerPeriodNoSpinBox.valueChanged.connect(
            self.handlePeriodNoChanged
        )

        # Setup slots for data files.
        self.widget.addContainerDataFileButton.clicked.connect(
            lambda: self.addFiles(
                self.widget.containerDataFilesList,
                "Add data files",
                f"{self.parent.gudrunFile.instrument.dataFileType}"
                f" (*.{self.parent.gudrunFile.instrument.dataFileType})",
            )
        )
        self.widget.removeContainerDataFileButton.clicked.connect(
            lambda: self.removeFile(
                self.widget.containerDataFilesList
            )
        )

        self.widget.duplicateContainerDataFileButton.clicked.connect(
            self.widget.containerDataFilesList.duplicate
        )

        # Populate geometry combo box.
        for g in Geometry:
            self.widget.containerGeometryComboBox.addItem(g.name, g)

        # Setup slots for geometry data.
        self.widget.containerGeometryComboBox.currentIndexChanged.connect(
            self.handleGeometryChanged
        )
        self.widget.containerGeometryComboBox.setDisabled(True)

        # Flatplate
        self.widget.containerUpstreamSpinBox.valueChanged.connect(
            self.handleUpstreamThicknessChanged
        )
        self.widget.containerDownStreamSpinBox.valueChanged.connect(
            self.handleDownstreamThicknessChanged
        )

        self.widget.containerAngleOfRotationSpinBox.valueChanged.connect(
            self.handleAngleOfRotationChanged
        )
        self.widget.containerSampleWidthSpinBox.valueChanged.connect(
            self.handleSampleWidthChanged
        )

        # Cylindrical
        self.widget.containerInnerRadiiSpinBox.valueChanged.connect(
            self.handleInnerRadiiChanged
        )
        self.widget.containerOuterRadiiSpinBox.valueChanged.connect(
            self.handleOuterRadiiChanged
        )

        self.widget.containerSampleHeightSpinBox.valueChanged.connect(
            self.handleSampleHeightChanged
        )

        # Setup slots for density data.
        (
            self.widget.containerDensitySpinBox
        ).valueChanged.connect(self.handleDensityChanged)

        # Populate density units combo box.
        for du in UnitsOfDensity:
            self.widget.containerDensityUnitsComboBox.addItem(du.name, du)

        self.widget.containerDensityUnitsComboBox.currentIndexChanged.connect(
            self.handleDensityUnitsChanged
        )

        # Setup slots for other container configuration data.
        # Populate cross section source combo box.
        for c in CrossSectionSource:
            self.widget.containerTotalCrossSectionComboBox.addItem(c.name, c)

        (
            self.widget.containerTotalCrossSectionComboBox
        ).currentIndexChanged.connect(
            self.handleTotalCrossSectionChanged
        )

        self.widget.containerCrossSectionFileLineEdit.textChanged.connect(
            self.handleCrossSectionFileChanged
        )

        self.widget.browseContainerCrossSectionFileButton.clicked.connect(
            self.handleBrowseCrossSectionFile
        )

        self.widget.containerTweakFactorSpinBox.valueChanged.connect(
            self.handleTweakFactorChanged
        )

        self.widget.containerPackingFractionSpinBox.valueChanged.connect(
            self.handlePackingFractionChanged
        )

        self.widget.containerScatteringFractionSpinBox.valueChanged.connect(
            self.handleScatteringFractionChanged
        )
        (
            self.widget.containerAttenuationCoefficientSpinBox
        ).valueChanged.connect(
            self.handleAttenuationCoefficientChanged
        )

        self.widget.runAsSampleGroupBox.clicked.connect(
            self.handleToggleRunAsSample
        )

        # Setup slots for composition table.
        self.widget.insertContainerElementButton.clicked.connect(
            self.handleInsertElement
        )
        self.widget.removeContainerElementButton.clicked.connect(
            self.handleRemoveElement
        )

        self.widget.containerTopHatWidthSpinBox.valueChanged.connect(
            self.handleTopHatWidthChanged
        )

        # Fill top hat width combo box.
        for tp in FTModes:
            self.widget.containerFTModeComboBox.addItem(tp.name, tp)

        self.widget.containerFTModeComboBox.currentIndexChanged.connect(
            self.handleBackgroundScatteringSubtractionModeChanged
        )

        self.widget.containerMinSpinBox.valueChanged.connect(
            self.handleMinChanged
        )
        self.widget.containerMaxSpinBox.valueChanged.connect(
            self.handleMaxChanged
        )
        self.widget.containerBroadeningFunctionSpinBox.valueChanged.connect(
            self.handleBroadeningFunctionChanged
        )
        self.widget.containerBroadeningPowerSpinBox.valueChanged.connect(
            self.handleBroadeningPowerChanged
        )
        self.widget.containerStepSizeSpinBox.valueChanged.connect(
            self.handleStepSizeChanged
        )

    def handlePeriodNoChanged(self, value):
        """
        Slot for handling change in the period number.
        Called when a valueChanged signal is emitted,
        from the containerPeriodNoSpinBox.
        Alters the container's period number as such.
        Parameters
        ----------
        value : float
            The new value of the containerPeriodNoSpinBox.
        """
        self.container.periodNumber = value
        if not self.widgetsRefreshing:
            self.parent.setModified()
            if not self.parent.gudrunFile.purgeFile.excludeSampleAndCan:
                self.parent.gudrunFile.purged = False

    def handleGeometryChanged(self, index):
        """
        Slot for handling change in sample geometry.
        Called when a currentIndexChanged signal is emitted,
        from the containerGeometryComboBox.
        Alters the container geometry as such.
        Parameters
        ----------
        index : int
            The new current index of the containerGeometryComboBox.
        """
        self.container.geometry = (
            self.widget.containerGeometryComboBox.itemData(index)
        )
        self.widget.containerGeometryInfoStack.setCurrentIndex(
            self.container.geometry.value
        )

    def handleUpstreamThicknessChanged(self, value):
        """
        Slot for handling change in the upstream thickness.
        Called when a valueChanged signal is emitted,
        from the containerUpstreamSpinBox.
        Alters the container's upstream thickness as such.
        Parameters
        ----------
        value : float
            The new value of the containerUpstreamSpinBox.
        """
        self.container.upstreamThickness = value
        total = (
            self.container.upstreamThickness +
            self.container.downstreamThickness
        )
        self.widget.totalContainerThicknessLabel.setText(
            f"Total: {total} cm"
        )
        if not self.widgetsRefreshing:
            self.parent.setModified()

    def handleDownstreamThicknessChanged(self, value):
        """
        Slot for handling change in the downstream thickness.
        Called when a valueChanged signal is emitted,
        from the containerDownStreamSpinBox.
        Alters the container's downstream thickness as such.
        Parameters
        ----------
        value : float
            The new value of the containerDownStreamSpinBox.
        """
        self.container.downstreamThickness = value
        total = (
            self.container.upstreamThickness +
            self.container.downstreamThickness
        )
        self.widget.totalContainerThicknessLabel.setText(
            f"Total: {total} cm"
        )
        if not self.widgetsRefreshing:
            self.parent.setModified()

    def handleInnerRadiiChanged(self, value):
        """
        Slot for handling change in the inner radii.
        Called when a valueChanged signal is emitted,
        from the containerInnerRadiiSpinBox.
        Alters the container's inner radius as such.
        Parameters
        ----------
        value : float
            The new value of the containerInnerRadiiSpinBox.
        """
        self.container.innerRadius = value
        if not self.widgetsRefreshing:
            self.parent.setModified()

    def handleOuterRadiiChanged(self, value):
        """
        Slot for handling change in the outer radii.
        Called when a valueChanged signal is emitted,
        from the containerOuterRadiiSpinBox.
        Alters the container's outer radius as such.
        Parameters
        ----------
        value : float
            The new value of the containerOuterRadiiSpinBox.
        """
        self.container.outerRadius = value
        if not self.widgetsRefreshing:
            self.parent.setModified()

    def handleDensityChanged(self, value):
        """
        Slot for handling change in the density.
        Called when a valueChanged signal is emitted,
        from the containerDensitySpinBox.
        Alters the container's density as such.
        Parameters
        ----------
        value : float
            The new value of the containerDensitySpinBox.
        """
        self.container.density = value
        if not self.widgetsRefreshing:
            self.parent.setModified()

    def handleDensityUnitsChanged(self, index):
        """
        Slot for handling change in density units.
        Called when a currentIndexChanged signal is emitted,
        from the containerDensityUnitsComboBox.
        Alters the container density units as such.
        Parameters
        ----------
        index : int
            The new current index of the containerDensityUnitsComboBox.
        """
        self.container.densityUnits = (
            self.widget.containerDensityUnitsComboBox.itemData(index)
        )
        if not self.widgetsRefreshing:
            self.parent.setModified()

    def handleTotalCrossSectionChanged(self, index):
        """
        Slot for handling change in total cross section source.
        Called when a currentIndexChanged signal is emitted,
        from the containerTotalCrossSectionComboBox.
        Alters the container's total cross section source as such.
        Parameters
        ----------
        index : int
            The new current index of the containerTotalCrossSectionComboBox.
        """
        self.container.totalCrossSectionSource = (
            self.widget.containerTotalCrossSectionComboBox.itemData(index)
        )
        self.widget.containerCrossSectionFileWidget.setVisible(
            self.container.totalCrossSectionSource == CrossSectionSource.FILE
        )
        if not self.widgetsRefreshing:
            self.parent.setModified()

    def handleCrossSectionFileChanged(self, value):
        """
        Slot for handling change in total cross section source file name.
        Called when a textChanged signal is emitted,
        from the containerCrossSectionFileLineEdit.
        Alters the container's total cross section source file name as such.
        Parameters
        ----------
        value : str
            The new text of the containerCrossSectionFileLineEdit.
        """
        self.container.crossSectionFilename = value
        if not self.widgetsRefreshing:
            self.parent.setModified()

    def handleBrowseCrossSectionFile(self):
        """
        Slot for browsing for a cross section source file.
        Called when a clicked signal is emitted,
        from the browseContainerCrossSectionFileButton.
        Alters the corresponding line edit as such.
        as such.
        """
        filename, _ = QFileDialog.getOpenFileName(
            self.widget, "Total cross section source", "")
        if filename:
            self.widget.containerCrossSectionFileLineEdit.setText(filename)

    def handleTweakFactorChanged(self, value):
        """
        Slot for handling change in the sample tweak factor.
        Called when a valueChanged signal is emitted,
        from the containerTweakFactorSpinBox.
        Alters the container's tweak factor as such.
        Parameters
        ----------
        value : float
            The new value of the containerTweakFactorSpinBox.
        """
        self.container.tweakFactor = value
        self.packingFractionChanging = True
        if value > 0.0:
            self.widget.containerPackingFractionSpinBox.setValue(1.0 / value)
        else:
            self.widget.containerPackingFractionSpinBox.setValue(0.0)
        self.packingFractionChanging = False
        if not self.widgetsRefreshing:
            self.parent.setModified()

    def handlePackingFractionChanged(self, value):
        """
        Slot for handling change in the packing fraction.
        Called when a valueChanged signal is emitted,
        from the the containerPackingFractionSpinBox.
        Updates the containers's tweak factor to reflect
        the new packing fraction.
        Parameters
        ----------
        value : float
            The new current value of the containerPackingFractionSpinBox.
        """
        if not self.packingFractionChanging:
            if value > 0.0:
                self.widget.containerTweakFactorSpinBox.setValue(1.0 / value)
            else:
                self.widget.containerTweakFactorSpinBox.setValue(0.0)

    def handleAngleOfRotationChanged(self, value):
        """
        Slot for handling change in the angle of rotation.
        Called when a valueChanged signal is emitted,
        from the containerAngleOfRotationSpinBox.
        Alters the container's angle of rotation as such.
        Parameters
        ----------
        value : float
            The new value of the containerAngleOfRotationSpinBox.
        """
        self.container.angleOfRotation = value
        if not self.widgetsRefreshing:
            self.parent.setModified()

    def handleSampleWidthChanged(self, value):
        """
        Slot for handling change in the sample width.
        Called when a valueChanged signal is emitted,
        from the containerSampleWidthSpinBox.
        Alters the container's sample width as such.
        Parameters
        ----------
        value : float
            The new value of the containerSampleWidthSpinBox.
        """
        self.container.sampleWidth = value
        if not self.widgetsRefreshing:
            self.parent.setModified()

    def handleSampleHeightChanged(self, value):
        """
        Slot for handling change in the sample height.
        Called when a valueChanged signal is emitted,
        from the containerSampleHeightSpinBox.
        Alters the container's sample height as such.
        Parameters
        ----------
        value : float
            The new value of the containerSampleHeightSpinBox.
        """
        self.container.sampleHeight = value
        if not self.widgetsRefreshing:
            self.parent.setModified()

    def handleScatteringFractionChanged(self, value):
        """
        Slot for handling change in the container's environment
        scattering fraction.
        Called when a valueChanged signal is emitted,
        from the containerScatteringFractionSpinBox.
        Alters the container's scattering fraction as such.
        Parameters
        ----------
        value : float
            The new value of the containerScatteringFractionSpinBox.
        """
        self.container.scatteringFraction = value
        if not self.widgetsRefreshing:
            self.parent.setModified()

    def handleAttenuationCoefficientChanged(self, value):
        """
        Slot for handling change in the container's environment
        attenuation coefficient.
        Called when a valueChanged signal is emitted,
        from the containerAttenuationCoefficientSpinBox.
        Alters the container's attenuation coefficient as such.
        Parameters
        ----------
        value : float
            The new value of the containerAttenuationCoefficientSpinBox.
        """
        self.container.attenuationCoefficient = value
        if not self.widgetsRefreshing:
            self.parent.setModified()

    def handleToggleRunAsSample(self, state):
        """
        Slot for handling toggling running the container as
        a sample. Called when a clicked signal is emitted,
        from the runAsSampleCheckBox. Updates the class attribute
        as such.
        Parameters
        ----------
        state : int
            The new state of the runAsSampleGroupBox check box.
        """
        self.container.runAsSample = bool(state)
        if not self.widgetsRefreshing:
            self.parent.setModified()

    def handleDataFilesAltered(self):
        """
        Slot for handling an item in the data files list being changed.
        Called when an itemChanged signal is emitted,
        from the dataFilesList.
        Alters the container's data files as such.
        """
        if not self.widgetsRefreshing:
            self.parent.setModified()
            self.parent.gudrunFile.purged = False
            self.container.dataFiles.dataFiles = (
                self.widget.containerDataFilesList.model().stringList()
            )

    def addFiles(self, target, title, regex):
        """
        Slot for adding files to the data files list.
        Called when a clicked signal is emitted,
        from the addContainerDataFileButton.
        Parameters
        ----------
        target : QListWidget
            Target widget to add to.
        title : str
            Window title for QFileDialog.
        regex : str
            Regex-like expression to use for specifying file types.
        """
        files, _ = QFileDialog.getOpenFileNames(
            self.widget, title,
            self.parent.gudrunFile.instrument.dataFileDir, regex
        )
        for file in files:
            if file:
                target.insertRow(file.split(os.path.sep)[-1])

    def removeFile(self, target):
        """
        Slot for removing files from the data files list.
        Called when a clicked signal is emitted,
        from the removeSampleDataFileButton.
        Parameters
        ----------
        target : QListWidget
            Target widget to add to.
        """
        target.removeItem()

    def updateCompositionTable(self):
        """
        Fills the composition list.
        """
        self.widget.containerCompositionTable.makeModel(
            self.container.composition.elements, self.container
        )
        self.widget.containerCompositionTable.model().dataChanged.connect(
            self.handleElementChanged
        )
        if not self.widgetsRefreshing:
            self.parent.setModified()

    def handleInsertElement(self):
        """
        Slot for handling insertion to the composition table.
        Called when a clicked signal is emitted, from the
        insertContainerElementButton.
        """
        self.widget.containerCompositionTable.insertRow()
        self.updateExpectedDCSLevel()
        if not self.widgetsRefreshing:
            self.parent.setModified()

    def handleRemoveElement(self):
        """
        Slot for removing files from the data files list.
        Called when a clicked signal is emitted,
        from the removeContainerElementButton.
        """
        self.widget.containerCompositionTable.removeRow(
            self.widget.containerCompositionTable
            .selectionModel().selectedRows()
        )
        self.updateExpectedDCSLevel()
        if not self.widgetsRefreshing:
            self.parent.setModified()

    def handleElementChanged(self):
        """
        Slot for handling modifications to elements in the composition
        table. Called when a dataChanged signal is emitted,
        from the containerCompositionTable.
        """
        if not self.widgetsRefreshing:
            self.parent.setModified()

    def connectToModelSignals(self):
        self.widget.sampleCompositionTable.model().dataChanged.connect(
            self.updateExpectedDCSLevel
        )
        self.widget.sampleRatioCompositionTable.model().dataChanged.connect(
            self.updateExpectedDCSLevel
        )
        self.updateExpectedDCSLevel()

    def updateExpectedDCSLevel(self, _=None, __=None):
        """
        Updates the expectedDcsLabel,
        to show the expected DCS level of the container.
        """
        elements = self.container.composition.elements
        dcsLevel = self.container.composition.calculateExpectedDCSLevel(
            elements
        )
        self.widget.containerExpectedDcsLabel.setText(
            f"Expected DCS Level: {dcsLevel}"
        )
        if config.USE_USER_DEFINED_COMPONENTS:
            elements = self.container.composition.shallowTranslate()
            dcsLevel = self.container.composition.calculateExpectedDCSLevel(
                elements
            )
            self.widget.containerExpectedDcsLabel.setText(
                f"Expected DCS Level: {dcsLevel}"
            )
        else:
            elements = self.container.composition.elements
            dcsLevel = self.container.composition.calculateExpectedDCSLevel(
                elements
            )
            self.widget.containerExpectedDcsLabel.setText(
                f"Expected DCS Level: {dcsLevel}"
            )
        if self.widget.containerDcsLabel.text() != "DCS Level":
            actualDcsLevel = nthfloat(self.widget.containerDcsLabel.text(), 2)
            error = round(
                ((actualDcsLevel - dcsLevel) / actualDcsLevel)*100, 1
            )
            self.widget.containerResultLabel.setText(f"{error}%")
            if abs(error) > 10:
                self.widget.containerResultLabel.setStyleSheet(
                    "background-color: red"
                )
            else:
                self.widget.containerResultLabel.setStyleSheet(
                    "background-color: green"
                )

    def handleTopHatWidthChanged(self, value):
        """
        Slot for handling change in the top hat width.
        Called when a valueChanged signal is emitted,
        from the the containerTopHatWidthSpinBox.
        Alters the container's top hat width as such.
        Parameters
        ----------
        value : float
            The new current value of the containerTopHatWidthSpinBox.
        """
        self.container.topHatW = value
        if not self.widgetsRefreshing:
            self.parent.setModified()

    def handleBackgroundScatteringSubtractionModeChanged(self, index):
        """
        Slot for handling change in FT Mode.
        Called when a currentIndexChanged signal is emitted,
        from the containerFTModeComboBox.
        Alters the container's FT mode as such.
        Parameters
        ----------
        index : int
            The new current index of the
            containerFTModeComboBox.
        """
        self.container.FTMode = (
            self.widget.FTModeComboBox.itemData(index)
        )

        if not self.widgetsRefreshing:
            self.parent.setModified()

    def handleMinChanged(self, value):
        """
        Slot for handling change in the minimum radius for FT.
        Called when a valueChanged signal is emitted,
        from the the containerMinSpinBox.
        Alters the container's minimum radius for FT as such.
        Parameters
        ----------
        value : float
            The new current value of the containerMinSpinBox.
        """
        self.container.minRadFT = value
        if not self.widgetsRefreshing:
            self.parent.setModified()

    def handleMaxChanged(self, value):
        """
        Slot for handling change in the maximum radius for FT.
        Called when a valueChanged signal is emitted,
        from the the containerMaxSpinBox.
        Alters the container's maximum radius for FT as such.
        Parameters
        ----------
        value : float
            The new current value of the containerMaxSpinBox.
        """
        self.container.maxRadFT = value
        if not self.widgetsRefreshing:
            self.parent.setModified()

    def handleBroadeningFunctionChanged(self, value):
        """
        Slot for handling change in g(r) broadening at r = 1A.
        Called when a valueChanged signal is emitted,
        from the the containerBroadeningFunctionSpinBox.
        Alters the container's broadening function as such.
        Parameters
        ----------
        value : float
            The new current value of the containerBroadeningFunctionSpinBox.
        """
        self.container.grBroadening = value
        if not self.widgetsRefreshing:
            self.parent.setModified()

    def handleBroadeningPowerChanged(self, value):
        """
        Slot for handling change in the power for broadening.
        Called when a valueChanged signal is emitted,
        from the the containerBroadeningPowerSpinBox.
        Alters the container's broadening power as such.
        Parameters
        ----------
        value : float
            The new current value of the containerBroadeningPowerSpinBox.
        """
        self.container.powerForBroadening = value
        if not self.widgetsRefreshing:
            self.parent.setModified()

    def handleStepSizeChanged(self, value):
        """
        Slot for handling change in the step size in radius for final g(r).
        Called when a valueChanged signal is emitted,
        from the containerStepSizeSpinBox.
        Alters the container's step size as such.
        Parameters
        ----------
        value : float
            The new current value of the containerStepSizeSpinBox.
        """
        self.container.stepSize = value
        if not self.widgetsRefreshing:
            self.parent.setModified()
