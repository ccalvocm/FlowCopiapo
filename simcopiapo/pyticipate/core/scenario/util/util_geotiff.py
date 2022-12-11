def buildgeotiff(corner_x, corner_y, res_x, res_y, width, height, arr, no_data=-1):
    import gdal
    # Create an in-memory dataset
    drv = gdal.GetDriverByName('MEM')
    ds = drv.Create('', width, height, 1, gdal.GDT_Byte)
    # Write data values
    band = ds.GetRasterBand(1)
    band.WriteArray(arr)
    # Set NoDataValue
    band.SetNoDataValue(no_data)
    # Set Georeference
    upper_left_x = corner_x
    x_resolution = res_x
    x_skew = 0
    upper_left_y = corner_y
    y_skew = 0
    y_resolution = res_y
    geotransform = (upper_left_x, x_resolution, x_skew, upper_left_y, y_skew, y_resolution)
    ds.SetGeoTransform(geotransform)
    # Set Projection
    from osgeo import osr
    spatialRef = osr.SpatialReference()
    spatialRef.ImportFromEPSG(4326)
    ds.SetProjection(spatialRef.ExportToWkt())
    # Create an in-memory file-stream and use it for the GeoTIFF driver
    gdal.FileFromMemBuffer('/vsimem/x.tif', '')
    gdal.GetDriverByName('GTiff').CreateCopy('/vsimem/x.tif', ds)
    # Extract the data-stream from the in-memory file-stream
    f = gdal.VSIFOpenL('/vsimem/x.tif', 'rb')
    gdal.VSIFSeekL(f, 0, 2)
    size = gdal.VSIFTellL(f)
    gdal.VSIFSeekL(f, 0, 0)
    d = gdal.VSIFReadL(1, size, f)
    gdal.VSIFCloseL(f)
    # Delete the in-memory file-stream
    gdal.Unlink('/vsimem/x.tif')
    # Convert the data-stream to a base64 encoded string
    import base64
    b64d = base64.b64encode(d)
    s = b64d.decode('utf-8')
    return {'b64' : s}

def build_geotiff_data(geo, arr, no_data=-1):
    corner_x = geo.lon
    corner_y = geo.lat
    res_x = geo.lonRes
    res_y = geo.latRes
    rows = geo.rows
    cols = geo.cols
    import numpy as np
    values = np.zeros((rows,cols), dtype=np.uint8)
    x = 0
    for i in range(cols):
        for j in range(rows):
            values[i][j] = arr[x]
            x = x + 1
    return buildgeotiff(corner_x, corner_y, res_x, res_y, rows, cols, values, no_data)

def import_geotiff(filepath):
    fi = open(filepath, 'rb')
    d = fi.read()
    import base64
    b64d = base64.b64encode(d)
    return { 'b64' : b64d.decode('utf-8') }