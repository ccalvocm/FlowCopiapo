def shp2geojson(shapefile_path, src_epsg=None):
    import geopandas
    from osgeo import ogr, osr
    ds = ogr.Open(shapefile_path)
    if not ds:
        raise IOError('Could not open ' + shapefile_path)
    layer = ds.GetLayer()
    if src_epsg is None:
        sourceprj = layer.GetSpatialRef()
        res = sourceprj.AutoIdentifyEPSG()
        if res != 0:
            import warnings
            warnings.warn('Unable to identify EPSG code for file: ' + shapefile_path + '. Reprojection may not be accurate!')
    else:
        sourceprj = osr.SpatialReference()
        sourceprj.ImportFromEPSG(src_epsg)
    targetprj = osr.SpatialReference()
    targetprj.ImportFromEPSG(4326)
    transform = osr.CoordinateTransformation(sourceprj, targetprj)
    features = []
    import json
    for feat in layer:
        pt = feat.GetGeometryRef()
        if pt is not None:
            pt.Transform(transform)
        json_feat = json.loads(feat.ExportToJson())
        features.append(json_feat)
    return features

def build_shapefile_data(shapefile_path, src_epsg=None, ident_properties=[], metadata_properties=[], metadata_properties_aka=[]):
    has_metadata = len(metadata_properties) > 0
    has_aka = len(metadata_properties) > 0 and len(metadata_properties) == len(metadata_properties_aka)
    data = {}
    identifiers = []
    metadata = []
    features = shp2geojson(shapefile_path, src_epsg)
    valid_features = []
    for feature in features:
        if feature['geometry'] is not None: # Remove features without a geometry
            valid_features.append(feature)
    features = valid_features
    for feature in features:
        if feature['type'] == 'Feature':
            props = feature['properties']
            ident_value = ''
            for att in ident_properties:
                if att in props:
                    att_val = str(props[att])
                    ident_value = ident_value + att_val + ' '
            identifiers.append(ident_value)
            metadata_value = {}
            if has_metadata:
                for i in range(len(metadata_properties)):
                    att = metadata_properties[i]
                    if att in props:
                        att_val = str(props[att])
                        if has_aka:
                            name = metadata_properties_aka[i]
                        else:
                            name = metadata_properties[i]
                        metadata_value[name] = att_val
            else:
                metadata_value['Info'] = ident_value
            metadata.append(metadata_value)
    data['features'] = features
    data['ids'] = identifiers
    data['metadata'] = metadata
    return data