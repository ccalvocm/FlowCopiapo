# -*- coding: utf-8 -*-
"""
Created on Fri Dec 16 08:35:05 2022

@author: ccalvo
"""

from flopy.utils import HeadFile
import os
from flopy.export import vtk
import flopy

def main():

    # dirs
    model_ws=os.path.join('.','modflow','run')
    head_file = os.path.join(model_ws, "SIMCOPIAPO.hds")
    outFile=os.path.join('.','modflow','run','heads.vtk')
    output_dir=os.path.join('.','modelOutputs')
    well_output_dir = os.path.join(output_dir, "WEL")
    dis_output_dir = os.path.join(output_dir, "DIS")
    bas_output_dir = os.path.join(output_dir, "BAS")
    upw_output_dir = os.path.join(output_dir, "UPW")
    lpf_output_dir = os.path.join(output_dir, "LPF")

    # create the vtk object and export heads
    nam_file=os.path.join(model_ws, "SIMCOPIAPO.nam")
    nam_file=r'G:\OneDrive - ciren.cl\2022_Ficha_Atacama\05_Modelos\DGA-DICTUC\MODFLOW Transiente\Copiapo_12102022.nam'
    # load model
    ml = flopy.modflow.Modflow.load(nam_file, model_ws='.', check=False)

def exportHds(ml,head_file,model_ws):
    
    hds = HeadFile(head_file)   
    # export heads
    vtkobj = vtk.Vtk(model=ml)
    vtk.export_heads(ml,head_file,'.',kstpkper=[(0,2)])
    
def exportWel(ml,well_output_dir):
    ml.wel.export(well_output_dir, fmt="vtk")
    
def exportDis(ml,dis_output_dir):
    ml.dis.export(dis_output_dir, fmt="vtk")

def exportBas(ml,bas_output_dir):
    ml.bas6.export(bas_output_dir, fmt="vtk")

def exportUpw(ml,upw_output_dir):
    ml.upw.export(upw_output_dir, fmt="vtk")

def exportLpf(ml,lpf_output_dir):
    ml.lpf.export(lpf_output_dir, fmt="vtk")
