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
    def __init__(self,pathNam,name):
        self.path=pathNam
        self.name=name
        self.model=None
        self.deltaX=317600.0
        self.deltaY=6883200.0
    def load(self):
        self.model=flopy.modflow.Modflow.load(self.path,version="mfnwt",
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
    sps=mf.dis.nper
    spd={(i,0) : ['save drawdown'] for i in range(0,sps)}
    oc = flopy.modflow.ModflowOc(mf, stress_period_data=spd,
                             save_every=True, compact=True,unit_number=39)
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

    dis=mf.dis
    nlay=dis.nlay
    nrow=dis.nrow
    ncol=dis.ncol
    delr=dis.delr
    delc=dis.delc
    top=dis.top
    botm=dis.botm
    perlen=list(dis.perlen.array)+list(pd.date_range('2018-01-01','2022-03-01',freq='MS').days_in_month)
    nper=len(perlen)
    nstp=list(np.ones(len(perlen)).astype(int))
    steady=[False if ind>0 else True for ind,x in enumerate(nstp)]
    mf.start_datetime='1-1-1993'
    tsmult=[1.2 for x in perlen]
    dis3 = flopy.modflow.ModflowDis(
    mf, nlay, nrow, ncol, delr=delr, delc=delc, top=top, botm=botm,
    nper=nper,perlen=perlen,nstp=nstp,steady=steady,unitnumber=29)
    return None
    
def NWT(mf):
    return flopy.modflow.ModflowNwt(mf,headtol=0.001,fluxtol=600,
maxiterout=600,thickfact=1e-05,linmeth=2,iprnwt=1,ibotav=1,options='COMPLEX')
    
def makeWEL(modelo):
    import geopandas as gpd
    import shapely
    # DAA subterraneos
    pathDAA=r'G:\OneDrive - ciren.cl\2022_Ficha_Atacama\03_Entregas\ICTF_agosto\DAA_Atacama_shacs_val_revE.shp'
    daa=gpd.read_file(pathDAA)
    daaSubt=gpd.GeoDataFrame(daa[daa['Naturaleza']=='Subterranea'])
    daaSubCons=daaSubt[daaSubt['Tipo Derec']!='No Consuntivo']
    daaSubConsCont=daaSubCons[(daaSubCons['Ejercicio'].str.contains('Cont')) | (daaSubCons['Ejercicio'].isna())]
    
    daaSubConsCont.geometry=daaSubConsCont.geometry.apply(lambda x: shapely.affinity.translate(x, 
                                    xoff=-modelo.deltaX, yoff=-modelo.deltaY))
    # celdas activas
    modelLimit=gpd.read_file('bas6.shp')
    limit=modelLimit[modelLimit['ibound_1']>0]
    
    # overlay con las celdas activas
    daaSubOverlay=gpd.overlay(daaSubConsCont,limit)
    daaSubOverlay.drop_duplicates('Nombre Sol',inplace=True)
    
    # convertir a unidades de l/s a m/d
    daaSubOverlay['Caudal Anu']=daaSubOverlay['Caudal Anu'].str.replace(',',
'.').astype(float)
    idx=daaSubOverlay[daaSubOverlay['Unidad D_1']=='Lt/min'].index
    daaSubOverlay.loc[idx,'Caudal Anu']=daaSubOverlay.loc[idx,'Caudal Anu'].values/60
    daaSubOverlay['Caudal Anu']=-86400*1e-3*daaSubOverlay['Caudal Anu']
    
    
    daaSubOverlay['COLROW']=daaSubOverlay.geometry.apply(lambda u: str(int(u.x/200))+','+str(530-int(u.y/200)))
    daaSubSum=daaSubOverlay.groupby(['COLROW']).agg('sum')['Caudal Anu']
    
    # crear matriz de coordenadas
    welAll=modelo.model.wel.stress_period_data.array['flux']
    
    # actualizar el paquete WEL
    # crear diccionario del paquete WEL
    wel_spd=dict.fromkeys(range(modelo.model.dis.nper))
    
    for stp in wel_spd.keys():
        listSpd=[]
        if stp>300:
            for col in range(np.shape(welAll[0][0])[1]-1):
                for row in range(np.shape(welAll[0][0])[0]-1):
                    try:
                        flux=daaSubSum.loc[str(col)+','+str(row)]
                        listSpd.append([0,row,col,flux]) 
                    except:
                        continue
        else:
            arrayWel=welAll[stp][0]
            for col in range(np.shape(arrayWel)[1]-1):
                for row in range(np.shape(arrayWel)[0]-1):
                    listSpd.append([0,row,col,arrayWel[row,col]])  
        wel_spd[stp]=[x for x in listSpd if x[-1]<=0]
        
    wel = flopy.modflow.ModflowWel(modelo.model,stress_period_data=wel_spd)

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
    
    ruta_lst=os.path.join('.','gv6nwt.lst')
    mf_list =  flopy.utils.MfListBudget(ruta_lst)
    df_incremental, df_cumulative = mf_list.get_dataframes(start_datetime="1993-01-01")
    cols=[x for x in df_incremental.columns if ('TOTAL_' not in x) & ('IN-OUT' not in x) & ('PERCENT' not in x)]
    df_incremental[[x for x in cols if '_OUT' in x]]=-df_incremental[[x for x in cols if '_OUT' in x]]
    df_incremental=df_incremental/86400
    df_incremental[cols].plot()
    plt.ylabel('Balance ($m^3/s$)')
    plt.savefig(os.path.join('.','out','balanceCopiapo.svg'),
                bbox_inches='tight')    
    # incremental, cumulative = mf_list.get_budget()
    
    #Leer el balance del primer timestep y primer stress period
    data = mf_list.get_data()
    plt.bar(data['index'], data['value'])
    plt.xticks(data['index'], data['name'], rotation=45, size=6)
    plt.show()
    plt.ylabel('Balance volumétrico ($m^3$)')
    plt.tight_layout()
    plt.grid()

def processHeads(mf):
    
    
    # import the HeadFile reader and read in the head file
    from flopy.utils import HeadFile
    from flopy.export import vtk
    import matplotlib.pyplot as plt
    head_file = os.path.join('.', "gv6nwt.hds")
    hds = HeadFile(head_file)
    
    import flopy.utils.binaryfile as bf
    hdobj = bf.HeadFile(head_file, precision='single')
    hdobj.list_records()
    rec = hdobj.get_data(kstpkper=(0, 50))
    rec[0][rec[0]==999]=np.nan
    plt.figure()
    plt.imshow(rec[0],vmin=0,interpolation='nearest')
    
    # create the vtk object and export heads
    vtkobj = vtk.Vtk(mf)
    otfolder=os.path.join('.','out')
    vtk.export_heads(mf, hdsfile=head_file, otfolder=otfolder,kstpkper=(0,0))  
    # vtkobj.add_heads(hds)
    # vtkobj.write(os.path.join('.','out', "gv6nwt_head.vtu"))


def main():
    # pathNam=os.path.join('..','simcopiapo','modflow','run','SIMCOPIAPO.nam')
    pathNam=os.path.join('..','modflow','gv6nwt.nam')
    os.chdir(os.path.dirname(pathNam))
    modelo=model(pathNam,'Copiapo')
    modelo.load()
    
    makeDIS(modelo.model)
    NWT(modelo.model)
    makeOC(modelo.model)
    makeWEL(modelo)
    modelo.run()

    
# if __name__=='__main__':
#     main()