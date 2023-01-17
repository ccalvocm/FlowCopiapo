from datetime import datetime, timedelta
import math
import numpy as np
import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')

class DamOperationModel():

    def __init__(self, storage_areas, curva_descarga_controlada, lautaro2):
        # Constants (Modelo)
        self.Vcritico = 0
        self.Qmax = 2.5
        self.Pastillocrit = 0
        self.Qinf_max = 4
        self.Qinf_min = 0.5
        # Constants (Interaccion GW-SW La Puerta)
        self.Vmax = 588
        self.Vini = 588
        self.alfa = 0.0012
        # Inputs (Modelo)
        self.Q_Lautaro_obs = 0.0
        self.Q_Pastillo = 0.0
        self.Q_ChecoDesal = 0.2
        # Inputs (Interaccion GW-SW La Puerta)
        self.Q_LaPuerta_obs = 0.0
        self.Q_bombeo = 0.0
        # Lookup
        self.storage_areas = storage_areas
        self.curva_descarga_controlada = curva_descarga_controlada
        # Setting
        self.lautaro2 = lautaro2

    def reset(self):
        self.Vi = 20000000
        self.Vi_hist = {}
        self.t_0 = True

    def run_time_step(self, dt):

        # Modelo

        if not self.t_0:
            self.Vi = self.Vf_abs

        if dt.month == 9 and dt.day == 1 and dt.hour == 0:
            self.Vi_hist[dt.year] = self.Vi

        self.h_regla = 8.53 + 1.33e-6 * self.Vi - 5.26e-14 * math.pow(self.Vi, 2) + 9.83e-22 * math.pow(self.Vi, 3)

        index = int(math.floor(self.h_regla * 100)) - 699
        if index < len(self.storage_areas):
            self.espejo = self.storage_areas[index]
        else:
            self.espejo = self.storage_areas[len(self.storage_areas)-1]

        if (self.h_regla <= 24.24):
            self.Q_Vertedero_sim = 0
        else:
            self.Q_Vertedero_sim = 183 * math.pow(self.h_regla-24.24, 1.5)

        if dt.month >= 9:
            self.irrigation_year = dt.year
        else:
            self.irrigation_year = dt.year - 1

        self.V_repartir = self.Vi #self.Vi_hist[self.irrigation_year]

        if self.t_0:
            self.Q_Lautaro_med = self.V_repartir / 86400 / 30.4 / 7 * self.Vi / self.V_repartir
        else:
            self.Q_Lautaro_med = self.V_repartir / 86400 / 30.4 / 7

        self.curva_descarga = self.curva_descarga_controlada[dt.month]

        self.Q_Lautaro_inst = self.Q_Lautaro_med * self.curva_descarga

        if (self.Q_Pastillo > self.Pastillocrit and self.Vi > self.Vcritico and self.curva_descarga > 0):
            self.Q_Lautaro_sim = self.Q_Lautaro_inst + (self.Qmax - self.Q_Lautaro_inst) / (25000000 - self.Vcritico) * (self.Vi - self.Vcritico)
        else:
            self.Q_Lautaro_sim = self.Q_Lautaro_inst
        self.Q_Lautaro_sim += 0.1

        if self.lautaro2 and dt >= datetime(1996,9,1,0):
            self.Q_Infiltracion = 0.0
        else:
            self.Q_Infiltracion = self.Qinf_min + (self.Qinf_max - self.Qinf_min) / 25000000 * self.Vi

        if self.Q_Infiltracion > 0:
            self.Q_Infiltracion_sim = self.Q_Infiltracion
        else:
            self.Q_Infiltracion_sim = 0

        self.dV_total = (self.Q_Pastillo - self.Q_Vertedero_sim - self.Q_Lautaro_sim - self.Q_Infiltracion_sim + self.Q_ChecoDesal) * 86400 / 4

        self.Vf = self.Vi + self.dV_total

        if self.Vf > 0:
            self.Vf_abs = self.Vf
        else:
            self.Vf_abs = 0

        # Interaccion GW-SW La Puerta

        if self.t_0:
            self.Vn = self.Vini - self.Vmax
        else:
            self.Vn = self.previous_VnPlus1

        self.Q_Infiltracion_Lautaro_sim = self.Q_Infiltracion_sim

        self.VnPlus1 = self.Vn * math.pow(2.71, -self.alfa * 6 * 60 * 60) + (self.Q_Infiltracion_Lautaro_sim - self.Q_bombeo) / self.alfa * (1 - math.pow(2.71, -self.alfa * 6 * 60 * 60))

        if self.VnPlus1 > 0:
            self.Q_Afloramiento = self.VnPlus1 * self.alfa
        else:
            self.Q_Afloramiento = 0.0

        self.Q_LaPuerta_sim = self.Q_Afloramiento + self.Q_Lautaro_sim + self.Q_Vertedero_sim

        self.previous_VnPlus1 = self.VnPlus1

        self.t_0 = False

def resampleQ():
    qDay=pd.read_excel(os.path.join(DATA_DIR,
'CaudalesDGAyMOP_Atacama_2022_revA.xlsx'),
                       sheet_name='Datos',index_col=0,parse_dates=True)
    qPastillo=qDay['03430003-8'].iloc[1:]
    qPastillo6H=qPastillo.resample("6H").ffill()
    qPastillo6H=qPastillo6H.loc[(qPastillo6H.index>='1991-09-01') & (qPastillo6H.index<='2022-03-31')]
    return qPastillo6H

def fillQ(df1,df2):
    df1=pd.DataFrame(df1.copy())
    idx=df1[df1.squeeze().isna()].index
    idx2=idx.intersection(df2.index)
    df1.loc[idx2,df1.columns]=df2.loc[idx2].values
    return df1

def extendArray(arr,df):
    steps=len(df)
    return np.append(arr,np.array([np.nan]*(steps-len(arr)+1)))
    
def run(Q_Pastillo_ts, lautaro2, record=[]):

    # Q Copiapo Pastillo CSIRO    
    dfQPastilloTs=pd.DataFrame(Q_Pastillo_ts,index=pd.date_range('1991-09-01',
'2017-03-31 18:00:00',freq='6H'))

    # Q Copiapo en Pastillo DGA
    dfQPastilloDGA=resampleQ()
    print(dfQPastilloDGA)
    dfQPastilloDGAfill=fillQ(dfQPastilloDGA,dfQPastilloTs)
    Q_Pastillo_ts=dfQPastilloDGAfill.values
        
    delta = timedelta(hours=6)
    start = datetime(1991,9,1,0)
    # end = datetime(2017,3,31,18)
    end=datetime(2022,3,31,0)

    dates = []
    steps = 0
    n = start
    while n <= end:
        dates.append(n)
        n = n + delta
        steps = steps + 1

    output = {}
    for r in record:
        output[r] = np.zeros((steps))

    batimetria_df = pd.read_csv(os.path.join(DATA_DIR, 'batimetria.csv'))
    storage_areas = batimetria_df['Area'].values

    curva_descarga_controlada = {
        1: 1.5,
        2: 0.5,
        3: 0.25,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0.25,
        10: 0.5,
        11: 1.5,
        12: 1.5
    }

    Q_Lautaro_obs_ts=np.loadtxt(os.path.join(DATA_DIR, 'Q_Lautaro_obs.dat'))
    Q_Lautaro_obs_ts=extendArray(Q_Lautaro_obs_ts,Q_Pastillo_ts)
    Q_LaPuerta_obs_ts=np.loadtxt(os.path.join(DATA_DIR,'Q_LaPuerta_obs.dat'))
    Q_LaPuerta_obs_ts=extendArray(Q_LaPuerta_obs_ts,Q_Pastillo_ts)

    model=DamOperationModel(storage_areas,curva_descarga_controlada,lautaro2)
    model.reset()

    model.Q_Evap = 0.0
    model.Q_bombeo = 0.089

    dt = start
    for i in range(steps):
        model.Q_Lautaro_obs = Q_Lautaro_obs_ts[i]
        model.Q_Pastillo = Q_Pastillo_ts[i]
        model.Q_LaPuerta_obs = Q_LaPuerta_obs_ts[i]
        model.run_time_step(dt)
        dt = dt + delta
        for r in record:
            output[r][i] = getattr(model, r)

    return (dates, output)

def run_model(Q_Pastillo_ts, lautaro2):

    record = ['Q_Lautaro_obs', 'Q_Lautaro_sim', 'Q_Vertedero_sim', 'Q_Afloramiento', 'Q_LaPuerta_sim', 'Q_Infiltracion_Lautaro_sim', 'Q_Pastillo', 'h_regla', 'Vi']
    result = run(Q_Pastillo_ts, lautaro2, record)
    dates = result[0]
    ts = result[1]
    ModeloEmbalseLautaro_df_6h = pd.DataFrame(data={'Q_Lautaro_obs': ts['Q_Lautaro_obs'], 'Q_Lautaro_sim': ts['Q_Lautaro_sim'], 'Q_Vertedero_sim': ts['Q_Vertedero_sim'], 'Q_Pastillo': ts['Q_Pastillo'], 'h_regla': ts['h_regla'], 'Vi': ts['Vi']}, index = pd.DatetimeIndex(dates))
    ModeloEmbalseLautaro_df_6h.index.name = 'date'
    LaPuerta_GWSW_df_6h = pd.DataFrame(data={'Q_Afloramiento': ts['Q_Afloramiento'], 'Q_LaPuerta_sim': ts['Q_LaPuerta_sim'], 'Q_Infiltracion_Lautaro_sim': ts['Q_Infiltracion_Lautaro_sim']}, index = pd.DatetimeIndex(dates))
    LaPuerta_GWSW_df_6h.index.name = 'date'
    return (ModeloEmbalseLautaro_df_6h, LaPuerta_GWSW_df_6h)

def run_dam_operation_model(Q_Pastillo_ts_name, swap_CAS_RAM, lautaro2):
    Q_Pastillo_ts=pd.read_csv(os.path.join(DATA_DIR, 
                                'Q_Pastillo.csv'))[Q_Pastillo_ts_name].values
    print('1 OK')
    if swap_CAS_RAM:
        reduce_by = 200.0 / 1000.0 # 200L/s
        for i in range(len(Q_Pastillo_ts)):
            Q_Pastillo_ts[i] = max(Q_Pastillo_ts[i] - reduce_by, 0.0)

    return run_model(Q_Pastillo_ts, lautaro2)
