# -*- coding: utf-8 -*-
"""
Created on Thu Dec 22 12:38:15 2022

@author: ccalvo
"""

import os
import flopy
import pandas as pd

class model(object):
    def __init__(self,pathNam,name):
        self.path=pathNam
        self.name=name
        self.model=None
    def load(self):
        self.model=flopy.modflow.Modflow.load(self.path,version="mfnwt",
 exe_name="MODFLOW-NWT.exe")
        sps=len(self.model.oc.stress_period_data)
        spd={(i,0) : ['save drawdown'] for i in range(0,sps)}
        oc = flopy.modflow.ModflowOc(self.model, stress_period_data=spd,
                                 save_every=True, compact=True,unit_number=39)
    def check(self):
        print(self.model.check())
    def run(self):
        # self.model.run()
        self.model.write_input()
        success, mfoutput = self.model.run_model('MODFLOW-NWT.exe')
        print(success)
        
def main():
    # pathNam=os.path.join('..','simcopiapo','modflow','run','SIMCOPIAPO.nam')
    pathNam=os.path.join('..','modflow','gv6nwt.nam')
    os.chdir(os.path.dirname(pathNam))
    modelo=model(pathNam,'Copiapo')
    modelo.load()
    modelo.run()
    

    
    
if __name__=='__main__':
    main()