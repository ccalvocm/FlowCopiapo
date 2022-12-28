# -*- coding: utf-8 -*-
"""
Created on Thu Dec 22 12:38:15 2022

@author: ccalvo
"""

import os
import flopy
import pandas as pd
import numpy as np

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
    nper=nper,perlen=perlen,nstp=nstp,steady=steady)
    return None
    
def NWT(mf):
    return flopy.modflow.ModflowNwt(mf)
    
def makeWEL(modelo):
    import geopandas as gpd
    import shapely
    # DAA subterraneos
    pathDAA=r'G:\OneDrive - ciren.cl\2022_Ficha_Atacama\03_Entregas\ICTF_agosto\DAA_Atacama_shacs_val_revE.shp'
    daa=gpd.read_file(pathDAA)
    daaSubt=gpd.GeoDataFrame(daa[daa['Naturaleza']=='Subterranea'])
    daaSubt.geometry=daaSubt.geometry.apply(lambda x: shapely.affinity.translate(x, 
                                    xoff=-modelo.deltaX, yoff=-modelo.deltaY))
    # celdas activas
    modelLimit=gpd.read_file('bas6.shp')
    limit=modelLimit[modelLimit['ibound_1']>0]
    
    # overlay con las celdas activas
    daaSubOverlay=gpd.overlay(daaSubt,limit)
    
def main():
    # pathNam=os.path.join('..','simcopiapo','modflow','run','SIMCOPIAPO.nam')
    pathNam=os.path.join('..','modflow','gv6nwt.nam')
    os.chdir(os.path.dirname(pathNam))
    modelo=model(pathNam,'Copiapo')
    modelo.load()
    modelo.run()
    
    modelo2=modelo.copy()
    makeDIS(modelo2.model)
    NWT(modelo2.model)
    makeOC(modelo2.model)
    
    
# if __name__=='__main__':
#     main()