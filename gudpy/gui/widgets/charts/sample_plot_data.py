from abc import abstractmethod
from PySide6.QtCharts import QLineSeries
from PySide6.QtCore import QPoint, QPointF

from core.gud_file import GudFile


class Point():
    def __init__(self, x, y, err):
        self.x = x
        self.y = y
        self.err = err

    def toQPointF(self):
        return QPointF(self.x, self.y)

    def toQPoint(self):
        return QPoint(self.x, self.y)


class GudPyPlot():
    # mint01 / mdcs01 / mdor01 / mgor01 / dcs
    def __init__(self, path, exists):
        if not exists:
            self.dataSet = None
        else:
            self.dataSet = self.constructDataSet(path)

    @abstractmethod
    def constructDataSet(self, path):
        dataSet = []
        with open(path, "r", encoding="utf-8") as fp:
            for dataLine in fp.readlines():

                # Ignore commented lines.
                if dataLine[0] == "#":
                    continue

                x, y, err, *__ = [float(n) for n in dataLine.split()]
                dataSet.append(Point(x, y, err))
        return dataSet

    def toQPointList(self):
        return [x.toQPoint() for x in self.dataSet] if self.dataSet else None

    def toQPointFList(self):
        return [x.toQPointF() for x in self.dataSet] if self.dataSet else None

    def toLineSeries(self, parent, offsetX, offsetY):
        self.series = QLineSeries(parent)
        points = self.toQPointFList()
        if points:
            points = [
                QPointF(p.x() + offsetX, p.y() + offsetY)
                for p in points
            ]
            self.series.append(points)
        return self.series


class Mint01Plot(GudPyPlot):

    def __init__(self, path, exists):
        self.path = path
        self.XLabel = "Q, 1\u212b"
        self.YLabel = "DCS, barns/sr/atom"
        super().__init__(path, exists)


class Mdcs01Plot(GudPyPlot):

    def __init__(self, path, exists):
        self.path = path
        self.XLabel = "Q, 1\u212b"
        self.YLabel = "DCS, barns/sr/atom"
        super().__init__(path, exists)


class Mdor01Plot(GudPyPlot):

    def __init__(self, path, exists):
        self.path = path
        self.XLabel = "r, \u212b"
        self.YLabel = "G(r)"
        super().__init__(path, exists)


class Mgor01Plot(GudPyPlot):

    def __init__(self, path, exists):
        self.path = path
        self.XLabel = "r, \u212b"
        self.YLabel = "G(r)"
        super().__init__(path, exists)


class DCSLevel:

    def __init__(self, path, exists):
        self.path = path
        if not exists:
            self.dcsLevel = None
            self.data = []
        else:
            self.dcsLevel = self.extractDCSLevel(path)
            self.data = []
        self.visible = True

    @abstractmethod
    def extractDCSLevel(self, path):
        gudFile = GudFile(path)
        return gudFile.expectedDCS

    def extend(self, xAxis):
        if self.dcsLevel:
            self.data = [QPointF(x, self.dcsLevel) for x in xAxis]

    def toLineSeries(self, parent):
        self.series = QLineSeries(parent)
        if self.data:
            self.series.append(self.data)
        return self.series
