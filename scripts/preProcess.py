# -*- coding: utf-8 -*-
"""
Created on Thu Dec 22 12:38:15 2022

@author: ccalvo
"""

import os
import flopy
import pandas as pd
import numpy as np
import geopandas as gpd


class model(object):
    def __init__(self, pathNam, name):
        self.path = pathNam
        self.name = name
        self.model = None
        self.deltaX = 317600.0
        self.deltaY = 6883200.0

    def load(self):
        self.model = flopy.modflow.Modflow.load(self.path, version="mfnwt",
                                                exe_name="MODFLOW-NWT.exe")

    def check(self):
        print(self.model.check())

    def run(self):
        # self.model.run()
        self.model.write_input()
        success, mfoutput = self.model.run_model('MODFLOW-NWT.exe')
        print(success)

    def copy(self):
        import copy
        return copy.deepcopy(self)


def makeOC(mf):
    """


    Parameters
    ----------
    mf : modflow model
        DESCRIPTION.

    Returns
    -------
    None.

    """
    sps = mf.dis.nper
    spd = {(i, 0): ['save drawdown'] for i in range(0, sps)}
    oc = flopy.modflow.ModflowOc(mf, stress_period_data=spd,
                                 save_every=True, compact=True, unit_number=39)
    return None


def makeDIS(mf):
    """


    Parameters
    ----------
    mf : modflow model
        DESCRIPTION.

    Returns
    -------
    None.

    """

    dis = mf.dis
    nlay = dis.nlay
    nrow = dis.nrow
    ncol = dis.ncol
    delr = dis.delr
    delc = dis.delc
    top = dis.top
    botm = dis.botm
    perlen = list(dis.perlen.array)+list(pd.date_range('2018-01-01', '2022-03-01',
                                                       freq='MS').days_in_month)
    nper = len(perlen)
    nstp = list(np.ones(len(perlen)).astype(int))
    steady = [False if ind > 0 else True for ind, x in enumerate(nstp)]
    mf.start_datetime = '1-1-1993'
    tsmult = [1.2 for x in perlen]
    dis3 = flopy.modflow.ModflowDis(
        mf, nlay, nrow, ncol, delr=delr, delc=delc, top=top, botm=botm,
        nper=nper, perlen=perlen, nstp=nstp, steady=steady, unitnumber=29)
    return None


def NWT(mf):
    return flopy.modflow.ModflowNwt(mf, headtol=0.001, fluxtol=600,
                                    maxiterout=600, thickfact=1e-05, linmeth=2, iprnwt=1, ibotav=1, options='COMPLEX')


def parseDates(df):
    colDate = df.columns[df.columns.str.contains('Fecha')][0]
    df[colDate] = df[colDate].apply(lambda x: pd.to_datetime(x))
    return df, colDate


def getDate():
    return pd.date_range('1993-01-01', '2022-04-01', freq='MS')


def wellsMFP(modelo):
    pathWells = os.path.join('.', 'geodata', 'CaudalTotal_CAS123.shp')
    wellsMFP = gpd.read_file(pathWells)
    wellsMFP.drop_duplicates(inplace=True)


def makeWEL(modelo):
    import geopandas as gpd
    import shapely
    # DAA subterraneos
    pathDAA = r'G:\OneDrive - ciren.cl\2022_Ficha_Atacama\03_Entregas\ICTF_agosto\DAA_Atacama_shacs_val_revH.shp'
    daa = gpd.read_file(pathDAA)
    daaSubt = gpd.GeoDataFrame(daa[daa['Naturaleza'] == 'Subterranea'])
    daaSubCons = daaSubt[daaSubt['Tipo Derec'] != 'No Consuntivo']
    daaSubConsCont = daaSubCons[(daaSubCons['Ejercicio'].str.contains('Cont',
                                                                      na=False)) | (daaSubCons['Ejercicio'].isna())]

    # daa que no caducaron
    daaSubConsCont.loc[daaSubConsCont[daaSubConsCont['Fecha Fin'].notnull()]['Fecha Fin'].index,
                       'Fecha Fin'] = '2022-01-01'
    daaSubConsCont.loc[daaSubConsCont[daaSubConsCont['Fecha Fin'].isnull()]['Fecha Fin'].index,
                       'Fecha Fin'] = '2023-04-01'

    # trasladar el modelo
    daaSubConsCont.geometry = daaSubConsCont.geometry.apply(lambda x: shapely.affinity.translate(x,
                                                                                                 xoff=-modelo.deltaX, yoff=-modelo.deltaY))
    # celdas activas
    modelLimit = gpd.read_file(os.path.join('.', 'geodata', 'bas6.shp'))
    limit = modelLimit[modelLimit['ibound_1'] > 0]

    # overlay con las celdas activas
    daaSubOverlay = gpd.overlay(daaSubConsCont, limit)
    # daaSubOverlay.drop_duplicates('Nombre Sol',inplace=True)

    # convertir a unidades de l/s a m/d
    daaSubOverlay['Caudal Anu'] = daaSubOverlay['Caudal Anu'].str.replace(',',
                                                                          '.').astype(float)
    idx = daaSubOverlay[daaSubOverlay['Unidad D_1'] == 'Lt/min'].index
    daaSubOverlay.loc[idx,
                      'Caudal Anu'] = daaSubOverlay.loc[idx,
                                                        'Caudal Anu'].values/60
    daaSubOverlay['Caudal Anu'] = -86400*1e-3*daaSubOverlay['Caudal Anu']

    daaSubOverlay['COLROW'] = daaSubOverlay.geometry.apply(
        lambda u: str(int(u.x/200))+','+str(530-int(u.y/200)))
    daaSubOverlay, colDate = parseDates(daaSubOverlay)
    # sumar los pozos por celda pero por año de sp
    # daaSubSum=daaSubOverlay.groupby(['COLROW']).agg('sum')['Caudal Anu']

    # crear matriz de coordenadas
    welAll = modelo.model.wel.stress_period_data.array['flux']

    # actualizar el paquete WEL
    # crear diccionario del paquete WEL
    wel_spd = dict.fromkeys(range(modelo.model.dis.nper))

    useFactor = 0.6203315705096603
    # El factor de uso se obtiene al comparar los bombeos de diciembre de 2017
    # y enero de 2018. Viene del hecho que los pozos no bombean el 100% del derecho

    # lista años
    listDates = getDate()
    for stp in wel_spd.keys():
        date = listDates[stp]
        listSpd = []
        if stp > 300:
            # sumar los DAA antes del año del stp
            daaSubSum = daaSubOverlay.copy()
            # filtrar los daa otorgados a la fecha
            daaSubSum = daaSubSum[daaSubSum[colDate].apply(
                lambda x: x) <= date]

            # filtrar los daa caducos
            daaSubSum = daaSubSum[daaSubSum['Fecha Fin'].apply(
                lambda x: pd.to_datetime(x)) > date]

            daaSubSum = daaSubSum.groupby(['COLROW']).agg('sum')[
                'Caudal Anu']*useFactor

            for col in range(np.shape(welAll[0][0])[1]-1):
                for row in range(np.shape(welAll[0][0])[0]-1):
                    try:
                        flux = daaSubSum.loc[str(col)+','+str(row)]
                        listSpd.append([0, row, col, flux])
                    except:
                        continue
        else:
            arrayWel = welAll[stp][0]
            for col in range(np.shape(arrayWel)[1]-1):
                for row in range(np.shape(arrayWel)[0]-1):
                    listSpd.append([0, row, col, arrayWel[row, col]])
        wel_spd[stp] = [x for x in listSpd if x[-1] <= 0]

    wel = flopy.modflow.ModflowWel(modelo.model, stress_period_data=wel_spd)


def processBudget():
    import matplotlib.pyplot as plt
    import flopy
    # zone_file = os.path.join('.', "gv6.zones")
    # zon = read_zbarray(zone_file)
    # nlay, nrow, ncol = zon.shape
    # zb = ZoneBudget('gv6nwt.cbc', zon)
    # dfZB=zb.get_dataframes()
    # names=list(zb.get_record_names())
    # names=[ 'TOTAL_IN','TOTAL_OUT']
    # names=['TOTAL_IN']

    # dateidx1 = dfZB.index[0][0]
    # dateidx2 = dfZB.index[-1][0]
    # zones = ['ZONE_1']
    # dfParsed=dfZB.reset_index()
    # dfZB=dfParsed.pivot_table(index='totim',columns='name',values='ZONE_1',aggfunc='last')
    # # cols=[x for x in dfZB (if 'TOTAL' not in x) | ('ZONE' not in x) | ]
    # dfZB[list(dfZB.columns[dfZB.columns.str.contains('TO_')])]=-dfZB[list(dfZB.columns[dfZB.columns.str.contains('TO_')])]
    # dfZB[cols].plot()

    ruta_lst = os.path.join('.', 'gv6nwt.lst')
    mf_list = flopy.utils.MfListBudget(ruta_lst)
    df_incremental, df_cumulative = mf_list.get_dataframes(
        start_datetime="1993-01-01")
    dfError = df_incremental[['IN-OUT', 'PERCENT_DISCREPANCY']]/86400
    dfError.columns = ['Entradas-salidas', 'Discrepancia del balance (%)']
    fig, ax = plt.subplots(1)
    dfError.plot(ax=ax)
    ax.set_ylim([-1e-3, 1e-3])
    ax.set_ylabel('Entradas-salidas ($m^3/s$)', fontsize=14)
    plt.grid()
    plt.savefig(os.path.join('.', 'out', 'cierreBalanceCopiapo.svg'),
                bbox_inches='tight')

    cols = [x for x in df_incremental.columns if (
        'TOTAL_' not in x) & ('IN-OUT' not in x) & ('PERCENT' not in x)]
    df_incremental[[x for x in cols if '_OUT' in x]] = - \
        df_incremental[[x for x in cols if '_OUT' in x]]
    df_incremental = df_incremental/86400
    df_incremental[cols].plot()
    plt.ylabel('Balance ($m^3/s$)', fontsize=14)
    plt.savefig(os.path.join('.', 'out', 'balanceCopiapo.svg'),
                bbox_inches='tight')
    df_incremental.to_excel(os.path.join('.', 'out', 'balanceCopiapo.xlsx'))
    # incremental, cumulative = mf_list.get_budget()

    # Leer el balance del primer timestep y primer stress period
    data = mf_list.get_data()
    plt.figure()
    plt.bar(data['index'], data['value'])
    plt.xticks(data['index'], data['name'], rotation=45, size=6)
    plt.show()
    plt.ylabel('Balance volumétrico ($m^3$)')
    plt.tight_layout()
    plt.grid()
    plt.savefig(os.path.join('.', 'out', 'balancePromedioCopiapo.svg'),
                bbox_inches='tight')


def processHeads(mf):

    # import the HeadFile reader and read in the head file
    from flopy.utils import HeadFile
    from flopy.export import vtk
    import matplotlib.pyplot as plt
    import flopy.utils.binaryfile as bf

    head_file = os.path.join('.', "gv6nwt.hds")
    hds = HeadFile(head_file)

    hdobj = bf.HeadFile(head_file, precision='single')
    hdobj.list_records()
    rec = hdobj.get_data(kstpkper=(0, 351))
    rec[0][rec[0] == 999] = np.nan
    plt.figure()
    plt.imshow(rec[0], vmin=0, interpolation='nearest')

    # create the vtk object and export heads
    vtkobj = vtk.Vtk(mf)
    otfolder = os.path.join('.', 'out')
    vtk.export_heads(mf, hdsfile=head_file, otfolder=otfolder, kstpkper=(0, 351),
                     point_scalars=True)
    vtkobj.add_heads(hds)
    vtkobj.write(os.path.join('.', 'out', "gv6nwt_head.vtu"))


def damModel():
    # correr modelo de embalse
    from surface_water import dam_operations as dam_ops

    # Run Lautaro Dam operations submodel
    sw_output = dam_ops.run_dam_operation_model('Historico', False, False)
    ModeloEmbalseLautaro_df_6h = sw_output[0]
    LaPuerta_GWSW_df_6h = sw_output[1]

    # Resample submodel from 6-hour to monthly timesteps
    ModeloEmbalseLautaro_df_M = ModeloEmbalseLautaro_df_6h.resample('M').mean()
    LaPuerta_GWSW_df_M = LaPuerta_GWSW_df_6h.resample('M').mean()

    # Apply rolling filter to Q_Afloramiento and then recalculate Q_LaPuerta_sim
    a = LaPuerta_GWSW_df_M.Q_Afloramiento
    b = LaPuerta_GWSW_df_M.Q_Afloramiento.rolling(20, center=True).mean()
    b = b.fillna(b.mean())
    LaPuerta_GWSW_df_M['Q_Afloramiento'] = b
    LaPuerta_GWSW_df_M['Q_LaPuerta_sim'] = LaPuerta_GWSW_df_M['Q_Afloramiento'] + \
        ModeloEmbalseLautaro_df_M['Q_Lautaro_sim'] + \
        ModeloEmbalseLautaro_df_M['Q_Vertedero_sim']

    return ModeloEmbalseLautaro_df_M, LaPuerta_GWSW_df_M


def SWmodel(ModeloEmbalseLautaro_df_M, LaPuerta_GWSW_df_M):
    # definir variables
    prorrata_S2_agricola = 0.1
    prorrata_S3_agricola = 0.60
    prorrata_S4_agricola = 0.60
    prorrata_S5_agricola = 0.6
    prorrata_S6_agricola = 1.0
    # los resultados del ABM se guardan en compilance
    compliance = 0
    ST_swap_89_a_17 = False
    ST_swap_89_a_ACH = False
    ST_swap_89_a_S56_rio = False
    ST_swap_89_a_S5_tubo_rio = False
    ST_swap_89_a_S5_tubo_mar = False
    ST_lautaro2 = False
    ST_entubamiento_canales = False
    ST_recarga_artificial_S3Nantoco = False
    MAR_capacity_S3Nantoco = 0
    ST_recarga_artificial_S4AntesKaukari = False
    MAR_capacity_S4AntesKaukari = 0
    ST_recarga_artificial_S4DespuesKaukari = False
    MAR_capacity_S4DespuesKaukari = 0
    ST_recarga_artificial_S5PiedraColgada = False
    MAR_capacity_S5PiedraColgada = 0

    # correr modelo de embalses
    ModeloEmbalseLautaro_df_M = damModel()[0]
    LaPuerta_GWSW_df_M = damModel()[1]

    # cargar las demandas de agua superficial
    # Load base irrigation demands for JVRC irrigation districts (Sectors 2, 3, 4)
    model_data_dir = 'data'
    irrigationdemands_S234_df = pd.read_pickle(os.path.join(model_data_dir,
                                                            'demandas_riego_S234.pkl'))

    # Load base irrigation demands for GW irrigation districts (Sectors 5, 6)
    irrigationdemands_S56_df = pd.read_pickle(os.path.join(model_data_dir,
                                                           'demandas_riego_S56.pkl'))

    # Load seasonal demand curves
    demandcurves_df = pd.read_pickle(os.path.join(model_data_dir,
                                                  'curvas_demandas_riego.pkl'))

    # correr modelo de aguas superficiales
    from surface_water.swmodel import run_swmodel

    SWMODEL_out_df = run_swmodel(
        prorrata_S2_agricola, prorrata_S3_agricola, prorrata_S4_agricola, prorrata_S5_agricola, prorrata_S6_agricola, compliance,
        ST_swap_89_a_17, ST_swap_89_a_ACH, ST_swap_89_a_S56_rio, ST_swap_89_a_S5_tubo_rio, ST_swap_89_a_S5_tubo_mar,
        ST_lautaro2, ST_entubamiento_canales,
        ST_recarga_artificial_S3Nantoco, MAR_capacity_S3Nantoco, ST_recarga_artificial_S4AntesKaukari, MAR_capacity_S4AntesKaukari,
        ST_recarga_artificial_S4DespuesKaukari, MAR_capacity_S4DespuesKaukari, ST_recarga_artificial_S5PiedraColgada, MAR_capacity_S5PiedraColgada,
        ModeloEmbalseLautaro_df_M, LaPuerta_GWSW_df_M,
        irrigationdemands_S234_df, irrigationdemands_S56_df, demandcurves_df)

    # guardar outputs
    SWMODEL_out_df.to_pickle(os.path.join('outputs', 'SW_model_outputs.pkl'))

    # calcular la recarga a partir del modelo superficial

    # Import GeoDataframes with irrigation, river and city cells
    model_irrcells_gdf = pd.read_pickle(os.path.join(model_data_dir,
                                                     'model_irrcells.pkl'))
    model_rivcells_gdf = pd.read_pickle(os.path.join(model_data_dir,
                                                     'model_rivcells.pkl'))
    model_citcells_gdf = pd.read_pickle(os.path.join(model_data_dir,
                                                     'model_citcells.pkl'))

    # Compute irrigation (infiltration + canal) RCH fluxes per aquifer sector
    RCH_irr_df_1M = SWMODEL_out_df[['RCH_riegoycanales_S2',
                                    'RCH_riegoycanales_S3', 'RCH_riegoycanales_S4', 'Q_perdidariego_P_S5',
                                    'Q_perdidariego_P_S6']]
    RCH_irr_df_3M = RCH_irr_df_1M.resample('Q').mean()
    RCH_irr_df_3M = RCH_irr_df_3M.reset_index().drop(columns='date').head(100)
    RCH_irr_df_3M.columns = ['Sector 2', 'Sector 3', 'Sector 4', 'Sector 5',
                             'Sector 6']
    RCH_irr_df_3M['Sector 5'] = RCH_irr_df_3M['Sector 5'] * \
        (prorrata_S5_agricola + (1 - prorrata_S5_agricola) * (1 - compliance))
    RCH_irr_df_3M['Sector 6'] = RCH_irr_df_3M['Sector 6'] * \
        (prorrata_S6_agricola + (1 - prorrata_S6_agricola) * (1 - compliance))

    # Compute Copiapo River RCH fluxes per aquifer sector
    RCH_riv_df_1M = SWMODEL_out_df[['RCH_rio_S2', 'RCH_rio_S3',
                                    'RCH_rio_S4', 'RCH_rio_S5', 'RCH_rio_S6']]
    RCH_riv_df_3M = RCH_riv_df_1M.resample('Q').mean()
    RCH_riv_df_3M = RCH_riv_df_3M.reset_index().drop(columns='date').head(100)
    RCH_riv_df_3M.columns = ['Sector 2', 'Sector 3', 'Sector 4',
                             'Sector 5', 'Sector 6']

    # Compute Lautaro Dam RCH fluxes
    # model_laucells_gdf = gpd.read_file(os.path.join('geodata', 'Lautaro_recharge.shp'))[['row','column','geometry']]
    # RCH_lau_df_3M = RCH_lau_df_1M.resample('Q').mean().reset_index().drop(columns='date').head(100)
    return SWMODEL_out_df['Q_InfiltracionLautaro'], SWMODEL_out_df


def makeRCH(model_, rchLautaro):

    # crear matriz de coordenadas
    rchAll = model_.rch.rech.array[0][0]
    # identificar las celdas con recarga desde el embalse
    mask = rchAll > 0.054

    # actualizar el paquete RCH
    # actualizar la tasa de recarga por celda
    # match con los srtress periods
    rchByCell = rchLautaro.loc[(
        rchLautaro.index >= '1993-01-01') & (rchLautaro.index <= '2022-03-31')]
    rchByCell = rchByCell.values*1e-03*86400./200./200./len(rchAll[mask])

    # crear diccionario del paquete RCH
    rch_spd = dict.fromkeys(range(model_.dis.nper))

    for stp in range(list(rch_spd.keys())[-1]+1):
        rechStp = model_.rch.rech.array[stp][0]
        if stp > 1:
            rechStp[mask] = rchByCell[stp-1]
        rch_spd[stp] = rechStp.astype(np.float16)[:]
        del rechStp

    rch = flopy.modflow.ModflowRch(model_, nrchop=3, rech=rch_spd)
    return rch


def plotQsim():
    fig, ax = plt.subplots(1)
    LaPuerta_GWSW_df_M['Q_LaPuerta_sim'].plot(ax=ax)
    dfQ.resample('MS').mean().reset_index().plot.scatter(x='index',
                                        y='03431001-7', c='DarkBlue', ax=ax)
    ax.legend(['Caudal simulado río Copiapó en La Puerta', 
               'Caudal observado río Copiapó en La Puerta'])
    ax.grid()
    ax.set_ylabel('Caudal $m^3/s$')
    ax.set_xlabel('')
    fig.savefig(os.path.join('.','outputs','QsimLaPuerta.svg'))

def main():

    # correr modelo de embalse
    os.chdir(os.path.join('..', 'Scripts'))
    ModeloEmbalseLautaro_df_M, LaPuerta_GWSW_df_M = damModel()

    # correr modelo hidrológico
    rchLautaro, df = SWmodel(ModeloEmbalseLautaro_df_M, LaPuerta_GWSW_df_M)

    pathNam = os.path.join('..', 'modflow', 'gv6nwt.nam')
    os.chdir(os.path.dirname(pathNam))
    modelo = model(pathNam, 'Copiapo')
    modelo.load()

    # makeDIS(modelo.model)
    # NWT(modelo.model)
    # makeOC(modelo.model)
    # makeWEL(modelo)

    # incoporar la recarga del modelo superficial
    makeRCH(modelo.model, rchLautaro)

    # correro modelo de aguas subterráneas
    modelo.model.run_model(silent=False)

    processHeads(modelo.model)
    processBudget()


if __name__ == '__main__':
    main()