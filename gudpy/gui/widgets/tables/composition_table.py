from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QAction, QCursor
from PySide6.QtWidgets import (
    QMainWindow, QMenu, QTableView
)
from PySide6.QtCore import Signal

from core import config
from core.mass_data import massData
from core.isotopes import Sears91
from gui.widgets.tables.gudpy_tables import GudPyTableModel
from gui.widgets.tables.composition_delegate import CompositionDelegate
from core.element import Element
from copy import deepcopy


class CompositionModel(GudPyTableModel):
    """
    Class to represent a CompositionModel. Inherits GudPyTableModel.

    ...

    Methods
    -------
    columnCount(parent)
        Returns the number of columns in the model.
    setData(index, value, role)
        Sets data in the model.
    insertRow(data)
        Inserts a row of data into the model.
    data(index, role)
        Returns data at a specific index.
    """
    def __init__(self, data, headers, parent):
        """
        Calls super().__init__ on the passed parameters.
        Sets up attrs dict.
        Parameters
        ----------
        data : list
            Data for model to use.
        headers: str[]
            Column headers for table.
        parent : QWidget
            Parent widget.
        """
        super(CompositionModel, self).__init__(data, headers, parent)
        self.attrs = {0: "atomicSymbol", 1: "massNo", 2: "abundance"}

    def columnCount(self, parent):
        """
        Returns the number of columns in the model.
        Parameters
        ----------
        parent : QWidget
            Parent widget.
        Returns
        -------
        int
            Number of columns in the model - this is always 3.
        """
        return 3

    def setData(self, index, value, role):
        """
        Sets data in the model.
        Parameters
        ----------
        index : QModelIndex
            Index to set data at.
        value : any
            Value to set data to.
        role : int
            Role.
        """
        row = index.row()
        col = index.column()
        if role == Qt.EditRole:
            sears91 = Sears91()
            if col == 0:
                if value == "D":
                    self._data[row].atomicSymbol = "H"
                    self._data[row].massNo = 2
                    self.dataChanged.emit(index, index)
                    return True
                elif value not in massData.keys():
                    return False
                if not sears91.isIsotope(
                    value, self._data[row].__dict__[self.attrs[1]]
                ):
                    self._data[row].__dict__[self.attrs[1]] = 0
                    self.dataChanged.emit(
                        self.index(row, 1, QModelIndex()),
                        self.index(row, 1, QModelIndex())
                    )
            if col == 1:
                if (
                    self._data[row].__dict__[self.attrs[0]]
                    and not sears91.isIsotope(
                        self._data[row].__dict__[self.attrs[0]],
                        value
                    )
                ):
                    return False
            self._data[row].__dict__[self.attrs[col]] = value
            self.dataChanged.emit(index, index)

    def insertRow(self):
        """
        Inserts a row of data into the model.
        The data is always by default "", 0, 0
        Calls super().insertRow().
        """
        self.beginInsertRows(
            QModelIndex(), self.rowCount(self), self.rowCount(self)
        )
        self._data.append(Element("H", 0, 0))
        self.endInsertRows()

    def data(self, index, role):
        """
        Returns the data at a given index.
        Parameters
        ----------
        index : QModelIndex
            Index to return data from.
        role : int
            Role
        Returns
        -------
        tuple
            str, float, float
            Element attributes.
        """
        row = index.row()
        col = index.column()
        if role == role & (Qt.DisplayRole | Qt.EditRole):
            if (
                config.NORMALISE_COMPOSITIONS
                and col == 2
                and config.USE_USER_DEFINED_COMPONENTS
            ):
                return (
                    self._data[row].abundance /
                    sum([el.abundance for el in self._data])
                )
            if col == 1:
                sears91 = Sears91()
                isotope = sears91.findIsotope(
                    self.data(self.index(row, 0), Qt.EditRole),
                    self._data[row].__dict__[self.attrs[1]]
                )
                return sears91.isotope(isotope)
            return self._data[row].__dict__[self.attrs[col]]


class CompositionTable(QTableView):
    """
    Class to represent a CompositionTable. Inherits QTableView.

    ...
    Attributes
    ----------
    parent : QWidget
        Parent widget.
    compositions : Composition[]
        List of all compositions.
    Methods
    -------
    makeModel(data)
        Creates the model using the data.
    insertRow()
        Inserts a row into the model.
    removeRow(rows)
        Removes selected rows from the model.
    farmCompositions()
        Collect compositions from normalisation, all samples and containers.
    copyFrom(composition)
        Create a new model from a given composition.
    showContextMenu(event)
        Creates context menu.
    mousePressEvent(event)
        Handles mouse presses.
    """

    modelChanged = Signal()

    def __init__(self, parent):
        """
        Constructs all the necessary attributes
        for the CompositionTable object.
        Calls super().__init__.
        Parameters
        ----------
        parent : QWidget
            Parent widget.
        """
        self.parent = parent
        self.compositions = []
        self.parentObject = None
        super(CompositionTable, self).__init__(parent=parent)

    def makeModel(self, data, parentObject, contextMenu=True):
        """
        Makes the model and the delegate based on the data.
        Collects all compositions.
        Parameters
        ----------
        data : list
            Data for model to use.
        """
        self.contextMenu = contextMenu
        self.setModel(
            CompositionModel(
                data, ["Element", "Isotope", "Abundance"], self.parent
            )
        )
        self.parentObject = parentObject
        self.setItemDelegate(CompositionDelegate())
        self.modelChanged.emit()

    def insertRow(self):
        """
        Inserts a row into the model.
        """
        self.model().insertRow()

    def removeRow(self, rows):
        """
        Removes rows from the model.
        Parameters
        ----------
        rows : QModelIndexList
            Rows to be removed.
        """
        for _row in rows:
            self.model().removeRow(_row.row())

    def farmCompositions(self):
        """
        Seeks up the widget heirarchy, and then collects all compositions.
        """
        ancestor = self.parent
        while not isinstance(ancestor, QMainWindow):
            ancestor = ancestor.parent
            if callable(ancestor):
                ancestor = ancestor()
        self.compositions.clear()
        self.compositions = [
                (
                    "Normalisation",
                    deepcopy(ancestor.gudrunFile.normalisation.composition)
                )
            ]
        for sampleBackground in ancestor.gudrunFile.sampleBackgrounds:
            for sample in sampleBackground.samples:
                if sample != self.parentObject:
                    self.compositions.append((sample.name, sample.composition))
                for container in sample.containers:
                    if container != self.parentObject:
                        self.compositions.append(
                            (container.name, container.composition)
                        )

    def copyFrom(self, composition):
        """
        Create a new model from a given composition,
        and replaces the current model with it.
        Parameters
        ----------
        composition : Composition
            Composition object to copy elements from.
        """
        self.parentObject.composition.elements = composition
        self.makeModel(composition.elements, self.parentObject)

    def showContextMenu(self, event):
        """
        Creates context menu, so that on right clicking the table,
        the user is able to copy compositions in.
        Parameters
        ----------
        event : QMouseEvent
            The event that triggers the context menu.
        """
        if self.contextMenu:
            self.farmCompositions()
            self.setContextMenuPolicy(Qt.ActionsContextMenu)
            self.menu = QMenu(self)
            copyMenu = self.menu.addMenu("Copy from")
            actionMap = {}
            for composition in self.compositions:
                action = QAction(f"{composition[0]}", copyMenu)
                copyMenu.addAction(action)
                actionMap[action] = composition[1]
            action = self.menu.exec(QCursor.pos())
            if action:
                self.copyFrom(deepcopy(actionMap[action]))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.showContextMenu(event)
            event.accept()
        else:
            return super().mousePressEvent(event)
