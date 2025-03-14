from copy import deepcopy
from PySide6.QtGui import QCursor, QIcon, QAction
from PySide6.QtWidgets import QMenu, QTreeView
from PySide6.QtCore import (
    QAbstractItemModel,
    QModelIndex,
    QPersistentModelIndex,
    Qt
)

from core import config
from core.composition import Components
from core.instrument import Instrument
from core.beam import Beam
from core.normalisation import Normalisation
from core.sample import Sample
from core.sample_background import SampleBackground
from core.container import Container
from core.config import NUM_GUDPY_CORE_OBJECTS


class GudPyTreeModel(QAbstractItemModel):
    """
    Class to represent a GudPyTreeModel. To be used with a GudyTree object.
    Inherits QAbstractTreeModel.

    ...

    Attributes
    ----------
    gudrunFile : GudrunFile
        GudrunFile object associated with the model.
    persistentIndexes : dict
        Dict of QPersistentIndexes,
        key is a GudPy object, value is a QPersistentIndex.
    sampleIcon : QIcon
        Icon for samples.
    containerIcon : QIcon
        Icon for containers.
    Methods
    -------
    index(row, column, parent)
        Returns index associated with given row, column and parent.
    parent(index)
        Returns parent of a given index.
    findParent(item)
        Finds the parent of a given Sample or Container.
    data(index, role)
        Returns the data at a given index.
    setData(index, value, role)
        Sets data at a given index.
    checkState(index)
        Returns the check state of a given index.
    rowCount(parent)
        Returns the row count of an index.
    columnCount(parent)
        Returns the column count of an index.
    setEnabled(state)
        Enables/disables "editing" of the tree.
    flags(index)
        Returns flags associated with a given index.
    isSample(index)
        Returns whether a given index is associated with a sample.
    isIncluded(index)
        Returns whether a given index of a sample is to be ran.
    insertRow(obj, parent)
        Insert a row containing an object to a parent index.
    removeRow(index)
        Remove a row from an index.
    """

    def __init__(self, parent, gudrunFile):
        """
        Constructs all the necessary attributes for the GudPyTreeModel object.
        Calls super()._init__ which calls the dunder init method
        from QAbstractItemModel.
        Parameters
        ----------
        parent : QWidget
            Parent widget.
        gudrunFile : GudrunFile
            GudrunFile object for model to use.
        """
        super(GudPyTreeModel, self).__init__(parent)
        self.gudrunFile = gudrunFile
        self.persistentIndexes = {}
        self.sampleIcon = QIcon(":/icons/sample")
        self.containerIcon = QIcon(":/icons/container")
        self.setEnabled(True)

    def index(self, row, column, parent=QModelIndex()):
        """
        Returns index associated with given row, column and parent.
        If no such index is possible, then an invalid QModelIndex
        is returned.
        Creates a QPersistentModelIndex and adds it to the dict,
        to keep the internal pointer of the QModelIndex in
        reference.
        Parameters
        ----------
        row : int
            Row number.
        column : int
            Column number.
        parent, optional: QModelIndex
            Parent index.
        Returns
        -------
        QModelIndex
            The index created.
        """
        # Check for invalid index.
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        elif not parent.isValid():
            # Invalid parent means we are at the top level.
            rows = {
                0: self.gudrunFile.instrument, 1: self.gudrunFile.beam,
                2: self.gudrunFile.components, 3: self.gudrunFile.normalisation
            }
            # Instrument | Beam | Normalisation
            if row in rows.keys():
                obj = rows[row]
            else:
                obj = self.gudrunFile.sampleBackgrounds[
                    row-NUM_GUDPY_CORE_OBJECTS
                ]
        elif parent.isValid() and not parent.parent().isValid():
            # Valid parent and invalid grandparent, means that the index
            # corresponds to a sample.
            obj = (
                self.gudrunFile.sampleBackgrounds[
                    parent.row()-NUM_GUDPY_CORE_OBJECTS
                ]
                .samples[row]
            )
        elif parent.isValid() and parent.parent().isValid():
            # Valid parent and grandparent means that the index
            # corresponds to a container.
            obj = (
                self.gudrunFile.sampleBackgrounds[
                    parent.parent().row()-NUM_GUDPY_CORE_OBJECTS
                ].samples[parent.row()].containers[row]
            )
        else:
            # Otherwise we return an invalid index.
            return QModelIndex()
        # Create the index and add a QPersistentModelIndex
        # constructed from the index, to the dict.
        index = self.createIndex(row, 0, obj)
        self.persistentIndexes[obj] = QPersistentModelIndex(index)
        return index

    def parent(self, index):
        """
        Returns parent of a given index.
        If the index is invalid, then an invalid QModelIndex is returned.
        Parent is decided on by checking the data type of the internal pointer
        of the index.
        Parameters
        ----------
        index : QModelIndex
            Index to find parent index of.
        Returns
        -------
        QModelIndex
            Parent index.
        """
        if not index.isValid():
            return QModelIndex()
        if isinstance(
            index.internalPointer(),
            (Instrument, Beam, Components, Normalisation, SampleBackground)
        ):
            return QModelIndex()
        elif isinstance(index.internalPointer(), Sample):
            parent = self.findParent(index.internalPointer())
            return QModelIndex(self.persistentIndexes[parent])
        elif isinstance(index.internalPointer(), Container):
            parent = self.findParent(index.internalPointer())
            return QModelIndex(self.persistentIndexes[parent])
        else:
            return QModelIndex()

    def findParent(self, item):
        """
        Finds the parent of a given Sample or Container.
        Parameters
        ----------
        item : Sample | Container
            Object to find parent of.
        Returns
        -------
        SampleBackground | Sample
            Parent object.
        """
        for i, sampleBackground in enumerate(
            self.gudrunFile.sampleBackgrounds
        ):
            if isinstance(item, Sample):
                if item in sampleBackground.samples:
                    return self.gudrunFile.sampleBackgrounds[i]
            elif isinstance(item, Container):
                for j, sample in enumerate(sampleBackground.samples):
                    if item in sample.containers:
                        return self.gudrunFile.sampleBackgrounds[i].samples[j]

    def data(self, index, role):
        """
        Returns the data at a given index.
        If the index is invalid, or the role is not
        Qt.EditRole | Qt.DisplayRole | Qt.CheckStateRole, then an empty
        QVariant is returned.
        Otherwise returns check state of index, or a QVariant constructed
        from its name.
        Parameters
        ----------
        index : QModelIndex
            Index to extract data from.
        role : int
            Role.
        Returns
        -------
        QVariant | QCheckState
            Data at index.
        """
        if not index.isValid():
            return None
        if role == Qt.DisplayRole or role == Qt.EditRole:
            if isinstance(
                index.internalPointer(),
                (Instrument, Beam, Components, Normalisation, SampleBackground)
            ):
                dic = {
                    0: "Instrument", 1: "Beam",
                    2: "Components", 3: "Normalisation", 4: "Sample Background"
                }
                return (
                    dic[
                        index.row() if index.row() <= NUM_GUDPY_CORE_OBJECTS
                        else NUM_GUDPY_CORE_OBJECTS
                    ]
                )
            elif isinstance(index.internalPointer(), (Sample, Container)):
                return index.internalPointer().name
        elif role == Qt.DecorationRole:
            if isinstance(index.internalPointer(), Sample):
                return self.sampleIcon
            elif isinstance(index.internalPointer(), Container):
                return self.containerIcon
        elif role == Qt.CheckStateRole and self.isSample(index):
            return self.checkState(index)
        else:
            return None

    def setData(self, index, value, role):
        """
        Sets data at a given index, if the index is valid.
        Only used for assigning CheckStates to samples,
        and altering the names of samples/containers.
        Parameters
        ----------
        index : QModelIndex
            Index to set data at.
        value : QCheckState
            Value to assign to data.
        role : int
            Role.
        Returns
        -------
        bool
            Success / Failure.
        """
        if not index.isValid():
            return False
        elif role == Qt.CheckStateRole and self.isSample(index):
            if value == Qt.Checked:
                index.internalPointer().runThisSample = True
            else:
                index.internalPointer().runThisSample = False
            self.dataChanged.emit(index, index)
            return True
        elif (
            role == Qt.EditRole
            and (self.isSample(index) or self.isContainer(index))
        ):
            index.internalPointer().name = value
            self.dataChanged.emit(index, index)
            return True
        else:
            return False

    def checkState(self, index):
        """
        Returns the check state of a given index.
        Parameters
        ----------
        index : QModelIndex
            Index to return check state from.
        Returns
        -------
        QCheckState
            Check state.
        """
        return Qt.Checked if self.isIncluded(index) else Qt.Unchecked

    def rowCount(self, parent=QModelIndex()):
        """
        Returns the row count of a given parent index.
        The row count returned depends on the data type of the parent.
        Parameters
        ----------
        parent : QModelIndex
            Parent index to retrieve row count from.
        Returns
        -------
        int
            Row count.
        """
        # If the parent is invalid, then it is a top level node.
        if not parent.isValid():
            # Instrument + Beam + Normalisation + N SampleBackgrounds
            return (
                NUM_GUDPY_CORE_OBJECTS
                + len(self.gudrunFile.sampleBackgrounds)
            )
        elif parent.isValid() and not parent.parent().isValid():
            # If the parent is valid, but the grandparent is invalid
            # Return the number of samples of the sample background.
            if (
                parent.row() >= NUM_GUDPY_CORE_OBJECTS
                and len(self.gudrunFile.sampleBackgrounds)
            ):
                return len(
                    self.gudrunFile.sampleBackgrounds[
                        parent.row()-NUM_GUDPY_CORE_OBJECTS
                    ].samples
                )
            else:
                return 0
        elif (
            parent.isValid()
            and parent.parent().isValid()
            and not parent.parent().parent().isValid()
        ):
            # If it is a leaf, then return the number of
            # containers for the sample.
            return len(
                self.gudrunFile.sampleBackgrounds[
                    parent.parent().row()-NUM_GUDPY_CORE_OBJECTS
                ].samples[parent.row()].containers
            )
        else:
            return 0

    def columnCount(self, parent=QModelIndex()):
        """
        Returns the column count of an index.
        Parameters
        ----------
        parent : QModelIndex
            Parent index to retrieve column row count from.
        Returns
        -------
        int
            Column count. This is always 1.
        """
        return 1

    def setEnabled(self, state):
        self.flags_ = {}
        # self.flags_[Sample]
        if state:
            self.flags_[Sample] = Qt.ItemIsEditable | Qt.ItemIsUserCheckable
            self.flags_[Container] = Qt.ItemIsEditable
        else:
            self.flags_[Sample] = Qt.NoItemFlags
            self.flags_[Container] = Qt.NoItemFlags

    def flags(self, index):
        """
        Returns flags associated with a given index.
        Parameters
        ----------
        index : QModelIndex
            Index to retreive flags from.
        Returns
        -------
        int
            Flags.
        """
        flags = super().flags(index)
        # If it is a sample, append checkable flag.
        if self.isSample(index):
            flags |= self.flags_[Sample]
        # If it is a container, return current flags_.
        elif self.isContainer(index):
            flags |= self.flags_[Container]
        return flags

    def isSample(self, index):
        """
        Returns whether a given index is associated with a sample.
        Parameters
        ----------
        index : QModelIndex
            Index to check if sample is associated with.
        Returns
        -------
        bool
            Is it a sample or not?
        """
        return isinstance(index.parent().internalPointer(), SampleBackground)

    def isContainer(self, index):
        """
        Returns whether a given index is associated with a container.
        Parameters
        ----------
        index : QModelIndex
            Index to check if container is associated with.
        Returns
        -------
        bool
            Is it a container or not?
        """
        return isinstance(index.parent().internalPointer(), Sample)

    def isIncluded(self, index):
        """
        Returns whether a given index of a sample is to be ran.
        Parameters
        ----------
        index : QModelIndex
            Index to check if the associated sample is to be included or not.
        Returns
        -------
        bool
            Is it to be included?
        """
        return self.isSample(index) and index.internalPointer().runThisSample

    def insertRow(self, obj, parent):
        """
        Insert a row containing an object to a parent index.
        Parameters
        ----------
        obj : SampleBackground | Sample | Container
            Object to be inserted.
        parent : QModelIndex
            Parent index to append to.
        """
        # Get the parent object.
        parentObj = parent.internalPointer()

        # Dict for deciding if the object has a valid parent.
        validParents = {
            SampleBackground: not isinstance(parentObj, SampleBackground),
            Sample: isinstance(parentObj, SampleBackground),
            Container: isinstance(parentObj, Sample)
        }

        # Dict for deciding if the parent object is actually a sibling.
        validSiblings = {
            SampleBackground: isinstance(parentObj, SampleBackground),
            Sample: isinstance(parentObj, Sample),
            Container: isinstance(parentObj, Container)
        }

        if validParents[type(obj)]:
            # We are appending
            if isinstance(obj, SampleBackground):
                # SampleBackground is top level, so the parent is the root.
                parent = QModelIndex()
                setter = self.gudrunFile.sampleBackgrounds.append
            if isinstance(obj, Sample):
                targetIndex = parent.row()-NUM_GUDPY_CORE_OBJECTS
                setter = (
                    self.gudrunFile.sampleBackgrounds[targetIndex]
                    .samples.append
                )
            elif isinstance(obj, Container):
                targetIndex = parent.parent().row()-NUM_GUDPY_CORE_OBJECTS
                setter = (
                    self.gudrunFile.sampleBackgrounds[targetIndex]
                    .samples[parent.row()].containers.append
                )
            # Since we are only inserting one row, start = end.
            start = end = self.rowCount(parent)
            # Begin inserting rows.
            self.beginInsertRows(parent, start, end)
            # Call the setter.
            setter(obj)
            # End inserting rows.
            self.endInsertRows()
            self.dataChanged.emit(
                self.index(start, end, parent),
                self.index(start, end, parent)
            )
        elif validSiblings[type(obj)]:
            # We are inserting.
            if isinstance(obj, SampleBackground):
                index = self.gudrunFile.sampleBackgrounds.index(parentObj)
                # SampleBackground is top level, so the parent is the root.
                parent = QModelIndex()
                setter = self.gudrunFile.sampleBackgrounds.insert
            elif isinstance(obj, Sample):
                targetIndex = parent.parent().row()-NUM_GUDPY_CORE_OBJECTS
                index = (
                    self.gudrunFile.sampleBackgrounds[targetIndex]
                    .samples.index(parentObj)
                )
                setter = (
                    self.gudrunFile.sampleBackgrounds[targetIndex]
                    .samples.insert
                )
            elif isinstance(obj, Container):
                targetIndex = (
                    parent.parent().parent().row()-NUM_GUDPY_CORE_OBJECTS
                )
                index = (
                    self.gudrunFile.sampleBackgrounds[targetIndex].
                    samples[parent.parent().row()].containers.index(parentObj)
                )
                setter = (
                    self.gudrunFile.sampleBackgrounds[targetIndex].
                    samples[parent.parent().row()].containers.insert
                )
            # Again, start = end.
            start = end = self.rowCount(parent.parent())
            # Begin inserting rows.
            self.beginInsertRows(parent.parent(), start, end)
            # Call the setter.
            # index+1 to insert after the current index.
            setter(index+1, obj)
            # End inserting rows.
            self.endInsertRows()
            self.dataChanged.emit(
                self.index(start, end, parent),
                self.index(start, end, parent)
            )

    def removeRow(self, index):
        """
        Remove a row from an index.
        Parameters
        ----------
        index : QModelIndex
            Index to remove.
        """
        # Get the parent index.
        parent = index.parent()
        # Get the object associated with the current index.
        obj = index.internalPointer()
        # Decide on the remove function.
        if isinstance(obj, SampleBackground):
            remove = self.gudrunFile.sampleBackgrounds.remove
        elif isinstance(obj, Sample):
            targetIndex = parent.row()-NUM_GUDPY_CORE_OBJECTS
            remove = (
                self.gudrunFile.sampleBackgrounds[targetIndex].samples.remove
            )
        elif isinstance(obj, Container):
            targetIndex = parent.parent().row()-NUM_GUDPY_CORE_OBJECTS
            remove = (
                self.gudrunFile.sampleBackgrounds[targetIndex]
                .samples[parent.row()].containers.remove
            )
        invalidated = []

        # Remove QPersistendIndexes from the dict that become invalidated
        # by removing the current index.
        if isinstance(obj, Sample):
            for otherObj in self.persistentIndexes.keys():
                if isinstance(otherObj, Sample):
                    if self.findParent(otherObj) == parent.internalPointer():
                        invalidated.append(otherObj)
            for otherObj in self.persistentIndexes.keys():
                if isinstance(otherObj, Container):
                    if self.findParent(otherObj) in invalidated:
                        invalidated.append(otherObj)

        elif isinstance(obj, Container):
            for otherObj in self.persistentIndexes.keys():
                if isinstance(otherObj, Container):
                    if self.findParent(otherObj) == parent.internalPointer():
                        invalidated.append(otherObj)
        for index_ in invalidated:
            del self.persistentIndexes[index_]
        start = end = index.row()
        # Begin inserting rows.
        self.beginRemoveRows(parent, start, end)
        # Pop the object from the dict.
        self.persistentIndexes.pop(obj)
        # Remove the row.
        remove(obj)
        # End inserting rows.
        self.endRemoveRows()
        self.dataChanged.emit(
            self.index(start, end, parent),
            self.index(start, end, parent)
        )


class GudPyTreeView(QTreeView):
    """
    Custom QTreeView View class for GudPy objects. Inherits QTreeView.

    ...

    Attributes
    ----------
    gudrunFile : GudrunFile
        GudrunFile object to build the tree from.
    parent : QWidget
        Parent widget.
    model : QStandardItemModel
        Model to be used for the tree view.
    sibling : QStackedWidget
        Sibling widget to communicate signals and slots to/from.
    contextMenuEnabled : bool
        Is the context tree enabled?
    Methods
    -------
    buildTree(gudrunFile, sibling)
        Builds the tree view from the gudrunFile, pairing
        the modelIndexes with pages of the sibling QStackedWidget.
    makeModel()
        Creates the model for the tree view from the GudrunFile.
    currentChanged(current, previous)
        Slot method for current index being changed in the tree view.
    click(modelIndex)
        Slot method for clicked signal on GudPyTreeView.
    currentObject()
        Returns the object associated with the current index.
    insertRow(obj)
        Inserts an object into the current row in the model.
    removeRow()
        Removes the current index from the model.
    contextMenuEvent(event)
        Creates context menu, for right clicking the table.
    insertSampleBackground_(sampleBackground)
        Inserts a SampleBackground into the GudrunFile.
    insertSample_(sample)
        Inserts a Sample into the GudrunFile.
    insertContainer_(container)
        Inserts a Container into the GudrunFile.
    copy()
        Copies the current object to the clipboard.
    cut_()
        Cuts the current object to the clipboard.
    paste_()
        Pastes the clipboard back into the GudrunFile.
    duplicate()
        Duplicates the current Sample.
    duplicateOnlySample()
        Duplicates the current Sample without any containers.
    setSamplesSelectected(selected)
        Sets sample states to selected.
    selectOnlyThisSample()
        Selects only the current sample, and deselects all others.
    setContextEnabled(state)
        Enable/Disable the context menu.
    """

    def __init__(self, parent):
        """
        Parameters
        ----------
        parent : QWidget
            Parent widget.
        """
        super(GudPyTreeView, self).__init__(parent)
        self.clipboard = None
        self.contextMenuEnabled = True

    def buildTree(self, gudrunFile, parent):
        """
        Constructs all the necessary attributes for the GudPyTreeView object.
        Calls the makeModel method,
        to create a QStandardItemModel for the tree view.
        Parameters
        ----------
        gudrunFile : GudrunFile
            GudrunFile object to create the tree from.
        sibling : QStackedWidget
            Sibling widget to communicate signals and slots to/from.
        """
        self.gudrunFile = gudrunFile
        self.parent = parent
        self.makeModel()
        self.setCurrentIndex(self.model().index(0, 0))
        self.setHeaderHidden(True)
        self.expandToDepth(0)
        self.model().rowsInserted.connect(self._expand)

        self.parent.setTreeActionsEnabled(False)
        self.click(self.model().index(0, 0))

    def makeModel(self):
        """
        Creates the QStandardItemModel to be used for the GudPyTreeView.
        The model is constructed from the GudrunFile.
        """
        self.model_ = GudPyTreeModel(self, self.gudrunFile)
        self.setModel(self.model_)

    def currentChanged(self, current, previous):
        """
        Slot method for current index being changed in the tree view.
        """
        if current.internalPointer():
            self.click(current)
        return super().currentChanged(current, previous)

    def click(self, modelIndex):
        """
        Sets the current index of the sibling QStackedWidget
        to the absolute index of the modelIndex.
        Parameters
        ----------
        modelIndex : QModelIndex
            QModelIndex of the QStandardItem that was clicked in the tree view.
        """
        indexMap = {
            Instrument: (0, None),
            Beam: (1, None),
            Components: (2, None),
            Normalisation: (3, None),
            SampleBackground: (
                4, self.parent.sampleBackgroundSlots.setSampleBackground
            ),
            Sample: (5, self.parent.sampleSlots.setSample),
            Container: (6, self.parent.containerSlots.setContainer)
        }
        self.parent.setTreeActionsEnabled(False)
        type_ = type(modelIndex.internalPointer())
        index, setter = indexMap[type_]
        self.parent.mainWidget.objectStack.setCurrentIndex(index)
        self.parent.updateComponents()
        if setter:
            setter(modelIndex.internalPointer())
        if isinstance(
            modelIndex.internalPointer(),
            (Instrument, Beam, Components, Normalisation, SampleBackground)
        ):
            self.parent.mainWidget.insertSampleBackground.setEnabled(True)
        if isinstance(
            modelIndex.internalPointer(), (SampleBackground, Sample)
        ):
            self.parent.mainWidget.insertSample.setEnabled(True)
        if isinstance(modelIndex.internalPointer(), (Sample, Container)):
            self.parent.mainWidget.insertContainerMenu.setEnabled(True)

        if self.model() and isinstance(self.currentObject(), (
            SampleBackground, Sample, Container)
        ):
            self.parent.mainWidget.copy.setEnabled(True)
            self.parent.mainWidget.cut.setEnabled(True)
            self.parent.mainWidget.delete_.setEnabled(True)

        # If the clipboard can be pasted under the current object.
        # Sample backgrounds default to append if this is not the case.
        if (
            isinstance(self.clipboard, SampleBackground)
            or
            (
                isinstance(self.clipboard, type(self.currentObject()))
                and self.clipboard
            )
            or
            (
                isinstance(self.clipboard, Sample)
                and isinstance(self.currentObject(), SampleBackground)

            )
            or
            (
                isinstance(self.clipboard, Container)
                and isinstance(self.currentObject(), Sample)
            )
            and self.clipboard
        ):
            self.parent.mainWidget.paste.setEnabled(True)

    def currentObject(self):
        """
        Returns the object associated with the current index.
        Returns
        -------
        Instrument | Beam | Normalisation |
        SampleBackground | Sample | Container
            Object associated with the current index.
        """
        return self.currentIndex().internalPointer()

    def insertRow(self, obj):
        """
        Inserts an object into the current row in the model.
        Parameters
        ----------
        obj : SampleBackground | Sample | Container
            Object to be inserted.
        """
        currentIndex = self.currentIndex()
        self.model().insertRow(obj, currentIndex)
        newIndex = self.model().index(
            currentIndex.row()+1, 0,
            self.model().parent(currentIndex)
        )
        self.expandRecursively(newIndex, 0)
        self.parent.updateAllSamples()

    def removeRow(self):
        """
        Removes the current index from the model.
        """
        self.model().removeRow(self.currentIndex())

    def contextMenuEvent(self, event):
        """
        Creates context menu, so that on right clicking the table,
        the user is able to perform menu actions.
        Parameters
        ----------
        event : QMouseEvent
            The event that triggers the context menu.
        """
        # Create the menu
        self.menu = QMenu(self)
        # Actions for insertion
        insertSampleBackground = QAction(
            "Insert Sample Background", self.menu
        )
        insertSampleBackground.triggered.connect(
            self.insertSampleBackground
        )
        insertSampleBackground.setDisabled(True)
        self.menu.addAction(insertSampleBackground)
        insertContainerMenu = QMenu("Insert Container", self.menu)
        insertContainerMenu.setDisabled(True)
        insertContainer = QAction("Default", self.menu)
        insertContainer.triggered.connect(
            self.insertContainer
        )
        insertContainerMenu.addAction(insertContainer)

        actionMap = {}
        insertContainerFromTemplate = QMenu("From Template..", self.menu)
        for name, path in config.containerConfigurations.items():
            action = QAction(f"{name}", insertContainerFromTemplate)
            insertContainerFromTemplate.addAction(action)
            actionMap[action] = path
        insertContainerMenu.addMenu(insertContainerFromTemplate)
        self.menu.addMenu(insertContainerMenu)

        insertSample = QAction("Insert Sample", self.menu)
        insertSample.triggered.connect(
            self.insertSample
        )
        insertSample.setDisabled(True)
        self.menu.addAction(insertSample)

        # Selection actions
        selectAllSamples = QAction("Select All Samples", self.menu)
        selectAllSamples.triggered.connect(
            lambda: self.setSamplesSelected(True)
        )
        selectAllSamples.setDisabled(True)
        self.menu.addAction(selectAllSamples)
        deselectAllSamples = QAction("Deselect All Samples", self.menu)
        deselectAllSamples.triggered.connect(
            lambda: self.setSamplesSelected(False)
        )
        deselectAllSamples.setDisabled(True)
        self.menu.addAction(deselectAllSamples)
        selectOnlyThisSample = QAction("Select Only This Sample", self.menu)
        selectOnlyThisSample.triggered.connect(
            self.selectOnlyThisSample
        )
        selectOnlyThisSample.setDisabled(True)
        self.menu.addAction(selectOnlyThisSample)

        # Copy/cut/paste actions
        copy_ = QAction("Copy", self.menu)
        copy_.triggered.connect(self.copy)
        copy_.setDisabled(True)
        self.menu.addAction(copy_)
        cut = QAction("Cut", self.menu)
        cut.triggered.connect(self.cut)
        cut.setDisabled(True)
        self.menu.addAction(cut)
        paste = QAction("Paste", self.menu)
        paste.setDisabled(True)
        paste.triggered.connect(self.paste)
        self.menu.addAction(paste)

        delete = QAction("Delete", self.menu)
        delete.triggered.connect(self.del_)
        delete.setDisabled(True)
        self.menu.addAction(delete)

        # Duplicate actions
        duplicate = QAction("Duplicate Sample", self.menu)
        duplicate.triggered.connect(self.duplicateSample)
        duplicate.setDisabled(True)
        self.menu.addAction(duplicate)
        duplicateOnlySample = QAction("Duplicate Only Sample", self.menu)
        duplicateOnlySample.triggered.connect(self.duplicateOnlySample)
        duplicateOnlySample.setDisabled(True)
        self.menu.addAction(duplicateOnlySample)

        convertToSample = QAction("Convert to Sample", self.menu)
        convertToSample.triggered.connect(self.convertToSample)
        convertToSample.setDisabled(True)
        self.menu.addAction(convertToSample)

        if self.contextMenuEnabled:
            # If the model has been instantiated,
            if self.model():
                # Enable selecting/deselecting all samples
                selectAllSamples.setEnabled(True)
                deselectAllSamples.setEnabled(True)
                # allow insertion of sample backgrounds.
                if isinstance(self.currentObject(), (Sample, Container)):
                    insertSampleBackground.setText("Append Sample Background")
                insertSampleBackground.setEnabled(True)
            # If the model has been instantiated
            # and the current object type can have siblings
            if self.model() and isinstance(self.currentObject(), (
                SampleBackground, Sample, Container)
            ):
                copy_.setEnabled(True)
                cut.setEnabled(True)
                delete.setEnabled(True)
            # If the clipboard can be pasted under the current object.
            # Sample backgrounds default to append if this is not the case.
            if (
                isinstance(self.clipboard, SampleBackground)
                or
                (
                    isinstance(self.clipboard, type(self.currentObject()))
                    and self.clipboard
                )
                or
                (
                    isinstance(self.clipboard, Sample)
                    and isinstance(self.currentObject(), SampleBackground)

                )
                or
                (
                    isinstance(self.clipboard, Container)
                    and isinstance(self.currentObject(), Sample)
                )
                and self.clipboard
            ):
                paste.setEnabled(True)

            # Enable insertion of samples and containers.
            if isinstance(self.currentObject(), (SampleBackground, Sample)):
                insertSample.setEnabled(True)
            if isinstance(self.currentObject(), (Sample, Container)):
                insertContainerMenu.setEnabled(True)
            # Enable duplication, and selection.
            if isinstance(self.currentObject(), Sample):
                duplicate.setEnabled(True)
                duplicateOnlySample.setEnabled(True)
                selectOnlyThisSample.setEnabled(True)
            if isinstance(self.currentObject(), Container):
                convertToSample.setEnabled(True)

        # Pop up the context menu.
        action = self.menu.exec(QCursor.pos())

        if action in actionMap.keys():
            self.insertContainer(
                container=Container(config_=actionMap[action])
            )

    def insertSampleBackground(self, sampleBackground=None):
        """
        Inserts a SampleBackground into the GudrunFile.
        Inserts it into the tree.
        Parameters
        ----------
        sampleBackground : SampleBackground, optional
            SampleBackground object to insert.
        """
        if not sampleBackground:
            sampleBackground = SampleBackground()
        self.insertRow(sampleBackground)

    def insertSample(self, sample=None):
        """
        Inserts a Sample into the GudrunFile.
        Inserts it into the tree.
        Parameters
        ----------
        sample : Sample, optional
            Sample object to insert.
        """
        if not sample:
            sample = Sample()
            sample.name = "SAMPLE"  # for now, give a default name.
        self.insertRow(sample)

    def insertContainer(self, container=None):
        """
        Inserts a Container into the GudrunFile.
        Inserts it into the tree.
        Parameters
        ----------
        container : Container, optional
            Container object to insert.
        """
        if not container:
            container = Container()
            container.name = "CONTAINER"  # for now, give a default name.
        self.insertRow(container)

    def copy(self):
        """
        Copies the current object to the clipboard.
        """
        self.clipboard = None
        obj = self.currentObject()
        if isinstance(obj, (SampleBackground, Sample, Container)):
            self.clipboard = deepcopy(obj)

    def del_(self):
        """
        Deletes the current object.
        """
        self.removeRow()

    def cut(self):
        """
        Copies the current object to the clipboard, and removes
        the object from the tree.
        """
        self.copy()
        if self.clipboard:
            self.removeRow()

    def paste(self):
        """
        Pastes the contents of the clipboard back into the GudrunFile.
        """
        if isinstance(self.clipboard, SampleBackground):
            self.insertSampleBackground(
                sampleBackground=deepcopy(self.clipboard)
            )
        elif isinstance(self.clipboard, Sample):
            self.insertSample(sample=deepcopy(self.clipboard))
        elif isinstance(self.clipboard, Container):
            self.insertContainer(container=deepcopy(self.clipboard))

    def duplicateSample(self):
        """
        Duplicates the current Sample.
        """
        self.copy()
        self.paste()

    def duplicateOnlySample(self):
        """
        Duplicates the current Sample without any containers.
        """
        self.copy()
        self.clipboard.containers = []
        self.paste()

    def setSamplesSelected(self, selected):
        """
        Sets all samples status to 'selected'.
        Used for selecting / deselecting all samples
        """
        for sampleBackground in self.gudrunFile.sampleBackgrounds:
            for sample in sampleBackground.samples:
                sample.runThisSample = selected
        if not self.parent.widgetsRefreshing:
            self.parent.setModified()

    def selectOnlyThisSample(self):
        """
        Selects only the current sample, and deselects all others.
        """
        self.setSamplesSelected(False)
        if isinstance(self.currentObject(), Sample):
            self.currentObject().runThisSample = True
        if isinstance(self.currentObject(), Container):
            self.model().findParent(self.currentObject()).runThisSample = True
        if not self.parent.widgetsRefreshing:
            self.parent.setModified()

    def setContextEnabled(self, state):
        """
        Disables/Enables the context menu.
        """
        self.contextMenuEnabled = state

    def getSamples(self):
        samples = []
        for i in range(
            NUM_GUDPY_CORE_OBJECTS,
            self.model().rowCount(QModelIndex())
        ):
            sampleBackground = self.model().index(i, 0, QModelIndex())
            for j in range(self.model().rowCount(sampleBackground)):
                sample = self.model().index(
                    j, 0, sampleBackground
                ).internalPointer()
                samples.append(sample)
        return samples

    def getContainers(self):
        containers = []
        for i in range(
            NUM_GUDPY_CORE_OBJECTS,
            self.model().rowCount(QModelIndex())
        ):
            sampleBackground = self.model().index(i, 0, QModelIndex())
            for j in range(self.model().rowCount(sampleBackground)):
                sample = self.model().index(
                    j, 0, sampleBackground
                ).internalPointer()
                containers = [*containers, *sample.containers]
        return containers

    def convertToSample(self):
        container = self.currentObject()
        sample = container.convertToSample()
        self.removeRow()
        self.insertSample(sample)

    def _expand(self, parent, _first, _last):
        self.expand(parent)
