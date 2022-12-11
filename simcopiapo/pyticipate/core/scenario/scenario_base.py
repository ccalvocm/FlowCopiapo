from copy import deepcopy
from calendar import monthrange
from datetime import timedelta
from abc import ABC, abstractmethod
from io import BytesIO
from uuid import uuid4


# GEOMETRY

class RasterGeometry():

    def __init__(self, lat, lon, cellsize, rows, cols, nullvalue):
        """
        Description of the geometry of a raster layer type.

        Args:
            lat: (numeric) Latitude (EPSG:4326).
            lon: (numeric) Longitude (EPSG:4326).
            cellsize: (int) Square cell height and width (in meters).
            rows: (int) Number of rows in grid.
            cols: (int) Number of columns in grid.
            nullvalue: (numeric) The null value, if a cell has this value, it will not be displayed.
        """
        self.lat = lat
        self.lon = lon
        self.cellsize = cellsize
        self.rows = rows
        self.cols = cols
        self.nullvalue = nullvalue

    def to_dict(self):
        return {
            'lat': self.lat,
            'lon': self.lon,
            'cellsize': self.cellsize,
            'rows': self.rows,
            'cols': self.cols,
            'nullvalue': self.nullvalue
        }

class GeoTIFFGeometryCreated():

    def __init__(self, lat, lon, latRes, lonRes, rows, cols, noData=-999):
        """
        Description of the geometry of a GeoTIFF layer created manually.

        Args:
            lat: (numeric) Latitude (EPSG:4326).
            lon: (numeric) Longitude (EPSG:4326).
            latRes: (numeric) Resolution of grid cells in latitudonal direction (in degrees).
            lonRes: (numeric) Resolution of grid cells in longitudinal direction (in degrees).
            rows: (int) Number of rows in grid.
            cols: (int) Number of columns in grid.
            noData: (numeric) The value which represents no data for a cell.
        """
        self.lat = lat
        self.lon = lon
        self.latRes = latRes
        self.lonRes = lonRes
        self.rows = rows
        self.cols = cols
        self.noData = noData

    def to_dict(self):
        return {
            'lat': self.lat,
            'lon': self.lon,
            'lat-res': self.latRes,
            'lon-res': self.lonRes,
            'rows': self.rows,
            'cols': self.cols,
            'noData': self.noData
        }

class GeoTIFFGeometryImported():

    def __init__(self, noData=-999):
        """
        Description of the geometry of a GeoTIFF layer imported from disk.

        Args:
            noData: (numeric) The value which represents no data for a cell.
        """
        self.noData = noData

    def to_dict(self):
        return {
            'noData': self.noData
        }

# DISPLAY

class NumberDisplay():

    def __init__(self, decimalPlaces=None):
        """
        Description of the display characteristics for numbers.

        Args:
            decimalPlaces: (:obj:`int`, optional) The number of decimal places to display in the user-interface. None means display full precision. Default is None.
        """
        if decimalPlaces is None:
            decimalPlaces = -1
        self.decimalPlaces = decimalPlaces

    def to_dict(self):
        return  {
            'decimal-places': self.decimalPlaces
        }

class ChartDisplay():

    def __init__(self, x_label=None, y_label=None, decimalPlaces=None):
        """
        Description of the display characteristics for generic charts.

        Args:
            x_label: (:obj:`str`, optional) Displays this string on the charts x-axis. Default is None.
            y_label: (:obj:`str`, optional) Displays this string on the charts y-axis. Default is None.
            decimalPlaces: (:obj:`int`, optional) The number of decimal places to display in the user-interface. None means display full precision. Default is None.
        """
        self.x_label = x_label
        self.y_label = y_label
        if decimalPlaces is None:
            decimalPlaces = -1
        self.decimalPlaces = decimalPlaces

    def to_dict(self):
        return {
            'x-label': self.x_label,
            'y-label': self.y_label,
            'decimal-places': self.decimalPlaces
        }

class RasterDisplay():

    def __init__(self, weight=1, opacity=1, fillOpacity=1, lineColor='#0000FF'):
        """
        Description of the display characteristics for a raster.

        Args:
            weight: (integer) Grid line weight. Default is 1.
            opacity: (0.0 to 1.0) Grid line opacity. Default is 1.0.
            fillOpacity: (0.0 to 1.0) Cell opacity. Default is 1.0.
            lineColor: (hex color string) Color of the grid lines. Default is #0000FF (Blue).
        """
        self.weight = weight
        self.opacity = opacity
        self.fillOpacity = fillOpacity
        self.lineColor = lineColor
        self.colorMap = []

    def add_color_rule(self, color, operator, value=None):
        """
        Add a color rule to the display.

        A rule set is built up by adding rules in order to this display object. A rule consists of an operator, color and in most cases a value.
        A typically rule is applied as cell `color` equals `value` `operator` cell value.
        For example: add_color_rule('#FF0000', '>', 10.0) means: where cell values are greater than 10.0 make the color '#FF0000' (Red).
        Possible operators are: '==', '>', '<', '>=', '<=', and 'else'.
        The 'else' operator is typically specified last and acts as a last option for values which are not caught by previous rules.
        As soon as a cell value matches (evaluates to true) a rule, that determines its color. Rules are run in the order in which they are added to this object.

        Args:
            color: (hex color string) Cell color.
            operator: (str) The rule operator.
            value: (:obj:`int`, optional) Default is None.
        """
        if value is None:
            self.colorMap.append({'o': operator, 'c': color})
        else:
            self.colorMap.append({'o': operator, 'v': value, 'c': color})

    def to_dict(self):
        if self.colorMap == []:
            colorMap = [{'o':'else','c':'#000000'}]
        else:
            colorMap = self.colorMap
        return {
            'weight': self.weight,
            'opacity': self.opacity,
            'fillOpacity': self.fillOpacity,
            'line-color': self.lineColor,
            'color_map': colorMap
        }

class PointDisplay():

    def __init__(self, radius=4, weight=1, opacity=1, fillOpacity=1, color='#0000FF', fillColor='#0000FF'):
        """
        Description of the display characteristics for a series of point features.

        Args:
            radius: (int) The radius of the point circles. Default is 4.
            weight: (int) The weight of the point circle lines. Default is 1.
            opacity: (0.0 to 1.0) The opacity of the point circle lines. Default is 1.0.
            fillOpacity: (0.0 to 1.0) The opacity of the point circles. Default is 1.0.
            color: (hex color string) Color of the point circle lines. Default is #0000FF (Blue).
            fillColor: (hex color string) Color of the point circle. Default is #0000FF (Blue).
        """
        self.radius = radius
        self.weight = weight
        self.opacity = opacity
        self.fillOpacity = fillOpacity
        self.color = color
        self.fillColor = fillColor

    def to_dict(self):
        return {
            'radius': self.radius,
            'weight': self.weight,
            'opacity': self.opacity,
            'fillOpacity': self.fillOpacity,
            'color': self.color,
            'fillColor': self.fillColor
        }

class LineDisplay():

    def __init__(self, weight=1, opacity=1, lineColor='#FF0000'):
        """
        Description of the display characteristics for a series of line features.

        Args:
            weight: (int) The weight of the lines. Default is 1.
            opacity: (0.0 to 1.0) The opacity of the lines. Default is 1.0.
            lineColor: (hex color string) The color of the lines. Default is #FF0000 (Red).
        """
        self.weight = weight
        self.opacity = opacity
        self.lineColor = lineColor

    def to_dict(self):
        return {
            'weight': self.weight,
            'opacity': self.opacity,
            'line-color': self.lineColor
        }

class PolygonDisplay():

    def __init__(self, weight=1, opacity=1, fillOpacity=0.5, lineColor='#FFFFFF', fillColor='#00FF00'):
        """
        Description of the display characteristics for a series of polygon features.

        Args:
            weight: (int) The weight of the border lines around the polygons. Default is 1.
            opacity: (0.0 to 1.0) The opacity of the border lines around the polygons. Default is 1.0.
            fillOpacity: (0.0 to 1.0) The opacity of the polygons. Default is 0.5.
            lineColor: (hex color string) The color of the border lines around the polygons. Default is #FFFFFF (White).
            fillColor: (hex color string) The color of the polygons. Default is #00FF00 (Green).
        """
        self.weight = weight
        self.opacity = opacity
        self.fillOpacity = fillOpacity
        self.lineColor = lineColor
        self.fillColor = fillColor

    def to_dict(self):
        return {
            'weight': self.weight,
            'opacity': self.opacity,
            'fillOpacity': self.fillOpacity,
            'line-color': self.lineColor,
            'fill-color': self.fillColor
        }

class ShapefileDisplay():

    def __init__(self, pointDisplay=None, lineDisplay=None, polygonDisplay=None, featureDisplayKey='', customFeatureDisplays={}):
        """
        Description of the display characteristics for shapefile.

        CUSTOM FEATURE DISPLAY:
            To support custom display options, an attribute of the shapefile's features can be used as a key to lookup a custom display setting.
            To do this, set the `featureDisplayKey` to one of the attribute strings from the feature collection in the shapefile.
            Then each feature with that attribute will use the attribute's value for that feature as a key in the `customFeatureDisplays` dictionary to
            determine how it should be displayed.

        Args:
            pointDisplay: (:obj:`PointDisplay`) The display description governing point features. Default is None.
            lineDisplay: (:obj:`LineDisplay`) The display description governing line features. Default is None.
            polygonDisplay: (:obj:`PolygonDisplay`) The display description governing polygon features. Default is None.
            featureDisplayKey: (str) The feature key used for custom feature display.
            customFeatureDisplays: (:dict:(`str`:`PointDisplay`,`LineDisplay`,`PolygonDisplay`) A dictionary of display objected keyed by `featureDisplayKey`.
        """
        if pointDisplay is None:
            pointDisplay = PointDisplay()
        if lineDisplay is None:
            lineDisplay = LineDisplay()
        if polygonDisplay is None:
            polygonDisplay = PolygonDisplay()
        self.point = pointDisplay
        self.line = lineDisplay
        self.polygon = polygonDisplay
        self.featureDisplayKey = featureDisplayKey
        self.customFeatureDisplays = customFeatureDisplays

    def to_dict(self):
        custom_feature_displays = {}
        for cfd in self.customFeatureDisplays:
            custom_feature_displays[cfd] = self.customFeatureDisplays[cfd].to_dict()
            #if contains these keys 
            self._swap_key(custom_feature_displays[cfd], 'line-color', 'color')
            self._swap_key(custom_feature_displays[cfd], 'fill-color', 'fillColor')
        shapefileline = self.line.to_dict()
        self._swap_key(shapefileline, 'line-color', 'color')
        shapefilepolygon = self.polygon.to_dict()
        self._swap_key(shapefilepolygon, 'line-color', 'color')
        self._swap_key(shapefilepolygon, 'fill-color', 'fillColor')
        return {
            'default': {
                'point': self.point.to_dict(),
                'line': shapefileline,
                'polygon': shapefilepolygon
            },
            'custom': {
                'featurekey': self.featureDisplayKey,
                'custom_displays': custom_feature_displays
            }
        }

    def _swap_key(self, d, old, new):
        if old in d:
            d[new] = d[old]
            del d[old]

class GeoTIFFDisplay():

    def __init__(self, scale=['#FFFFFF', '#000000'], opacity=1.0, domain=None):
        """
        Description of the display characteristics for GeoTIFF.

        Args:
            scale: (list(hex color strings),None) Color range from min value to max value for the GeoTIFF. Default is ['#FFFFFF', '#000000'] (White to Black)
            opacity: (0.0 to 1.0) GeoTIFF layer opacity. Default is 1.
            domain: ([float,float], None) Min and max values to use as color scheme extremities.
        """
        self.scale = scale
        self.opacity = opacity
        self.domain = domain

    def to_dict(self):
        return {
            'scale': self.scale,
            'opacity': self.opacity,
            'domain': self.domain
        }

class GaugeDisplay():

    def __init__(self, labels=[], decimal_places=0):
        """
        Description of the display characteristics for a Gauge.

        Args:
            labels: (list(numeric)) A list of numeric values representing the points on the gauge at which a text label will be shown.
            decimal_places: (int) The number of decimal places to draw each of the numeric labels with.
        """
        self.labels = { 'labels': labels, 'decimal_places': decimal_places }
        self.percent = []
        self.zones = []

    def add_percent(self, color, frac):
        """
        Add a percentage color value to the gauge.
        Adding these makes the gauge change color depending on the current value the gauge is showing.

        NB: The percentage color scheme cannot be used in conjunction with the zone scheme.

        Args:
            color: (hex color string) The color to associate with this part of the gauge.
            frac: (numeric) (0.0 - 1.0) The fraction of the gauge to associate a color with.
        """
        self.percent.append([frac, color])

    def add_zone(self, color, min, max):
        """
        Add a distinct color zone to the gauge.
        Adding these creates distinct color bands or zones around the gauge.

        NB: The zone color scheme cannot be used in conjunction with the percentage scheme.

        Args:
            color: (hex color string) The color for this zone.
            min: (numeric) The value at which this zone starts.
            max: (numeric) The value at which this zone ends.
        """
        self.zones.append({ 'color': color, 'min': min, 'max': max })

    def to_dict(self):
        return {
            'labels': self.labels,
            'percent': self.percent,
            'zones': self.zones
        }

# PARAMETER

class ParameterBase(ABC):

    def __init__(self, type, id, name, default=None):
        self.type = type
        self.id = id
        self.name = name
        self.default = default
        self.value = deepcopy(default)

    def get_value(self):
        return self.value

    def set_value(self, value):
        self.value = value

    def reset(self):
        self.value = deepcopy(self.default)

    def get_metadata(self):
        result = deepcopy(self.__dict__)
        result.pop('value')
        return result

# INPUT DEFINITIONS

class InputBaseDef(ParameterBase):

    def __init__(self, type, id, name, grouping, default=None):
        super().__init__(type, id, name, default)
        self.grouping = grouping

class InputNumericDef(InputBaseDef):

    def __init__(self, id, name, grouping, default, step=1, allowPositive=True, allowZero=True, allowNegative=True):
        """
        A numeric input type.

        Datatype to expect when getting input value: numeric

        Args:
            id: (str) A unique identifier for the input. This is the variable you will use to get the input value via the get_input function.
            name: (str) A human-readable name for the input which will be displayed in the user-interface.
            grouping: (str) The grouping ID to which this input belongs.
            default: (numeric) The default value the input will initially take.
            step: (numeric) A valid input must be a multiple of this number, default is 1.
            allowPositive: (bool) A valid input can be a positive number. Defaults to True.
            allowZero: (bool) A valid input can be zero. Defaults to True.
            allowNegative: (bool) A valid input can be a negative number. Defaults to True.
        """
        super().__init__('Numeric', id, name, grouping, default)
        self.step = step
        self.positive = allowPositive
        self.zero = allowZero
        self.negative = allowNegative

class InputBoundNumericDef(InputBaseDef):

    def __init__(self, id, name, grouping, min, max, default, step=1):
        """
        A bound (limited by a min and max) numeric input type.

        Datatype to expect when getting input value: numeric

        Args:
            id: (str) A unique identifier for the input. This is the variable you will use to get the input value via the get_input function.
            name: (str) A human-readable name for the input which will be displayed in the user-interface.
            grouping: (str) The grouping ID to which this input belongs.
            min: (numeric) The lower bound (inclusive) of the valid numeric range.
            max: (numeric) The upper bound (inclusive) of the valid numeric range.
            default: (numeric) The default value the input will initially take.
            step: (numeric) A valid input must be a multiple of this number, default is 1.
        """
        super().__init__('BoundNumeric', id, name, grouping, default)
        self.min = min
        self.max = max
        self.step = step

class InputBooleanDef(InputBaseDef):

    def __init__(self, id, name, grouping, default):
        """
        A boolean input type.

        Datatype to expect when getting input value: bool

        Args:
            id: (str) A unique identifier for the input. This is the variable you will use to get the input value via the get_input function.
            name: (str) A human-readable name for the input which will be displayed in the user-interface.
            grouping: (str) The grouping ID to which this input belongs.
            default: (bool) The default value the input will initially take.
        """
        super().__init__('Boolean', id, name, grouping, default)

class InputSingleSelectionDef(InputBaseDef):

    def __init__(self, id, name, grouping, options, default=None):
        """
        An input type which allows for the selection of a single value from a list of possible values.

        Datatype to expect when getting input value: str

        Args:
            id: (str) A unique identifier for the input. This is the variable you will use to get the input value via the get_input function.
            name: (str) A human-readable name for the input which will be displayed in the user-interface.
            grouping: (str) The grouping ID to which this input belongs.
            options: (List(str)) The list of possible options.
            default: (:obj:`str`, optional) The option which is initially selected. If not specified, the initially selected value will be the first in the list of `options`. Defaults to None.
        """
        if default is None:
            default = options[0]
        super().__init__('SingleSelection', id, name, grouping, default)
        self.options = options

class InputMultiSelectionDef(InputBaseDef):

    def __init__(self, id, name, grouping, options, defaults=[]):
        """
        An input type which allows for the selection of multiple values from a list of possible values.

        Datatype to expect when getting input value: List(str)

        Args:
            id: (str) A unique identifier for the input. This is the variable you will use to get the input value via the get_input function.
            name: (str) A human-readable name for the input which will be displayed in the user-interface.
            grouping: (str) The grouping ID to which this input belongs.
            options: (List(str)) The list of possible options.
            defaults: (List(str), optional) The options which are initially selected. If not specified, no initial values will be specified. Defaults to empty list.
        """
        super().__init__('MultiSelection', id, name, grouping, defaults)
        self.options = options

# OUTPUT DEFINITIONS

class OutputBaseDef(ParameterBase):

    def __init__(self, type, id, name, grouping, default=None):
        super().__init__(type, id, name, default)
        self.grouping = grouping

    def set_value(self, value, dt):
        self.value = value

class OutputNumericDef(OutputBaseDef):

    def __init__(self, id, name, grouping, display=None):
        """
        A numeric output type.

        Datatype to pass when setting output value: numeric OR `OutputSingleVal`

        Args:
            id: (str) A unique identifier for the output. This is the variable you will use to set the output value via the set_output function.
            name: (str) A human-readable name for the output which will be displayed in the user-interface.
            grouping: (str) The grouping ID to which this output belongs.
            display: (:obj:`NumberDisplay`, optional) Display options object. Defaults to None.
        """
        super().__init__('Numeric', id, name, grouping, None)
        if display is None:
            display = NumberDisplay()
        self.display = display.to_dict()

class OutputTimeSeriesDef(OutputBaseDef):

    def __init__(self, id, name, grouping, display=None):
        """
        A time series output type.

        Datatype to pass when setting output value: numeric OR `OutputSingleVal`

        Args:
            id: (str) A unique identifier for the output. This is the variable you will use to set the output value via the set_output function.
            name: (str) A human-readable name for the output which will be displayed in the user-interface.
            grouping: (str) The grouping ID to which this output belongs.
            display: (:obj:`ChartDisplay`, optional) Display options object. Defaults to None.
        """
        super().__init__('TimeSeries', id, name, grouping, [])
        if display is None:
            display = ChartDisplay()
        self.display = display.to_dict()

    def set_value(self, value, dt):
        if isinstance(value, TimseriesBaseVal):
            output = value.get()
            date_lst = output['dates']
            value_lst = output['values']
            for i in range(len(date_lst)):
                d = date_lst[i]
                v = value_lst[i]
                self.value.append({'date':d.strftime('%Y-%m-%d'),'value':v})
        else:
            self.value.append({'date':dt.strftime('%Y-%m-%d'),'value':value})

class OutputTimeSeriesWithIntervalsDef(OutputBaseDef):

    def __init__(self, id, name, grouping, display=None):
        """
        A time series with confidence intervals output type.

        Datatype to pass when setting output value: `OutputTimeSeriesWithIntervalsVal`

        Args:
            id: (str) A unique identifier for the output. This is the variable you will use to set the output value via the set_output function.
            name: (str) A human-readable name for the output which will be displayed in the user-interface.
            grouping: (str) The grouping ID to which this output belongs.
            display: (:obj:`ChartDisplay`, optional) Display options object. Defaults to None.
        """
        super().__init__('TimeSeriesWithIntervals', id, name, grouping, [])
        if display is None:
            display = ChartDisplay()
        self.display = display.to_dict()

    def set_value(self, values, dt):
        if isinstance(values, TimseriesBaseVal):
            output = values.get()
            date_lst = output['dates']
            value_lst = output['values']
            for i in range(len(dates_lst)):
                d = date_lst[i]
                vs = value_lst[i]
                self.value.append({'date':d.strftime('%Y-%m-%d'),'values':vs})
        else:
            self.value.append({'date':dt.strftime('%Y-%m-%d'),'values':values})

class OutputRadarDef(OutputBaseDef):

    def __init__(self, id, name, grouping, variables):
        """
        A radar (or spider) chart output type.

        Datatype to pass when setting output value: `OutputMultipleNumericDatasetVal`

        Args:
            id: (str) A unique identifier for the output. This is the variable you will use to set the output value via the set_output function.
            name: (str) A human-readable name for the output which will be displayed in the user-interface.
            grouping: (str) The grouping ID to which this output belongs.
            variables: (List(str)) The list of variables (or categories) the chart will contain.
        """
        super().__init__('Radar', id, name, grouping, [])
        self.variables = variables

class OutputDoughnutDef(OutputBaseDef):

    def __init__(self, id, name, grouping, variables):
        """
        A doughnut chart output type.

        Datatype to pass when setting output value: `OutputMultipleNumericDatasetVal`

        Args:
            id: (str) A unique identifier for the output. This is the variable you will use to set the output value via the set_output function.
            name: (str) A human-readable name for the output which will be displayed in the user-interface.
            grouping: (str) The grouping ID to which this output belongs.
            variables: (List(str)) The list of variables (or categories) the chart will contain.
        """
        super().__init__('Doughnut', id, name, grouping, [])
        self.variables = variables

class OutputHistogramDef(OutputBaseDef):

    def __init__(self, id, name, grouping, intervals, display=None):
        """
        A histogram chart output type.

        Datatype to pass when setting output value: `OutputMultipleNumericDatasetVal`

        Args:
            id: (str) A unique identifier for the output. This is the variable you will use to set the output value via the set_output function.
            name: (str) A human-readable name for the output which will be displayed in the user-interface.
            grouping: (str) The grouping ID to which this output belongs.
            intervals: (List(str)) The list of intervals (or buckets) the chart will contain.
            display: (:obj:`ChartDisplay`, optional) Display options object. Defaults to None.
        """
        super().__init__('Histogram', id, name, grouping, [])
        self.intervals = intervals
        if display is None:
            display = ChartDisplay()
        self.display = display.to_dict()

class OutputPieDef(OutputBaseDef):

    def __init__(self, id, name, grouping, variables):
        """
        A pie chart output type.

        Datatype to pass when setting output value: `OutputSingleNumericDatasetVal`

        Args:
            id: (str) A unique identifier for the output. This is the variable you will use to set the output value via the set_output function.
            name: (str) A human-readable name for the output which will be displayed in the user-interface.
            grouping: (str) The grouping ID to which this output belongs.
            variables: (List(str)) The list of variables (or categories) the chart will contain.
        """
        super().__init__('Pie', id, name, grouping, [])
        self.variables = variables

class OutputBoxDef(OutputBaseDef):

    def __init__(self, id, name, grouping, variables, display=None):
        """
        A box chart output type.

        Datatype to pass when setting output value: `OutputBoxNumericDatasetVal`

        Args:
            id: (str) A unique identifier for the output. This is the variable you will use to set the output value via the set_output function.
            name: (str) A human-readable name for the output which will be displayed in the user-interface.
            grouping: (str) The grouping ID to which this output belongs.
            variables: (List(str)) The list of variables (or categories) the chart will contain.
            display: (:obj:`ChartDisplay`, optional) Display options object. Defaults to None.
        """
        super().__init__('Box', id, name, grouping, [])
        self.variables = variables
        if display is None:
            display = ChartDisplay()
        self.display = display.to_dict()

class OutputGaugeDef(OutputBaseDef):

    def __init__(self, id, name, grouping, min, max, display=None):
        """
        A gauge chart output type.

        Datatype to pass when setting output value: `OutputSingleVal`

        Args:
            id: (str) A unique identifier for the output. This is the variable you will use to set the output value via the set_output function.
            name: (str) A human-readable name for the output which will be displayed in the user-interface.
            grouping: (str) The grouping ID to which this output belongs.
            min: (numeric) The minimum value the gauge can display.
            max: (numeric) The maximum value the gauge can display.
            display: (:obj:`GaugeDisplay`, optional) Display options object. Defaults to None.
        """
        super().__init__('Gauge', id, name, grouping, None)
        self.min = min
        self.max = max
        if display is None:
            display = GaugeDisplay()
        self.display = display.to_dict()

class OutputImageDef(OutputBaseDef):

    def __init__(self, id, name, grouping):
        """
        An image output type.

        USAGE:
            Before setting an image, it must first be loaded into the system with a unique key through the `set_image` function.

        Datatype to pass when setting output value: `OutputImageVal`

        Args:
            id: (str) A unique identifier for the output. This is the variable you will use to set the output value via the set_output function.
            name: (str) A human-readable name for the output which will be displayed in the user-interface.
            grouping: (str) The grouping ID to which this output belongs.
        """
        super().__init__('Image', id, name, grouping, None)

# COMMON VALUES (OUTPUT AND LAYER DATA)

class TimseriesBaseVal(ABC):

    def __init__(self, dates, values):
        """
        Used to pass part or all of a time series value to an output or layer data variable.

        Args:
            dates: (list(datetime)) List of dates for the values.
            values: (list(numeric) OR list(list(numeric))) List of value for TimeSeries and list of intervals for TimeSeriesWithIntervals.
        """
        self.dates = dates
        self.values = values

    def get(self):
        return {'dates':self.dates, 'values':self.values}

# OUTPUT VALUES

class OutputBaseVal(ABC):

    @abstractmethod
    def get(self):
        pass

class OutputSingleVal(OutputBaseVal):

    def __init__(self, value):
        """
        Used to pass a single numeric value to an output or layer data variable.

        Args:
            value: (numeric) The output or layer data value.
        """
        self.value = value

    def get(self):
        return self.value

class OutputTimeSeriesWithIntervalsVal(OutputBaseVal):

    def __init__(self, upperConfidenceInterval, meanValue, lowerConfidenceInterval):
        """
        Used to pass values with confidence intervals to an output or layer data variable.

        Args:
            upperConfidenceInterval: (numeric) The upper confidence interval.
            meanValue: (numeric) The mean value.
            lowerConfidenceInterval: (numeric) The lower confidence interval.
        """
        self.upperConfidenceInterval = upperConfidenceInterval
        self.meanValue = meanValue
        self.lowerConfidenceInterval = lowerConfidenceInterval

    def get(self):
        return [self.upperConfidenceInterval, self.meanValue, self.lowerConfidenceInterval]

class OutputSingleNumericDatasetVal(OutputBaseVal):

    def __init__(self, values):
        """
        Used to pass a list of numeric values to an output or layer data variable.

        Args:
            values: (list(numeric)) A list of numbers.
        """
        self.value = values

    def get(self):
        return self.value

class OutputMultipleNumericDatasetVal(OutputBaseVal):

    def __init__(self):
        """
        Used to pass a collection of named numeric lists to an output or layer data variable.
        """
        self.value = []

    def append_dataset(self, values, name=None):
        """
        Appends a dataset to the collection.

        Args:
            values: (List(numeric)) A list of numeric values.
            name: (:obj:`str`, optional) A name for the dataset. Not required if only adding one dataset. Default is None.
        """
        self.value.append({'name': name, 'values': values})
        return self

    def get(self):
        return self.value

class BoxNumericDatasetVal():

    def __init__(self, min, q1, median, q3, max, outliers=[]):
        """
        Used to pass a single box plot variables dataset to the `OutputBoxNumericDatasetVal`.

        Args:
            min: (numeric) The minimum value of the set (excluding outliers).
            q1: (numeric) The lower quartile of the set.
            median: (numeric) The median values of the set.
            q3: (numeric) The higher quartile of the set.
            max: (numeric) The maximum value of the set (excluding outliers).
            outliers: (List(numeric)) Outliers greater or less than 3/2 times of lower or upper quartiles.
        """
        self.min = min
        self.q1 = q1
        self.median = median
        self.q3 = q3
        self.max = max
        self.outliers = outliers

class OutputBoxNumericDatasetVal(OutputBaseVal):

    def __init__(self):
        """
        Used to pass a box plot dataset collection to an output or layer data variable.
        """
        self.value = []

    def append_dataset(self, boxDatasets=[], name=None):
        """
        Append a list of single box plot variables (one dataset) to the collection.

        Args:
            boxDatasets: (list(:obj:`BoxNumericDatasetVal`)) List of single box plot variables (one dataset).
            name: (:obj:`str`, optional) A name for the dataset. Not required if only adding one dataset. Default is None.
        """
        values = []
        for d in boxDatasets:
            values.append({'min':d.min,'q1':d.q1,'median':d.median,'q3':d.q3,'max':d.max,'outliers':d.outliers})
        self.value.append({'name':name,'values':values})
        return self

    def get(self):
        return self.value

class OutputImageVal(OutputBaseVal):

    def __init__(self, ident):
        """
        Used to pass an image identifier to an image output or layer data variable.

        Args:
            ident: (str) The image identifier.
        """
        self.ident = ident

    def get(self):
        return self.ident

# LAYER DEFINITIONS

class LayerBaseDef(ParameterBase):

    def __init__(self, type, id, name, description, index, constant, show, display):
        super().__init__(type, id, name)
        self.description = description
        self.index = index
        self.constant = constant
        self.show = show
        self.display = display

    def reset(self):
        if not self.constant:
            super().reset()

    def get_metadata(self):
        result = deepcopy(self.__dict__)
        result.pop('value')
        if hasattr(self, 'geometry'):
            result.pop('geometry')
            result['geometry'] = self.geometry.to_dict()
        result.pop('display')
        if self.display is None:
            result['display'] = None
        elif isinstance(self.display, list):
            l = []
            for d in self.display:
                l.append(d.to_dict())
            result['display'] = l
        else:
            result['display'] = self.display.to_dict()
        return result

class LayerRasterDef(LayerBaseDef):

    def __init__(self, id, name, description, geometry, index, constant, show, display=None):
        """
        A raster layer type.

        Datatype to pass when setting layer value: List(numeric) All cell values top-left, by row, to bottom-right.

        Args:
            id: (str) A unique identifier for the layer. This is the variable you will use to set the layer value via the set_layer function.
            name: (str) A human-readable name for the layer which will be displayed in the user-interface.
            description: (str) A small text description of the layer and what the cell values mean.
            geometry: (:obj:`RasterGeometry`) Geometry options object.
            index: (int) The desired display index of the layer within the layer stack (higher numbers are on top)
            constant: (bool) Is the layer unchanging throughout the model run?
            show: (bool) Is the layer visible by default?
            display: (:obj:`RasterDisplay`, optional) Display options object. Defaults to None.
        """
        if display is None:
            display = RasterDisplay()
        super().__init__('Raster', id, name, description, index, constant, show, display)
        self.geometry = geometry

class LayerPointsDef(LayerBaseDef):

    def __init__(self, id, name, description, index, constant, show, display=None):
        """
        A point feature layer type.

        Datatype to pass when setting layer value: `LayerPointsVal`

        Args:
            id: (str) A unique identifier for the layer. This is the variable you will use to set the layer value via the set_layer function.
            name: (str) A human-readable name for the layer which will be displayed in the user-interface.
            description: (str) A small text description of the layer and what the cell values mean.
            index: (int) The desired display index of the layer within the layer stack (higher numbers are on top)
            constant: (bool) Is the layer unchanging throughout the model run?
            show: (bool) Is the layer visible by default?
            display: (:obj:`PointDisplay`, optional) Display options object. Defaults to None.
        """
        if display is None:
            display = PointDisplay()
        super().__init__('Points', id, name, description, index, constant, show, display)

class LayerLinesDef(LayerBaseDef):

    def __init__(self, id, name, description, index, constant, show, display=None):
        """
        A line feature layer type.

        Datatype to pass when setting layer value: `LayerMultiLineVal`

        Args:
            id: (str) A unique identifier for the layer. This is the variable you will use to set the layer value via the set_layer function.
            name: (str) A human-readable name for the layer which will be displayed in the user-interface.
            description: (str) A small text description of the layer and what the cell values mean.
            index: (int) The desired display index of the layer within the layer stack (higher numbers are on top)
            constant: (bool) Is the layer unchanging throughout the model run?
            show: (bool) Is the layer visible by default?
            display: (:obj:`LineDisplay`, list(:obj:`LineDisplay`), optional) Display options object, or list of them (one for each line). Defaults to None.
        """
        if display is None or display == []:
            display = LineDisplay()
            display = [display]
        else:
            display = [display]
        super().__init__('Lines', id, name, description, index, constant, show, display)

class LayerPolygonsDef(LayerBaseDef):

    def __init__(self, id, name, description, index, constant, show, display=None):
        """
        A polygon feature layer type.

        Datatype to pass when setting layer value: `LayerMultiPolygonVal`

        Args:
            id: (str) A unique identifier for the layer. This is the variable you will use to set the layer value via the set_layer function.
            name: (str) A human-readable name for the layer which will be displayed in the user-interface.
            description: (str) A small text description of the layer and what the cell values mean.
            index: (int) The desired display index of the layer within the layer stack (higher numbers are on top)
            constant: (bool) Is the layer unchanging throughout the model run?
            show: (bool) Is the layer visible by default?
            display: (:obj:`PolygonDisplay`, list(:obj:`PolygonDisplay`), optional) Display options object, or list of them (one for each polygon). Defaults to None.
        """
        if display is None or display == []:
            display = PolygonDisplay()
            display = [display]
        else:
            display = [display]
        super().__init__('Polygons', id, name, description, index, constant, show, display)

class LayerShapefileDef(LayerBaseDef):

    def __init__(self, id, name, description, index, constant, show, display=None):
        """
        A shapefile feature layer type.

        Datatype to pass when setting layer value: `LayerShapefileVal`

        Args:
            id: (str) A unique identifier for the layer. This is the variable you will use to set the layer value via the set_layer function.
            name: (str) A human-readable name for the layer which will be displayed in the user-interface.
            description: (str) A small text description of the layer and what the cell values mean.
            index: (int) The desired display index of the layer within the layer stack (higher numbers are on top)
            constant: (bool) Is the layer unchanging throughout the model run?
            show: (bool) Is the layer visible by default?
            display: (:obj:`ShapefileDisplay`, optional) Display options object. Defaults to None.
        """
        if display is None:
            display = ShapefileDisplay()
        super().__init__('Shapefile', id, name, description, index, constant, show, display)

class LayerGeoTIFFDef(LayerBaseDef):

    def __init__(self, id, name, description, geometry, index, constant, show, display=None):
        """
        A GeofTIFF layer type.

        MODES:
            If building your own GeoTIFF in memory use `geometry` argument type: `GeoTIFFGeometryCreated` and setting value type: `LayerGeoTIFFCreatedVal`
            If importing a GeoTIFF from disk use `geometry` argument type: `GeoTIFFGeometryImported` and setting value type: `LayerGeoTIFFImportedVal`

        Datatype to pass when setting layer value: `LayerGeoTIFFCreatedVal` OR `LayerGeoTIFFImportedVal`

        Args:
            id: (str) A unique identifier for the layer. This is the variable you will use to set the layer value via the set_layer function.
            name: (str) A human-readable name for the layer which will be displayed in the user-interface.
            description: (str) A small text description of the layer and what the cell values mean.
            geometry: (:obj:`GeoTIFFGeometryCreated`,`GeoTIFFGeometryImported`) Geometry options object. See MODES comment.
            index: (int) The desired display index of the layer within the layer stack (higher numbers are on top)
            constant: (bool) Is the layer unchanging throughout the model run?
            show: (bool) Is the layer visible by default?
            display: (:obj:`GeoTIFFDisplay`, optional) Display options object. Defaults to None.
        """
        if display is None:
            display = GeoTIFFDisplay()
        self.geometry = geometry
        super().__init__('GeoTIFF', id, name, description, index, constant, show, display)

class LayerIconsDef(LayerBaseDef):

    def __init__(self, id, name, description, index, constant, show):
        """
        An icon or image layer type.

        USAGE:
            Before setting an icon or image, it must first be loaded into the system with a unique key through the `set_image` function.

        Datatype to pass when setting layer value: `LayerIconVal`

        Args:
            id: (str) A unique identifier for the layer. This is the variable you will use to set the layer value via the set_layer function.
            name: (str) A human-readable name for the layer which will be displayed in the user-interface.
            description: (str) A small text description of the layer and what the cell values mean.
            index: (int) The desired display index of the layer within the layer stack (higher numbers are on top)
            constant: (bool) Is the layer unchanging throughout the model run?
            show: (bool) Is the layer visible by default?
        """
        super().__init__('Icons', id, name, description, index, constant, show, None)

# LAYER VALUES

class LayerBaseVal(ABC):

    @abstractmethod
    def get(self):
        pass

class LayerPointsVal(LayerBaseVal):

    def __init__(self, points=[], names=[]):
        """
        Used to pass a collection of points to a layer variable.

        Args:
            points: (list([lat,lon])) A list of points. A point is a list of two numbers [lat,lon] in EPGS:4326.
            names: (list(str)) A list of point names.
        """
        if len(points) != len(names):
            raise ValueError('Points list and names list must have the same length!')
        self.points = points
        self.names = names

    def add_point(self, point, name):
        """
        Points can be appended to the collection one by one using this function.

        Args:
            point: ([lat,lon]) Point coordinates [lat,lon] in EPGS:4326.
            name: (str) Point name.
        """
        self.points.append(point)
        self.names.append(name)
        return self

    def get(self):
        pts = []
        for pt in self.points:
            pts.append({'lat':pt[0],'lon':pt[1]})
        return {'points': pts, 'metadata': self.names}

class LayerMultiLineVal(LayerBaseVal):

    def __init__(self, lines=[[]], names=[]):
        """
        Used to pass a collection of lines to a layer variable.

        Args:
            lines: (list(list([lat,lon])) A list of lines, each line is a list of points, each point is a list of two numbers [lat,lon] in EPGS:4326.
            names: (list(str)) A list of line names.
        """
        if len(lines) != len(names):
            raise ValueError('Lines list and names list must have the same length!')
        self.lines = lines
        self.names = names

    def add_line(self, line, name):
        """
        Lines can be appended to the collection one by one using this function.

        Args:
            line: (list([lat,lon])) A line, which is a list of points, each point is a list of two numbers [lat,lon] in EPGS:4326.
            name: (str) Line name.
        """
        self.lines.append(line)
        self.names.append(name)
        return self

    def get(self):
        lns = []
        for ln in self.lines:
            pts = []
            for pt in ln:
                pts.append({'lat':pt[0],'lon':pt[1]})
            lns.append(pts)
        return {'lines': lns, 'metadata': self.names}

class LayerMultiPolygonVal(LayerBaseVal):

    def __init__(self, polygons=[[]], names=[]):
        """
        Used to pass a collection of polygons to a layer variable.

        Args:
            polygons: (list(list([lat,lon])) A list of polygons, each polygon is a list of points, each point is a list of two numbers [lat,lon] in EPGS:4326.
            names: (list(str)) A list of polygon names.
        """
        if len(polygons) != len(names):
            raise ValueError('Polygons list and names list must have the same length!')
        self.polygons = polygons
        self.names = names

    def add_line(self, polygon, name):
        """
        Polygons can be appended to the collection one by one using this function.

        Args:
            polygon: (list([lat,lon])) A polygon, which is a list of points, each point is a list of two numbers [lat,lon] in EPGS:4326.
            name: (str) Line name.
        """
        self.polygon.append(polygon)
        self.names.append(name)
        return self

    def get(self):
        pgs = []
        for pg in self.polygons:
            pts = []
            for pt in pg:
                pts.append({'lat':pt[0],'lon':pt[1]})
            pgs.append(pts)
        return {'polygons': pgs, 'metadata': self.names}

class LayerShapefileVal(LayerBaseVal):

    def __init__(self, file_path, src_epsg=None, ident_properties=[], metadata_properties=[], metadata_properties_aka=[]):
        """
        Used to pass a shapefile to a layer variable.

        Args:
            file_path: (str) The file path of the Shapefile to load.
            src_epsg: (:obj:`int`) The EPSG code of the Shapefile (sometimes this is not stored within the file). Default is None.
            ident_properties: (list(`str`)) Feature attributes to be used for unique identification of each feature.
            metadata_properties: (list(`str`)) Feature attributes to be displayed on mouse over.
            metadata_properties_aka: (list(`str`)) Feature attributes user-friendly names.
        """
        self.file_path = file_path
        self.src_epsg = src_epsg
        self.ident_properties = ident_properties
        if len(metadata_properties) > 0 and len(metadata_properties_aka) > 0 and len(metadata_properties) != len(metadata_properties_aka):
            raise ValueError('metadata_properties and metadata_properties_aka lists must be of the same length!')
        self.metadata_properties = metadata_properties
        self.metadata_properties_aka = metadata_properties_aka

        from pyticipate.core.scenario.util.util_shapefile import build_shapefile_data
        self._data = build_shapefile_data(self.file_path, self.src_epsg, self.ident_properties, self.metadata_properties, self.metadata_properties_aka)

    def set(self, data):
        self._data = data

    def get(self):
        return self._data

class LayerGeoTIFFCreatedVal(LayerBaseVal):

    def __init__(self, layer_geometry, arr, no_data=-1):
        """
        Used to pass manually created GeoTIFF data to a layer variable.

        Args:
            layer_geometry: (:obj:`GeoTIFFGeometryCreated`) The layer geometry object.
            arr: (list(numeric)): The list of cell values from top-left, by row, to bottom-right.
            no_data: (numeric) The no data value.
        """
        self.layer_geometry = layer_geometry
        self.arr = arr
        self.no_data = no_data

    def get(self):
        from pyticipate.core.scenario.util.util_geotiff import build_geotiff_data
        return build_geotiff_data(self.layer_geometry, self.arr, self.no_data)

class LayerGeoTIFFImportedVal(LayerBaseVal):

    def __init__(self, file_path):
        """
        Used to pass imported GeoTIFF data to a layer variable.

        Args:
            file_path: (str) The file path of the GeoTIFF to load.
        """
        self.file_path = file_path

        from pyticipate.core.scenario.util.util_geotiff import import_geotiff
        self._data = import_geotiff(self.file_path)

    def set(self, data):
        self._data = data

    def get(self):
        return self._data

class LayerIconVal(LayerBaseVal):

    def __init__(self):
        """
        Used to pass a collection of icons or images to a layer variable.
        """
        self.icons = []

    def add_icon(self, id, height, width, lat, lon, angle=0):
        """
        Icons or images can be appended to the collection one by one using this function.

        Args:
            id: (str) The id string of the image asset to set on the layer.
            height: (numeric) The height in pixels of the image to display.
            width: (numeric) The width in pixels of the image to display.
            lat: (numeric) The latitude at which to display the image on the map in EPGS:4326.
            lon: (numeric) The longitude at which to display the image on the map in EPGS:4326.
            angle: (numeric) The angle by which to rotate the image in degrees. Default is 0.
        """
        self.icons.append({'address':id,'height':height,'width':width,'lat':lat,'lon':lon,'angle':angle})
        return self

    def get(self):
        return {'icons':self.icons}

# LAYER DATA DEFINITIONS

class LayerDataBaseDef(ABC):

    def __init__(self, layer_id, type, ident=None, default=None):
        self.layer_id = layer_id
        self.type = type
        self.ident = ident
        self.default = default
        self.value = deepcopy(default)

    def get_value(self):
        return self.value

    def set_value(self, value, dt):
        self.value = value

    def reset(self):
        self.value = deepcopy(self.default)

    def get_metadata(self):
        result = deepcopy(self.__dict__)
        result.pop('value')
        return result

class LayerDataTimeSeriesDef(LayerDataBaseDef):

    def __init__(self, layer_id, display=None, ident=None):
        """
        A time series layer data type.

        Datatype to pass when setting layer data value: numeric

        Args:
            layer_id: (str) The corresponding id for the layer that this data will be associated with.
            display: (:obj:`ChartDisplay`, optional) Display options object. Defaults to None.
            ident: (str) The identifier which will be used as a key when matching datasets to layer features or grid cells.
        """
        super().__init__(layer_id, 'TimeSeries', ident, {})
        if display is None:
            display = ChartDisplay()
        self.display = display.to_dict()

    def set_value(self, value, dt):
        for key in value:
            if key not in self.value or self.value[key] is None:
                self.value[key] = []
            if isinstance(value[key], TimseriesBaseVal):
                outputs = value[key].get()
                date_lst = outputs['dates']
                value_lst = outputs['values']
                for i in range(len(date_lst)):
                    d = date_lst[i]
                    v = value_lst[i]
                    self.value[key].append({'Date':d.strftime('%Y-%m-%d'),'Value':v})
            else:
                self.value[key].append({'Date':dt.strftime('%Y-%m-%d'),'Value':value[key]})

class LayerDataTimeSeriesWithIntervalsDef(LayerDataBaseDef):

    def __init__(self, layer_id, display=None, ident=None):
        """
        A time series with confidence intervals layer data type.

        Datatype to pass when setting layer data value: `OutputTimeSeriesWithIntervalsVal`

        Args:
            layer_id: (str) The corresponding id for the layer that this data will be associated with.
            display: (:obj:`ChartDisplay`, optional) Display options object. Defaults to None.
            ident: (str) The identifier which will be used as a key when matching datasets to layer features or grid cells.
        """
        super().__init__(layer_id, 'TimeSeriesWithIntervals', ident, {})
        if display is None:
            display = ChartDisplay()
        self.display = display.to_dict()

    def set_value(self, values, dt):
        for key in values:
            if key not in self.value or self.value[key] is None:
                self.value[key] = []
            if isinstance(values[key], TimseriesBaseVal):
                outputs = values[key].get()
                date_lst = outputs['dates']
                value_lst = outputs['values']
                for i in range(len(date_lst)):
                    d = date_lst[i]
                    vs = value_lst[i]
                    self.value[key].append({'Date':d.strftime('%Y-%m-%d'),'Values':vs})
            else:
                self.value[key].append({'Date':dt.strftime('%Y-%m-%d'),'Values':values[key]})

class LayerDataRadarDef(LayerDataBaseDef):

    def __init__(self, layer_id, variables, ident=None):
        """
        A radar (or spider) chart layer data type.

        Datatype to pass when setting layer data value: `OutputMultipleNumericDatasetVal`

        Args:
            layer_id: (str) The corresponding id for the layer that this data will be associated with.
            variables: (List(str)) The list of variables (or categories) the chart will contain.
            ident: (str) The identifier which will be used as a key when matching datasets to layer features or grid cells.
        """
        super().__init__(layer_id, 'Radar', ident, {})
        self.variables = variables

class LayerDataDoughnutDef(LayerDataBaseDef):

    def __init__(self, layer_id, variables, ident=None):
        """
        A doughnut chart layer data type.

        Datatype to pass when setting layer data value: `OutputMultipleNumericDatasetVal`

        Args:
            layer_id: (str) The corresponding id for the layer that this data will be associated with.
            variables: (List(str)) The list of variables (or categories) the chart will contain.
            ident: (str) The identifier which will be used as a key when matching datasets to layer features or grid cells.
        """
        super().__init__(layer_id, 'Doughnut', ident, {})
        self.variables = variables

class LayerDataHistogramDef(LayerDataBaseDef):

    def __init__(self, layer_id, intervals, display=None, ident=None):
        """
        A histogram chart layer data type.

        Datatype to pass when setting layer data value: `OutputMultipleNumericDatasetVal`

        Args:
            layer_id: (str) The corresponding id for the layer that this data will be associated with.
            intervals: (List(str)) The list of intervals (or buckets) the chart will contain.
            display: (:obj:`ChartDisplay`, optional) Display options object. Defaults to None.
            ident: (str) The identifier which will be used as a key when matching datasets to layer features or grid cells.
        """
        super().__init__(layer_id, 'Histogram', ident, {})
        self.intervals = intervals
        if display is None:
            display = ChartDisplay()
        self.display = display.to_dict()

class LayerDataPieDef(LayerDataBaseDef):

    def __init__(self, layer_id, variables, ident=None):
        """
        A pie chart layer data type.

        Datatype to pass when setting layer data value: `OutputSingleNumericDatasetVal`

        Args:
            layer_id: (str) The corresponding id for the layer that this data will be associated with.
            variables: (List(str)) The list of variables (or categories) the chart will contain.
            ident: (str) The identifier which will be used as a key when matching datasets to layer features or grid cells.
        """
        super().__init__(layer_id, 'Pie', ident, {})
        self.variables = variables

class LayerDataBoxDef(LayerDataBaseDef):

    def __init__(self, layer_id, variables, display=None, ident=None):
        """
        A box chart layer data type.

        Datatype to pass when setting layer data value: `OutputBoxNumericDatasetVal`

        Args:
            layer_id: (str) The corresponding id for the layer that this data will be associated with.
            variables: (List(str)) The list of variables (or categories) the chart will contain.
            display: (:obj:`ChartDisplay`, optional) Display options object. Defaults to None.
            ident: (str) The identifier which will be used as a key when matching datasets to layer features or grid cells.
        """
        super().__init__(layer_id, 'Box', ident, {})
        self.variables = variables
        if display is None:
            display = ChartDisplay()
        self.display = display.to_dict()

class LayerDataGaugeDef(LayerDataBaseDef):

    def __init__(self, layer_id, min, max, display=None, ident=None):
        """
        A gauge chart layer data type.

        Datatype to pass when setting layer data value: `OutputSingleVal`

        Args:
            layer_id: (str) The corresponding id for the layer that this data will be associated with.
            min: (numeric) The minimum value the gauge can display.
            max: (numeric) The maximum value the gauge can display.
            display: (:obj:`GaugeDisplay`, optional) Display options object. Defaults to None.
            ident: (str) The identifier which will be used as a key when matching datasets to layer features or grid cells.
        """
        super().__init__(layer_id, 'Gauge', ident, {})
        self.min = min
        self.max = max
        if display is None:
            display = GaugeDisplay()
        self.display = display.to_dict()

class LayerDataImageDef(LayerDataBaseDef):

    def __init__(self, layer_id, ident=None):
        """
        An image layer data type.

        Datatype to pass when setting layer data value: `OutputImageVal`

        Args:
            layer_id: (str) The corresponding id for the layer that this data will be associated with.
            ident: (str) The identifier which will be used as a key when matching datasets to layer features or grid cells.
        """
        super().__init__(layer_id, 'Image', ident, {})

# SIMULATION

class TimeStep():

    DAILY_NAME = 'Daily'
    MONTHLY_NAME = 'Monthly'
    ANNUAL_NAME = 'Annual'

    END_OF_MONTH_DAY = 25

    def __init__(self, name, is_regular, step=None):
        self.name = name
        self.is_regular = is_regular
        self.step = step

    def Parse(str):
        if str == TimeStep.DAILY_NAME:
            return TimeStep(str, True, timedelta(1))
        elif str == TimeStep.MONTHLY_NAME:
            return TimeStep(str, False)
        elif str == TimeStep.ANNUAL_NAME:
            return TimeStep(str, False)
        else:
            raise ValueError('Unknown TimeStep "'+str+'"')

    def Add(self, dt, num_steps=1):
        now = dt
        for i in range(num_steps):
            if self.is_regular:
                now = now + self.step
            else:
                if self.name == TimeStep.MONTHLY_NAME:
                    day = dt.day
                    month = dt.month
                    year = dt.year
                    days_in_current_month = monthrange(year, month)[1]
                    month = month + 1
                    if month == 13:
                        month = 1
                        year = year + 1
                    days_in_next_month = monthrange(year, month)[1]
                    if day >= TimeStep.END_OF_MONTH_DAY:
                        days_from_end_of_month = days_in_current_month - day
                        day = days_in_next_month - days_from_end_of_month
                    now = dt.replace(day=day,month=month,year=year)
                elif self.name == TimeStep.ANNUAL_NAME:
                    now = dt.replace(year=dt.year+1)
        return now

    def Subtract(self, dt, num_steps=1):
        now = dt
        for i in range(num_steps):
            if self.is_regular:
                now = now - self.step
            else:
                if self.name == TimeStep.MONTHLY_NAME:
                    day = dt.day
                    month = dt.month
                    year = dt.year
                    days_in_current_month = monthrange(year, month)[1]
                    month = month - 1
                    if month == 0:
                        month = 12
                        year = year - 1
                    days_in_previous_month = monthrange(year, month)[1]
                    if day >= TimeStep.END_OF_MONTH_DAY:
                        days_from_end_of_month = days_in_current_month - day
                        day = days_in_previous_month - days_from_end_of_month
                    now = dt.replace(day=day,month=month,year=year)
                elif self.name == TimeStep.ANNUAL_NAME:
                    now = dt.replace(year=dt.year-1)
        return now

    def __str__(self):
        return self.name

class GroupDef():

    def __init__(self, id, name, parent_id=None, info_html_filepath=None):
        self.id = id
        self.name = name
        self.parent_id = parent_id
        self.info_html = self._read_html(info_html_filepath)
        self._subgroups = {}
        self.index = -1

    def _add_subgroup(self, group_def):
        id = group_def.id
        group_def.index = len(self._subgroups)
        self._subgroups[id] = group_def

    def _read_html(self, filepath):
        if filepath is None:
            return ''
        fi = open(filepath, 'r')
        contents = fi.read()
        fi.close()
        return contents

    def serialize(self):
        result = {}
        result['id'] = self.id
        result['name'] = self.name
        result['info_html'] = self.info_html
        subs = []
        for key in self._subgroups:
            subs.append(self._subgroups[key].serialize())
        result['subgroups'] = subs
        result['index'] = self.index
        return result

class Grouping():

    def __init__(self):
        self.INPUT_KEY = 'input'
        self.OUTPUT_KEY = 'output'
        self._groupings = {}
        self._groupings[self.INPUT_KEY] = {}
        self._groupings[self.OUTPUT_KEY] = {}

    def _key(self, input):
        if input:
            return self.INPUT_KEY
        else:
            return self.OUTPUT_KEY

    def _find_group(self, id):
        def search(dct, id):
            if id in dct:
                return dct[id]
            for key in dct:
                return search(dct[key]._subgroups, id)
        group_def = search(self._groupings[self.INPUT_KEY], id)
        if group_def is None:
            group_def = search(self._groupings[self.OUTPUT_KEY], id)
        return group_def

    def add_group(self, group_def, input):
        key = self._key(input)
        if group_def.parent_id is not None:
            parent_def = self._find_group(group_def.parent_id)
            parent_def._add_subgroup(group_def)
        else:
            id = group_def.id
            group_def.index = len(self._groupings[key])
            self._groupings[key][id] = group_def

    def get_groups(self, input):
        key = self._key(input)
        return self._groupings[key]

    def serialize(self, input):
        groups = self.get_groups(input)
        result = []
        for key in groups:
            result.append(groups[key].serialize())
        return result

class ScenarioBase(ABC):

    def __init__(self, start, end, timestep = TimeStep.Parse('Daily'), multi_step=False):
        self._start = start
        self._end = end
        self._timestep = timestep
        self._now = self._timestep.Subtract(self._start)
        self._multi_step = multi_step
        self._initialised = False
        self._constant_layers_loaded = False

        self._groupings = Grouping()

        self._inputs = {}
        self._outputs = {}
        self._layers = {}
        self._layer_data = {}

        self._input_values = {}
        self._output_values = {}
        self._layer_values = {}
        self._layer_data_values = {}

        self._images = {}
        self._image_ids_to_remove = []
        self._points_of_interest = {}

        self._run_status = {'percentage': 0.0, 'description': ''}

    # ***** SCENARIO FUNCTIONS FOR USE BY CHILD CLASSES *****

    # DEFINITION STAGE

    def add_group(self, group_def, input):
        """
        Add a Group to the model. The Group can be added to either the Input or Output category.

        Args:
            group_def: (:obj) The group definition object.
            input: (bool) True if for Input category, False if for Output category.
        """
        self._groupings.add_group(group_def, input)

    def add_input(self, input_def):
        """
        Add an Input variable to the model.
        """
        input_def.index = len(self._inputs)
        id = input_def.id
        if id in self._inputs:
            raise ValueError('An input with this ID has already been declared! ID: "' + str(id) + '"')
        self._inputs[id] = input_def
        self._input_values[id] = None

    def add_output(self, output_def):
        """
        Add an Output variable to the model.
        """
        output_def.index = len(self._outputs)
        id = output_def.id
        if id in self._outputs:
            raise ValueError('An output with this ID has already been declared! ID: "' + str(id) + '"')
        self._outputs[id] = output_def
        self._output_values[id] = None

    def add_layer(self, layer_def):
        """
        Add a Layer to the model.
        """
        layer_def.index = len(self._layers)
        id = layer_def.id
        if id in self._layers:
            raise ValueError('A layer with this ID has already been declared! ID: "' + str(id) + '"')
        self._layers[id] = layer_def
        self._layer_values[id] = None

    def add_layer_data(self, layer_data_def):
        """
        Add a Layer Data to the model.
        """
        layer_id = layer_data_def.layer_id
        self._layers[layer_id].click = {'type':layer_data_def.type,'ident':layer_data_def.ident}
        self._layer_data[layer_id] = layer_data_def
        self._layer_data_values[layer_id] = dict()

    def add_point_of_interest(self, id, name, lat, lon, zoom):
        """
        Add a Point of Interest to the model.

        Args:
            id: (str) The point of interest ID.
            name: (str) Name of the point of interest.
            lat: (float) The latitude (EPSG:4326) of the point of interest.
            lon: (float) The longitude (EPSG:4326) of the point of interest.
            zoom: (int) The zoom level of the map (Leaflet zoom number).
        """
        self._points_of_interest[id] = { 'name': name, 'lat': lat, 'lon': lon, 'zoom': zoom }

    # RUN STAGE

    def get_input(self, id):
        """
        Get an input value using its ID.
        The return type is dependent on the InputDef originally used to define the Input.

        Args:
            id: (str) The Input ID.
        """
        return self._inputs[id].get_value()

    def set_output(self, id, value):
        """
        Set an output value using its ID.

        Args:
            id: (str) The Output ID.
            value: (:obj) The ouput value to set. Its type is dependent on the OutputDef originally used to define the Output.
        """
        if isinstance(value, OutputBaseVal):
            self._output_values[id] = value.get()
        else:
            self._output_values[id] = value        

    def get_layer_geometry(self, id):
        """
        Get a layers' geometry (if it has one).

        Args:
            id: (str) The Layer ID.
        """
        return self._layers[id].geometry

    def set_layer(self, id, value):
        """
        Set a layer value using its ID.

        Args:
            id: (str) The Layer ID.
            value: (:obj) The layer value to set. Its type is dependent on the LayerDef originally used to define the Layer.
        """
        if isinstance(value, LayerBaseVal):
            self._layer_values[id] = value.get()
        else:
            self._layer_values[id] = value

    def get_unique_image_id(self):
        """
        Get a new, unique image ID.
        """
        while True:
            ident = str(uuid4())
            if ident not in self._images:
                return ident

    def set_image(self, id, buffer, mimetype, autoremove=False):
        """
        Used to add an icon or image asset to the system for later use by the Image Output or Icon Layer.

        NOTE:
            The browser will cache images, so if the image is to be updated during the simulation,
            a new unique identifier will need to be used each time the image is updated.
            The autoremove flag is designed to help with this by removing old images after each timestep.

        Args:
            id: (str) A unique identifier to refer to the image/icon when applying the image/icon to an output/layer.
            buffer: (:obj:`bytearray`) Raw binary data of the image/icon.
            mimetype: (str) The MIME type of the image/icon.
            autoremove: (bool) If True, remove image/icon from system for next timestep.
        """
        self._images[id] = {'buffer':buffer,'mimetype':mimetype}
        if autoremove:
            self._image_ids_to_remove.append(id)

    def set_layer_data(self, id, key, value):
        """
        Set a layer data value using its ID.

        Args:
            id: (str) The Layer ID to assign this layer data value too.
            key: (str) The value which maps the data value to the correct cell or feature on the layer.
            value: (:obj) The layer data value to set. Its type is dependent on the LayerDataDef originally used to define the Layer Data.
        """
        if isinstance(value, OutputBaseVal):
            self._layer_data_values[id][key] = value.get()
        else:
            self._layer_data_values[id][key] = value

    def set_run_status(self, percentage, description):
        self._run_status['percentage'] = percentage
        self._run_status['description'] = description

    # SIMULATION FUNCTIONS

    @abstractmethod
    def metadata(self):
        pass

    def load_constant_layers(self):
        pass

    def initialise(self):
        pass

    def reset(self):
        pass

    def run_time_step(self, dt):
        pass

    def run_time_steps(self, dt, steps):
        pass

    def export_results(self):
        result = {}
        result['filename'] = 'report.txt'
        result['type'] = 'application/txt'
        result['data'] = ''
        return result

    @abstractmethod
    def dispose(self):
        pass

    # ***** PRIVATE FUNCTIONS *****

    def get_metadata(self):
        md = self.metadata()
        md['timestep'] = str(self._timestep)
        return md

    def initialise_scenario(self):
        if not self._initialised:
            self.initialise()
            self._initialised = True

    def remove_images(self):
        for id in self._image_ids_to_remove:
            self._images.pop(id)
        self._image_ids_to_remove.clear()

    # ***** FUNCTIONS USED BY WEB API *****

    def get_run_status(self):
        return self._run_status

    def reset_scenario(self):
        self.remove_images()
        self.initialise_scenario()
        for id in self._layers:
            self._layers[id].reset()
        for id in self._outputs:
            self._outputs[id].reset()
        for id in self._layer_data:
            self._layer_data[id].reset()
        self._now = self._timestep.Subtract(self._start)
        self.reset()

    def run_scenario_time_step(self, num_timesteps=1):
        self.remove_images()
        self.initialise_scenario()
        if self._multi_step:
            steps = 0
            for i in range(num_timesteps):
                if self._now < self._end:
                    self._now = self._timestep.Add(self._now)
                    steps = steps + 1
            for id in self._inputs:
                self._input_values[id] = self._inputs[id].get_value()
            self.run_time_steps(self._now, steps)
            for id in self._outputs:
                self._outputs[id].set_value(self._output_values[id], self._now)
            for id in self._layers:
                self._layers[id].set_value(self._layer_values[id])
            for id in self._layer_data:
                self._layer_data[id].set_value(self._layer_data_values[id], self._now)
        else:
            for i in range(num_timesteps):
                if self._now < self._end:
                    self._now = self._timestep.Add(self._now)
                    for id in self._inputs:
                        self._input_values[id] = self._inputs[id].get_value()
                    self.run_time_step(self._now)
                    for id in self._outputs:
                        self._outputs[id].set_value(self._output_values[id], self._now)
                    for id in self._layers:
                        self._layers[id].set_value(self._layer_values[id])
                    for id in self._layer_data:
                        self._layer_data[id].set_value(self._layer_data_values[id], self._now)

    def get_scenario_metadata(self):
        return self.get_metadata()

    def get_simulation_dates(self):
        dates = {}
        dates['start'] = self._start.strftime('%Y-%m-%d')
        dates['end'] = self._end.strftime('%Y-%m-%d')
        return dates

    def get_current_date(self):
        if self._now < self._start:
            return self._start.strftime('%Y-%m-%d')
        else:
            return self._now.strftime('%Y-%m-%d')

    def get_groupings(self, input):
        return self._groupings.serialize(input)

    def get_all_inputs_metadata(self):
        input_metadata = []
        for id in self._inputs:
            input_metadata.append(self._inputs[id].get_metadata())
        return input_metadata
        
    def get_all_outputs_metadata(self):
        output_metadata = []
        for id in self._outputs:
            output_metadata.append(self._outputs[id].get_metadata())
        return output_metadata
    
    def get_all_layers_metadata(self):
        layer_metadata = []
        for id in self._layers:
            layer_metadata.append(self._layers[id].get_metadata())
        return layer_metadata

    def get_layer_data_metadata(self, layer_id, type, ident):
        if layer_id in self._layer_data:
            return self._layer_data[layer_id].get_metadata()
        else:
            return None

    def set_all_inputs_values(self, inputs):
        for id in inputs:
            self._inputs[id].set_value(inputs[id])

    def get_all_inputs_values(self):
        inputs = {}
        for id in self._inputs:
            inputs[id] = self.get_input(id)
        return inputs

    def get_all_outputs_values(self):
        outputs = {}
        for id in self._outputs:
            outputs[id] = self._outputs[id].get_value()
        return outputs

    def get_all_layers_values(self):
        if not self._constant_layers_loaded:
            self.load_constant_layers()
            for id in self._layers:
                self._layers[id].set_value(self._layer_values[id])
            self._constant_layers_loaded = True
        layers = {}
        for id in self._layers:
            layers[id] = self._layers[id].get_value()
        return layers

    def get_layer_data(self, layer_id, type, ident):
        ident_type = ident['type']
        ident_value = ident['value']
        if ident_type == 'tuple':
            ident_value = (int(ident_value.split(',')[0][1:]),int(ident_value.split(',')[1][:-1]))
        data = self._layer_data[layer_id].get_value()
        if ident_value in data:
            return data[ident_value]
        else:
            return []

    def get_image_data(self, id):
        if id in self._images:
            buffer = self._images[id]['buffer']
            mimetype = self._images[id]['mimetype']
            return (BytesIO(buffer), mimetype)
        else:
            raise ValueError('No image with id "' + id + '" found.')

    def get_points_of_interest(self):
        return self._points_of_interest

    def path_for_resource(self, resource):
        return ''