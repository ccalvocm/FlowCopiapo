import core.scenario.scenario_base as sb

import os
import datetime as dt
import random as rand


class Scenario(sb.ScenarioBase):

    def dispose(self):
        pass

    def path_for_resource(self, resource):
        return os.path.join(self.root_dir, 'static', resource)

    def __init__(self, working_dir):
        self.root_dir = os.path.abspath(os.path.dirname(__file__))
        # Define temporal characteristics
        start = dt.datetime(2017,1,1)
        end = dt.datetime(2017,12,31)
        timestep = sb.TimeStep.Parse('Daily')
        super().__init__(start, end, timestep)
        # Define Groupings
        super().add_group(sb.GroupDef('input_group_1','Group 1',None,os.path.join(self.root_dir,'static/html/group_1.html')),True)
        super().add_group(sb.GroupDef('input_group_1_subgroup_a','Sub Group A','input_group_1',os.path.join(self.root_dir,'static/html/subgroup_a.html')),True)
        super().add_group(sb.GroupDef('input_group_1_subgroup_b','Sub Group B','input_group_1',os.path.join(self.root_dir,'static/html/subgroup_b.html')),True)
        super().add_group(sb.GroupDef('input_group_2','Group 2'),True)
        super().add_group(sb.GroupDef('input_group_3','Group 3'),True)
        super().add_group(sb.GroupDef('output_group_1','Group 1',None,os.path.join(self.root_dir,'static/html/group_1_out.html')),False)
        super().add_group(sb.GroupDef('output_group_1_subgroup_a','Sub Group A','output_group_1',os.path.join(self.root_dir,'static/html/subgroup_a_out.html')),True)
        super().add_group(sb.GroupDef('output_group_1_subgroup_b','Sub Group B','output_group_1',os.path.join(self.root_dir,'static/html/subgroup_b_out.html')),True)
        super().add_group(sb.GroupDef('output_group_2','Group 2'),False)
        super().add_group(sb.GroupDef('output_group_3','Group 3'),False)
        super().add_group(sb.GroupDef('output_group_4','Group 4'),False)
        super().add_group(sb.GroupDef('output_group_5','Group 5'),False)
        # Define Inputs
        super().add_input(sb.InputBoundNumericDef('input_1','Input 1','input_group_1_subgroup_a',1,10,3,1))
        super().add_input(sb.InputBoundNumericDef('input_2','Input 2','input_group_1_subgroup_b',1,10,8.2,0.1))
        super().add_input(sb.InputSingleSelectionDef('input_3','Input 3','input_group_2',['Add','Subtract','Multiply','Divide'],'Add'))
        super().add_input(sb.InputMultiSelectionDef('input_4','Input 4','input_group_2',['Alpha','Beta','Gamma','Delta','Epsilon'],['Delta']))
        super().add_input(sb.InputBooleanDef('input_5','Input 5','input_group_3',True))
        super().add_input(sb.InputNumericDef('input_6','Input 6','input_group_3',34.54,0.01,True,True,False))
        # Define Outputs
        sample_axis_display = sb.ChartDisplay(x_label='x-label', y_label='y-label', decimalPlaces=3)
        super().add_output(sb.OutputTimeSeriesDef('output_1','Output 1','output_group_1_subgroup_a',sample_axis_display))
        super().add_output(sb.OutputTimeSeriesDef('output_2','Output 2','output_group_1_subgroup_b',sample_axis_display))
        super().add_output(sb.OutputNumericDef('output_3','Output 3','output_group_2',sb.NumberDisplay(3)))
        super().add_output(sb.OutputRadarDef('output_4','Output 4','output_group_2',['Alpha','Beta','Gamma','Delta','Epsilon']))
        super().add_output(sb.OutputTimeSeriesWithIntervalsDef('output_5','Output 5','output_group_2',sample_axis_display))
        super().add_output(sb.OutputDoughnutDef('output_6','Output 6','output_group_2',['Alpha','Beta','Gamma','Delta','Epsilon']))
        super().add_output(sb.OutputHistogramDef('output_7','Output 7','output_group_3',['Alpha','Beta','Gamma','Delta','Epsilon'],sample_axis_display))
        super().add_output(sb.OutputPieDef('output_8','Output 8','output_group_3',['Alpha','Beta','Gamma','Delta','Epsilon']))
        super().add_output(sb.OutputBoxDef('output_9','Output 9','output_group_4',['Alpha','Beta','Gamma'],sample_axis_display))
        sample_gauge_display = sb.GaugeDisplay([0, 33, 67, 100])
        sample_gauge_display.add_zone('#61FF33',0,33)
        sample_gauge_display.add_zone('#FFAC33',33,67)
        sample_gauge_display.add_zone('#FF4233',67,100)
        super().add_output(sb.OutputGaugeDef('output_10','Output 10','output_group_4',0,100,sample_gauge_display))
        super().add_output(sb.OutputImageDef('output_11','Output 11','output_group_5'))
        # Define Layers
        # Layer 1 (Raster)
        layer_1_geometry = sb.RasterGeometry(lat=-27.38, lon=-70.45, cellsize=1000, rows=100, cols=100, nullvalue=0)
        layer_1_display = sb.RasterDisplay(weight=1, opacity=0.1, fillOpacity=0.4, lineColor='#ffffff')
        layer_1_display.add_color_rule('#ff0000', '==', 1)
        layer_1_display.add_color_rule('#00ff00', '==', 2)
        layer_1_display.add_color_rule('#0000ff', '==', 3)
        layer_1_display.add_color_rule('#000000', 'else')
        super().add_layer(sb.LayerRasterDef('layer_1','Random Raster','Sample Layer Description',layer_1_geometry,1,False,True,layer_1_display))
        # Layer 2 (Points)
        layer_2_display = sb.PointDisplay(radius=4, weight=1, opacity=1, fillOpacity=0.8, color='#ff00ff', fillColor='#ff00ff')
        super().add_layer(sb.LayerPointsDef('layer_2','Example Points','Sample Layer Description',2,True,True,layer_2_display))
        # Layer 3 (Lines)
        layer_3_display = sb.LineDisplay(weight=1, opacity=1, lineColor='#00ff00')
        super().add_layer(sb.LayerLinesDef('layer_3','Example Lines','Sample Layer Description',3,True,True,layer_3_display))
        # Layer 4 (Polygons)
        layer_4_display = sb.PolygonDisplay(weight=1, opacity=1, fillOpacity=0.5, lineColor='#000000', fillColor='#0000ff')
        super().add_layer(sb.LayerPolygonsDef('layer_4','Example Polygon','Sample Layer Description',4,True,True,layer_4_display))
        # Layer 5 (Shapefile)
        layer_5_custom_display = { }
        layer_5_custom_display[1] = sb.PointDisplay(4, 1, 1, 1, '#3232FF', '#3232FF')
        layer_5_custom_display[2] = sb.PointDisplay(6, 1, 1, 1, '#6666FF', '#6666FF')
        layer_5_custom_display[3] = sb.PointDisplay(8, 1, 1, 1, '#9999FF', '#9999FF')
        layer_5_custom_display[4] = sb.PointDisplay(10, 1, 1, 1, '#CCCCFF', '#CCCCFF')
        layer_5_display = sb.ShapefileDisplay(None, None, None, 'SIZE', layer_5_custom_display)
        self.add_layer(sb.LayerShapefileDef('layer_5','Bocatomas Principales','Sample Layer Description',5,False,True,layer_5_display))
        # Layer 6 (Shapefile)
        super().add_layer(sb.LayerShapefileDef('layer_6','Canālis','Sample Layer Description',6,True,True))
        # Layer 7 (Shapefile)
        layer_7_display = sb.ShapefileDisplay(polygonDisplay=sb.PolygonDisplay(weight=1, opacity=1, fillOpacity=0.5, lineColor='#001100', fillColor='#00ff00'))
        super().add_layer(sb.LayerShapefileDef('layer_7','Ciudad de Copiapó','Sample Layer Description',7,True,True,layer_7_display))
        # Layer 8 (GeoTIFF)
        layer_8_geometry = sb.GeoTIFFGeometryCreated(lat=-27.38, lon=-70.45, latRes=-0.0044, lonRes=0.005, rows=100, cols=100, noData=-999)
        layer_8_display = sb.GeoTIFFDisplay(scale=['#733BCC','#0099FF'], opacity=0.5)
        super().add_layer(sb.LayerGeoTIFFDef('layer_8','Random GeoTIFF','Sample Layer Description',layer_8_geometry,8,False,True,layer_8_display))
        # Layer 9 (Icons)
        super().add_layer(sb.LayerIconsDef('layer_9','Icons','Sample Layer Description',9,False,True))
        # Add layer data time series to layer_2 (type Points)
        super().add_layer_data(sb.LayerDataTimeSeriesDef('layer_2',sample_axis_display,'value'))
        # Add layer data time series to layer_8 (type GeoTIFF)
        super().add_layer_data(sb.LayerDataTimeSeriesDef('layer_8',sample_axis_display))
        # Add layer data gauge to layer_3 (type Lines)
        super().add_layer_data(sb.LayerDataGaugeDef('layer_3', 0, 100, None, 'value'))
        # Add layer data histogram to layer_4 (type Polygon)
        super().add_layer_data(sb.LayerDataHistogramDef('layer_4',['Alpha','Beta','Gamma','Delta','Epsilon'],sample_axis_display,'value'))
        # Add points of interest
        self.add_point_of_interest('POI1', 'P.O.I. Alpha', -27.50, -70.00, 10)
        self.add_point_of_interest('POI2', 'P.O.I. Beta', -27.65, -70.09, 8)
        # Declare variables
        self.sum = 0
        self.count = 0

    def metadata(self):
        metadata = {}
        metadata['id'] = 'demonstration'
        metadata['name'] = 'Demonstration'
        metadata['description'] = 'A demo scenario for developing the website.'
        metadata['view'] = { 'lat': -27.77, 'lon': -69.94, 'zoom': 10 }
        metadata['timesteps'] = { 'steps': [1,2,5,10], 'unit_singular': 'day', 'unit_plural': 'days' }
        metadata['exports_results'] = False
        return metadata

    def load_constant_layers(self):
        with open(os.path.join(self.root_dir, 'data/001.png'), 'rb') as fl:
            self.set_image('001', fl.read(), 'image/png')
        with open(os.path.join(self.root_dir, 'data/002.png'), 'rb') as fl:
            self.set_image('002', fl.read(), 'image/png')
        # Set values for constant layers
        self.set_layer('layer_2', sb.LayerPointsVal([[-27.90,-70.25],[-27.94,-70.30],[-28.05,-70.20]], ['Point 1','Point 2','Point 3']))
        self.set_layer('layer_3', sb.LayerMultiLineVal([[[-27.90,-70.25],[-27.94,-70.30],[-28.05,-70.20]]], ['Line 1']))
        self.set_layer('layer_4', sb.LayerMultiPolygonVal([[[-27.90,-70.25],[-27.94,-70.30],[-28.05,-70.20]]], ['Polygon 1']))
        shapefile_src_epsg = 24879
        self.set_layer('layer_6', sb.LayerShapefileVal(os.path.join(self.root_dir, 'data/Canales.shp'),shapefile_src_epsg,['Nombre']))
        self.set_layer('layer_7', sb.LayerShapefileVal(os.path.join(self.root_dir, 'data/Ciudad_de_Copiapo.shp'),shapefile_src_epsg,['NOM_REG']))

    def reset(self):
        self.sum = 0
        self.count = 0

    def initialise(self):
        shapefile_src_epsg = 24879
        self.layer_5_val = sb.LayerShapefileVal(os.path.join(self.root_dir,'data/Bocatomas_principales.shp'),shapefile_src_epsg,['COD_BCTOMA'])

    def run_time_step(self, dt):
        rand.seed()
        # Compute output_1, output_2, output_3, output_4, output_5, output_6, output_7, output_8 and output_9
        input_1 = self.get_input('input_1')
        input_2 = self.get_input('input_2')
        self.sum += (input_1 + input_2)
        self.count += 1
        self.set_output('output_1', input_1)
        action = self.get_input('input_3')
        if action == 'Add':
            self.set_output('output_2', input_1 + input_2)
        elif action == 'Subtract':
            self.set_output('output_2', input_1 - input_2)
        elif action == 'Multiply':
            self.set_output('output_2', input_1 * input_2)
        else:
            self.set_output('output_2', input_1 / float(input_2))
        self.set_output('output_3', self.sum / float(self.count))
        output_4_values = list(range(1,6))
        for i in range(5):
            output_4_values[i] = rand.randint(0, 9)
        self.set_output('output_4', sb.OutputMultipleNumericDatasetVal().append_dataset(output_4_values))
        mean = rand.randint(3, 6)
        int1 = mean + rand.randint(1, 3)
        int2 = mean - rand.randint(1, 3)
        self.set_output('output_5', sb.OutputTimeSeriesWithIntervalsVal(int1, mean, int2))
        output_6_values = list(range(1,6))
        for i in range(5):
            output_6_values[i] = rand.randint(0, 9)
        self.set_output('output_6', sb.OutputMultipleNumericDatasetVal().append_dataset(output_6_values))
        output_7_values = list(range(1,6))
        for i in range(5):
            output_7_values[i] = rand.randint(0, 9)
        self.set_output('output_7', sb.OutputMultipleNumericDatasetVal().append_dataset(output_7_values))
        output_8_values = list(range(1,6))
        for i in range(5):
            output_8_values[i] = rand.randint(0, 9)
        self.set_output('output_8', sb.OutputSingleNumericDatasetVal(output_8_values))
        output_9_values = list()
        for i in range(3):
            min = rand.randint(0,2)
            q1 = min + rand.randint(1,3)
            median = q1 + rand.randint(1,3)
            q3 = median + rand.randint(1,3)
            max = q3 + rand.randint(1,3)
            output_9_values.append(sb.BoxNumericDatasetVal(min, q1, median, q3, max, []))
        self.set_output('output_9', sb.OutputBoxNumericDatasetVal().append_dataset(output_9_values))
        output_10_value = rand.randint(0, 100)
        self.set_output('output_10', sb.OutputSingleVal(output_10_value))
        output_11_ident = self.get_unique_image_id()
        with open(os.path.join(self.root_dir, 'data/example.svg'), 'rb') as fl:
            self.set_image(output_11_ident, fl.read(), 'image/svg+xml', True)
        self.set_output('output_11', sb.OutputImageVal(output_11_ident))
        # Compute layer_1 (Raster)
        raster_layer_geo = self.get_layer_geometry('layer_1')
        raster_rows = raster_layer_geo.rows
        raster_cols = raster_layer_geo.cols
        raster_values = []
        for i in range(raster_rows*raster_cols):
            raster_values.append(rand.randint(1, 3))
        self.set_layer('layer_1', raster_values)
        # Edit layer_5 (Shapefile)
        layer_5_data = self.layer_5_val.get()
        for i in range(len(layer_5_data['features'])):
            layer_5_data['features'][i]['properties']['SIZE'] = rand.randint(1, 4)
        self.layer_5_val.set(layer_5_data)#See if needed (by val or by ref)
        self.set_layer('layer_5', self.layer_5_val)
        # Compute layer_8 (GeoTIFF)
        geotiff_layer_geo = self.get_layer_geometry('layer_8')
        geotiff_rows = geotiff_layer_geo.rows
        geotiff_cols = geotiff_layer_geo.cols
        geotiff_values = []
        for i in range(geotiff_rows*geotiff_cols):
            geotiff_values.append(rand.randint(1, 255))
        self.set_layer('layer_8', sb.LayerGeoTIFFCreatedVal(geotiff_layer_geo, geotiff_values, -999))
        # Compute feature values for layer 2 points
        self.set_layer_data('layer_2', 'Point 1', rand.randint(0, 9))
        self.set_layer_data('layer_2', 'Point 2', rand.randint(0, 9))
        self.set_layer_data('layer_2', 'Point 3', rand.randint(0, 9))
        # Compute cell values for layer_8 cells
        self.set_layer_data('layer_8', (0,0), rand.randint(0, 9))
        # Compute feature values for layer 3 line
        self.set_layer_data('layer_3', 'Line 1', sb.OutputSingleVal(output_10_value))
        # Compute feature values for layer 4 polygon
        layer_data_4_values = list(range(1,6))
        for i in range(5):
            layer_data_4_values[i] = rand.randint(0, 9)
        self.set_layer_data('layer_4', 'Polygon 1', sb.OutputMultipleNumericDatasetVal().append_dataset(layer_data_4_values))
        # Icons
        if dt.day % 2 == 0:
            image_id = '001'
        else:
            image_id = '002'
        self.set_layer('layer_9', sb.LayerIconVal().add_icon(image_id, 20, 20, -27.77, -69.94).add_icon(image_id, 20, 20, -27.80, -69.90))
