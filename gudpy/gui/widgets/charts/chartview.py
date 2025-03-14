from PySide6.QtCharts import QChartView
from PySide6.QtCore import QRectF, QRect, Qt
from PySide6.QtGui import (
    QAction, QClipboard, QCursor, QPainter, QMouseEvent, QContextMenuEvent
)
from PySide6.QtWidgets import (
    QApplication, QMenu, QSizePolicy
)

from core.container import Container
from core.sample import Sample
from gui.widgets.charts.chart import GudPyChart
from gui.widgets.charts.enums import PlotModes, SeriesTypes
from gui.widgets.charts.enums import Axes


class GudPyChartView(QChartView):
    """
    Class to represent a GudPyChartView. Inherits QChartView.

    ...
    Attributes
    ----------
    chart : GudPyChart
        Chart to be shown in the view.
    Methods
    -------
    wheelEvent(event):
        Event handler for using the scroll wheel.
    toggleLogarithmicAxes():
        Toggles logarithmic axes in the chart.
    contextMenuEvent(event):
        Creates context menu.
    keyPressEvent(event):
        Handles key presses.
    enterEvent(event):
        Handles the mouse entering the chart view.
    leaveEvent(event):
        Handles the mouse leaving the chart view.
    """
    def __init__(self, parent):
        """
        Constructs all the necessary attributes for the GudPyChartView object.
        Calls super()._init__ which calls the dunder init method
        from QChartView.
        Parameters
        ----------
        parent : QWidget, optional
            Parent widget.
        """
        super(GudPyChartView, self).__init__(parent=parent)

        # Set size policy.
        self.setSizePolicy(
            QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        )

        # Enable rectangualar rubber banding.
        self.setRubberBand(QChartView.RectangleRubberBand)

        # Enable Antialiasing.
        self.setRenderHint(QPainter.Antialiasing)
        self.clipboard = QClipboard(self.parent())

        self.previousPos = 0

    def wheelEvent(self, event):
        """
        Event handler called when the scroll wheel is used.
        This event is overridden for zooming in/out.
        Parameters
        ----------
        event : QWheelEvent
            Event that triggered the function call.
        """
        # Decide on the zoom factor.
        # If y > 0, zoom in, if y < 0 zoom out.
        zoomFactor = 2.0 if event.angleDelta().y() > 0 else 0.5

        # Create QRect area to zoom in on.
        chartArea = self.chart().plotArea()
        left = chartArea.left()
        top = chartArea.top()
        width = chartArea.width() / zoomFactor
        height = chartArea.height() / zoomFactor
        zoomArea = QRectF(left, top, width, height)

        # Move the rectangle to the mouse position.
        mousePos = self.mapFromGlobal(QCursor.pos())
        zoomArea.moveCenter(mousePos)

        # Zoom in on the area.
        self.chart().zoomIn(zoomArea)

        # Scroll to match the zoom.
        delta = self.chart().plotArea().center() - mousePos
        self.chart().scroll(delta.x(), -delta.y())

    def mouseMoveEvent(self, event):
        if isinstance(event, QMouseEvent):
            if event.buttons() & Qt.MouseButton.MiddleButton:

                if self.previousPos:
                    offset = event.pos() - self.previousPos
                else:
                    offset = event.pos()
                self.chart().zoom(1 + 0.00000001)
                self.chart().scroll(-offset.x(), offset.y())

                self.previousPos = event.pos()
                event.accept()
            else:
                if type(self.chart()) == GudPyChart:
                    if self.chart().plotArea().contains(event.pos()):
                        pos = self.chart().mapToValue(event.pos())
                        self.chart().label.setPlainText(
                            f"x={round(pos.x(), 4)}, y={round(pos.y(), 4)}"
                        )
                        if not self.chart().label.isVisible():
                            self.chart().label.show()
                    else:
                        self.chart().label.hide()
            return super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if isinstance(event, QMouseEvent):
            if event.button() == Qt.MouseButton.MiddleButton:
                self.previousPos = event.pos()
            elif event.button() == Qt.MouseButton.LeftButton:
                # Catch the origin of the rubber band.
                self.rubberBandOrigin = event.pos()

            event.accept()
        return super().mousePressEvent(event)

    def copyPlot(self):
        pixMap = self.grab()
        self.clipboard.setPixmap(pixMap)

    def mouseReleaseEvent(self, event):
        if isinstance(event, QMouseEvent):
            if event.button() == Qt.MouseButton.RightButton:
                event.accept()
            elif event.button() == Qt.MouseButton.LeftButton:

                # Collect dims for rubber band rect.
                width = event.pos().x() - self.rubberBandOrigin.x()
                height = event.pos().y() - self.rubberBandOrigin.y()

                # Create QRect area to zoom in on.
                zoomArea = QRect(
                    self.rubberBandOrigin.x(),
                    self.rubberBandOrigin.y(),
                    width,
                    height
                ).normalized()

                # Zoom in on the area.
                self.chart().zoomIn(zoomArea)

                # Disable, then re-enable rubber banding
                # to force hiding of the rect.
                self.setRubberBand(QChartView.NoRubberBand)
                event.accept()
                self.setRubberBand(QChartView.RectangleRubberBand)
        return super(GudPyChartView, self).mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        """
        Handles key presses.
        Used for implementing hotkeys / shortcuts.
        """
        modifiers = QApplication.keyboardModifiers()
        if event.key() == Qt.Key_C and modifiers == Qt.ControlModifier:
            self.copyPlot()
        # 'L/l' refers to logarithms.
        elif event.key() == Qt.Key_L:
            # Get the modifiers e.g. shift, control etc.
            # 'Ctrl+L/l' toggles logarithmic X-axis.
            if modifiers == Qt.ControlModifier:
                self.toggleLogarithmicAxes(Axes.X)
            # 'Ctrl+Shift+L/l' toggles logarithmic Y-axis.
            elif modifiers == (Qt.ControlModifier | Qt.ShiftModifier):
                self.toggleLogarithmicAxes(Axes.Y)
            else:
                # 'L/l' toggles both axes.
                self.toggleLogarithmicAxes(Axes.A)
        # 'A/a' refers to resetting the zoom / showing the limits.
        elif event.key() == Qt.Key_A:
            self.chart().zoomReset()
        return super().keyPressEvent(event)

    def enterEvent(self, event):
        """
        Handles the mouse entering the chart view.
        Gives focus to the chart view.
        """

        # Acquire focus.
        self.setFocus(Qt.OtherFocusReason)
        return super().enterEvent(event)

    def leaveEvent(self, event):
        """
        Handles the mouse leaving the chart view.
        Gives focus back to the parent.
        """
        # Relinquish focus.
        self.parent().setFocus(Qt.OtherFocusReason)
        return super().leaveEvent(event)

    def contextMenuEvent(self, event):
        """
        Creates context menu, so that on right clicking the chartview,
        the user is able to perform actions.
        Parameters
        ----------
        event : QMouseEvent
            The event that triggers the context menu.
        """
        if isinstance(event, QContextMenuEvent):
            self.menu = QMenu(self)
            actionMap = {}
            if self.chart():

                resetAction = QAction("Reset View", self.menu)
                resetAction.triggered.connect(self.chart().zoomReset)
                self.menu.addAction(resetAction)

                toggleLogarithmicMenu = QMenu(self.menu)
                toggleLogarithmicMenu.setTitle("Toggle logarithmic axes")

                toggleLogarithmicAllAxesAction = QAction(
                    "Toggle logarithmic all axis", toggleLogarithmicMenu
                )

                toggleLogarithmicAllAxesAction.setCheckable(True)
                toggleLogarithmicAllAxesAction.setChecked(
                    self.chart().logarithmicX
                    & self.chart().logarithmicY
                )
                toggleLogarithmicAllAxesAction.triggered.connect(
                    lambda: self.toggleLogarithmicAxes(Axes.A)
                )
                toggleLogarithmicMenu.addAction(toggleLogarithmicAllAxesAction)

                toggleLogarithmicXAxisAction = QAction(
                    "Toggle logarithmic X-axis", toggleLogarithmicMenu
                )
                toggleLogarithmicXAxisAction.setCheckable(True)
                toggleLogarithmicXAxisAction.setChecked(
                    self.chart().logarithmicX
                )
                toggleLogarithmicXAxisAction.triggered.connect(
                    lambda: self.toggleLogarithmicAxes(Axes.X)
                )
                toggleLogarithmicMenu.addAction(toggleLogarithmicXAxisAction)

                toggleLogarithmicYAxisAction = QAction(
                    "Toggle logarithmic Y-axis", toggleLogarithmicMenu
                )
                toggleLogarithmicYAxisAction.setCheckable(True)
                toggleLogarithmicYAxisAction.setChecked(
                    self.chart().logarithmicY
                )
                toggleLogarithmicYAxisAction.triggered.connect(
                    lambda: self.toggleLogarithmicAxes(Axes.Y)
                )
                toggleLogarithmicMenu.addAction(toggleLogarithmicYAxisAction)

                self.menu.addMenu(toggleLogarithmicMenu)

                if self.chart().plotMode in [
                    PlotModes.SF_MDCS01, PlotModes.SF_MDCS01_CANS
                ]:
                    showDCSLevelAction = QAction("Show dcs level", self.menu)
                    showDCSLevelAction.setCheckable(True)
                    showDCSLevelAction.setChecked(
                        self.chart().isVisible(SeriesTypes.DCSLEVEL)
                    )
                    showDCSLevelAction.triggered.connect(
                        lambda: self.chart().toggleVisible(
                            SeriesTypes.DCSLEVEL
                        )
                    )
                    self.menu.addAction(showDCSLevelAction)
                elif (
                    self.chart().plotMode in
                    [
                        PlotModes.RDF,
                        PlotModes.RDF_CANS
                    ]
                ):
                    showMdor01Action = QAction("Show mdor01 data", self.menu)
                    showMdor01Action.setCheckable(True)
                    showMdor01Action.setChecked(
                        self.chart().isVisible(SeriesTypes.MDOR01)
                    )
                    showMdor01Action.triggered.connect(
                        lambda: self.chart().toggleVisible(
                            SeriesTypes.MDOR01
                        )
                    )
                    self.menu.addAction(showMdor01Action)

                    showMgor01Action = QAction("Show mgor01 data", self.menu)
                    showMgor01Action.setCheckable(True)
                    showMgor01Action.setChecked(
                        self.chart().isVisible(SeriesTypes.MGOR01)
                    )
                    showMgor01Action.triggered.connect(
                        lambda: self.chart().toggleVisible(
                            SeriesTypes.MGOR01
                        )
                    )
                    self.menu.addAction(showMgor01Action)
                if len(self.chart().samples) > 1:
                    showMenu = QMenu(self.menu)
                    showMenu.setTitle("Show..")
                    if self.chart().plotMode in [
                        PlotModes.SF_MINT01,
                        PlotModes.SF_MDCS01, PlotModes.RDF
                    ]:
                        samples = [
                            sample for sample in self.chart().samples
                            if isinstance(sample, Sample)
                        ]
                    elif self.chart().plotMode in [
                        PlotModes.SF_MINT01_CANS,
                        PlotModes.SF_MDCS01_CANS, PlotModes.RDF_CANS
                    ]:
                        samples = [
                            sample for sample in self.chart().samples
                            if isinstance(sample, Container)
                        ]
                    for sample in samples:
                        action = QAction(f"Show {sample.name}", showMenu)
                        action.setCheckable(True)
                        action.setChecked(self.chart().isSampleVisible(sample))
                        showMenu.addAction(action)
                        actionMap[action] = sample
                    self.menu.addMenu(showMenu)

            copyAction = QAction("Copy plot", self.menu)
            copyAction.triggered.connect(self.copyPlot)
            self.menu.addAction(copyAction)

            action = self.menu.exec(QCursor.pos())

            if action in actionMap.keys():
                self.chart().toggleSampleVisibility(
                    action.isChecked(),
                    actionMap[action]
                )

    def toggleLogarithmicAxes(self, axis):
        """
        Toggles logarithmic axes in the chart.
        """
        self.chart().toggleLogarithmicAxis(axis)

    def setChart(self, chart):
        if type(chart) == GudPyChart:
            chart.label.setPos(
                self.mapToScene(
                    25, self.sceneRect().height()-50
                )
            )
            chart.label.show()
        return super().setChart(chart)

    def resizeEvent(self, event):
        if type(self.chart()) == GudPyChart:
            self.chart().label.setPos(
                self.mapToScene(25, self.sceneRect().height()-50)
            )
        return super().resizeEvent(event)
