# -*- coding: utf-8 -*-
"""
Created on Fri Dec 16 08:35:05 2022

@author: ccalvo
"""

from flopy.utils import HeadFile
import os
from flopy.export import vtk
import flopy

model_ws=os.path.join('.','modflow','run')
head_file = os.path.join(model_ws, "SIMCOPIAPO.hds")
hds = HeadFile(head_file)


# create the vtk object and export heads
nam_file=os.path.join(model_ws, "SIMCOPIAPO.nam")
ml = flopy.modflow.Modflow.load(nam_file, model_ws='.', check=False)

vtkobj = vtk.Vtk(model=ml)
vtkobj.add_heads(hds)
vtkobj.write(os.path.join('.', "heads_output_test", "freyberg_head.vtu"))