from copy import deepcopy
import os

from core.element import Element
from core.data_files import DataFiles
from core.composition import Composition
from core.enums import FTModes, Geometry, UnitsOfDensity
from core import config
from core.enums import CrossSectionSource
from core.sample import Sample
from core.exception import ParserException
from core.utils import firstword, nthfloat, nthint


class Container:
    """
    Class to represent a Container.

    ...

    Attributes
    ----------
    name : str
        Name of the container.
    periodNumber : int
        Period number for the data files.
    dataFiles : DataFiles
        DataFiles object storing data files belonging to the container.
    composition : Composition
        Composition object storing the atomic composition of the container.
    geometry : Geometry
        Geometry of the container (FLATPLATE / CYLINDRICAL / SameAsBeam).
    upstreamThickness : float
        Upstream thickness of the container - if its geometry is FLATPLATE.
    downstreamThickness : float
        Downstream thickness of the container - if its geometry is FLATPLATE.
    angleOfRotation : float
        Angle of rotation of the container - if its geometry is FLATPLATE.
    sampleWidth : float
        Width of the container - if its geometry is FLATPLATE.
    innerRadius : float
        Inner radius of the container - if its geometry is CYLINDRICAL.
    outerRadius : float
        Outer radius of the container - if its geometry is CYLINDRICAL.
    sampleHeight : float
        Height of the container - if its geometry is CYLINDRICAL.
    density : float
        Density of the container.
    densityUnits : int
        0 = atoms/Angstrom^3, 1 = gm/cm^3
    overallBackgroundFactor : float
        Background factor.
    totalCrossSectionSource : CrossSectionSource
        TABLES / TRANSMISSION monitor / filename
    crossSectionFilename : str
        Filename for total cross section source if applicable.
    scatteringFractionAttenuationCoefficient : tuple(float, float)
        Sample environment scattering fraction and attenuation coefficient,
        per Angstrom
    Methods
    -------
    """
    def __init__(self, config_=None):
        """
        Constructs all the necessary attributes for the Container object.

        Parameters
        ----------
        None
        """
        self.name = ""
        self.periodNumber = 1
        self.dataFiles = DataFiles([], "CONTAINER")
        self.composition = Composition("CONTAINER")
        self.geometry = Geometry.SameAsBeam
        self.upstreamThickness = 0.1
        self.downstreamThickness = 0.1
        self.angleOfRotation = 0.0
        self.sampleWidth = 5.0
        self.innerRadius = 0.0
        self.outerRadius = 0.0
        self.sampleHeight = 0.0
        self.density = 0.0542
        self.densityUnits = UnitsOfDensity.ATOMIC
        self.totalCrossSectionSource = CrossSectionSource.TABLES
        self.crossSectionFilename = ""
        self.tweakFactor = 1.0
        self.scatteringFraction = 0.0
        self.attenuationCoefficient = 0.0

        self.runAsSample = False
        self.topHatW = 0.0
        self.FTMode = FTModes.SUB_AVERAGE
        self.minRadFT = 0.0
        self.maxRadFT = 0.0
        self.grBroadening = 0.
        self.powerForBroadening = 0.0
        self.stepSize = 0.0

        self.yamlignore = {
            "runAsSample",
            "topHatW",
            "FTMode",
            "minRadFT",
            "maxRadFT",
            "grBroadening",
            "powerForBroadening",
            "stepSize",
            "yamlignore"
        }

        if config_:
            self.parseFromConfig(config_)

    def __str__(self):
        """
        Returns the string representation of the Container object.

        Parameters
        ----------
        None

        Returns
        -------
        string : str
            String representation of Container.
        """

        nameLine = (
            f"CONTAINER {self.name}{config.spc5}"
            if self.name != "CONTAINER"
            else
            f"CONTAINER{config.spc5}"
        )

        dataFilesLines = (
            f'{str(self.dataFiles)}\n'
            if len(self.dataFiles) > 0
            else
            ''
            )

        if self.densityUnits == UnitsOfDensity.ATOMIC:
            units = 'atoms/\u212b^3'
            density = -self.density
        elif self.densityUnits == UnitsOfDensity.CHEMICAL:
            units = 'gm/cm^3'
            density = self.density

        compositionSuffix = "" if str(self.composition) == "" else "\n"

        geometryLines = (
            f'{self.upstreamThickness}{config.spc2}'
            f'{self.downstreamThickness}{config.spc5}'
            f'Upstream and downstream thicknesses [cm]\n'
            f'{self.angleOfRotation}{config.spc2}'
            f'{self.sampleWidth}{config.spc5}'
            f'Angle of rotation and sample width (cm)\n'
            if (
                self.geometry == Geometry.SameAsBeam
                and config.geometry == Geometry.FLATPLATE
            )
            or self.geometry == Geometry.FLATPLATE
            else
            f'{self.innerRadius}{config.spc2}{self.outerRadius}{config.spc5}'
            f'Inner and outer radii [cm]\n'
            f'{self.sampleHeight}{config.spc5}'
            f'Sample height (cm)\n'
        )

        densityLine = (
            f'{density}{config.spc5}'
            f'Density {units}?\n'
        )

        crossSectionSource = (
            CrossSectionSource(self.totalCrossSectionSource.value).name
        )
        crossSectionLine = (
            f"{crossSectionSource}{config.spc5}"
            if self.totalCrossSectionSource != CrossSectionSource.FILE
            else
            f"{self.crossSectionFilename}{config.spc5}"
        )

        return (
            f'{nameLine}{{\n\n'
            f'{len(self.dataFiles)}{config.spc2}'
            f'{self.periodNumber}{config.spc5}'
            f'Number of files and period number\n'
            f'{dataFilesLines}'
            f'{str(self.composition)}{compositionSuffix}'
            f'*{config.spc2}0{config.spc2}0{config.spc5}'
            f'* 0 0 to specify end of composition input\n'
            f'SameAsBeam{config.spc5}'
            f'Geometry\n'
            f'{geometryLines}'
            f'{densityLine}'
            f'{crossSectionLine}'
            f'Total cross section source\n'
            f'{self.tweakFactor}{config.spc5}'
            f'Tweak factor\n'
            f'{self.scatteringFraction}{config.spc2}'
            f'{self.attenuationCoefficient}{config.spc5}'
            f'Sample environment scattering fraction '
            f'and attenuation coefficient [per \u212b]\n'
            f'\n}}\n'
        )

    def convertToSample(self):

        sample = Sample()
        sample.name = self.name
        sample.periodNumber = self.periodNumber
        sample.dataFiles = deepcopy(self.dataFiles)
        sample.forceCalculationOfCorrections = True
        sample.composition = deepcopy(self.composition)
        sample.geometry = self.geometry
        sample.upstreamThickness = self.upstreamThickness
        sample.downstreamThickness = self.downstreamThickness
        sample.angleOfRotation = self.angleOfRotation
        sample.sampleWidth = self.sampleWidth
        sample.innerRadius = self.innerRadius
        sample.outerRadius = self.outerRadius
        sample.sampleHeight = self.sampleHeight
        sample.density = self.density
        sample.densityUnits = self.densityUnits
        sample.totalCrossSectionSource = self.totalCrossSectionSource
        sample.sampleTweakFactor = self.tweakFactor
        sample.topHatW = self.topHatW
        sample.FTMode = self.FTMode
        sample.grBroadening = self.grBroadening
        sample.exponentialValues = [(0.0, 1.0)]
        sample.normalisationCorrectionFactor = 1.0
        sample.fileSelfScattering = "*"
        sample.maxRadFT = self.maxRadFT
        sample.minRadFT = self.minRadFT
        sample.powerForBroadening = self.powerForBroadening
        sample.stepSize = self.stepSize
        sample.scatteringFraction = 1.0

        return sample

    def parseFromConfig(self, path):
        if not os.path.exists(path):
            raise ParserException(
                "The path supplied is invalid.\
                 Cannot parse from an invalid path"
            )

        # Decide the encoding
        import chardet
        with open(path, 'rb') as fp:
            encoding = chardet.detect(fp.read())['encoding']

        # Read the input stream into our attribute.
        with open(path, encoding=encoding) as fp:
            self.stream = fp.readlines()

        try:
            # Create a new instance of Container.

            # Extract the name from the lines,
            # and then discard the unnecessary lines.
            self.name = (
                str(self.getNextToken()[:-2]).strip()
                .replace("CONTAINER", "").strip()
            )
            if not self.name:
                self.name = "CONTAINER"
            self.consumeWhitespace()

            # The number of files and period number are both stored
            # on the same line.
            # So we extract the 0th integer for the number of files,
            # and the 1st integer for the period number.
            dataFileInfo = self.getNextToken()
            self.periodNumber = nthint(dataFileInfo, 1)

            # Construct composition
            composition = []
            line = self.getNextToken()
            # Extract the composition.
            # Each element in the composition consists of the first 'word',
            # integer at the second position, and float t the first position,
            # (Atomic Symbol, MassNo, Abundance) in the line.
            # If the marker line is encountered,
            # then the panel has been parsed.
            while "end of composition input" not in line:

                atomicSymbol = firstword(line)
                massNo = nthint(line, 1)
                abundance = nthfloat(line, 2)

                # Create an Element object and append to the composition list.
                composition.append(Element(atomicSymbol, massNo, abundance))
                line = self.getNextToken()
            # Create a Composition object from the dataFiles list constructed.
            self.composition = Composition(
                "Container",
                elements=composition
            )

            # For enumerated attributes,
            # where the member name of the attribute is
            # the first 'word' in the line, and we must get the member,
            # we do this: Enum[memberName].
            self.geometry = Geometry[firstword(self.getNextToken())]

            # Is the geometry FLATPLATE?
            if (
                (
                    self.geometry == Geometry.SameAsBeam
                    and config.geometry == Geometry.FLATPLATE
                )
                    or self.geometry == Geometry.FLATPLATE):
                # If is is FLATPLATE, then extract the upstream and downstream
                # thickness, the angle of rotation and sample width.
                thickness = self.getNextToken()
                self.upstreamThickness = nthfloat(thickness, 0)
                self.downstreamThickness = nthfloat(thickness, 1)

                geometryValues = self.getNextToken()
                self.angleOfRotation = nthfloat(geometryValues, 0)
                self.sampleWidth = nthfloat(geometryValues, 1)
            else:

                # Otherwise, it is CYLINDRICAL,
                # then extract the inner and outer
                # radii and the sample height.
                radii = self.getNextToken()
                self.innerRadius = nthfloat(radii, 0)
                self.outerRadius = nthfloat(radii, 1)
                self.sampleHeight = nthfloat(self.getNextToken(), 0)

            # Extract the density.
            density = nthfloat(self.getNextToken(), 0)

            # Take the absolute value of the density - since it could be -ve.
            self.density = abs(density)

            # Decide on the units of density.
            # -ve density means it is atomic (atoms/A^3)
            # +ve means it is chemical (gm/cm^3)
            self.densityUnits = (
                UnitsOfDensity.ATOMIC if
                density < 0
                else UnitsOfDensity.CHEMICAL
            )
            crossSectionSource = firstword(self.getNextToken())
            if (
                crossSectionSource == "TABLES"
                or crossSectionSource == "TRANSMISSION"
            ):
                self.totalCrossSectionSource = (
                    CrossSectionSource[crossSectionSource]
                )
            else:
                self.totalCrossSectionSource = CrossSectionSource.FILE
                self.crossSectionFilename = crossSectionSource
            self.tweakFactor = nthfloat(self.getNextToken(), 0)

            # Consume whitespace and the closing brace.
            self.consumeUpToDelim("}")

        except Exception as e:
            raise ParserException(
                    "Whilst parsing Container, an exception occured."
                    " The input file is most likely of an incorrect format, "
                    "and some attributes were missing."
            ) from e
