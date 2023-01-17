import numpy as np
import pandas as pd

from math import exp

Lautaro2_Afloramiento_inicial = 0
Lautaro2_endvalue = 300
Lautaro2_alfa = 0
Lautaro2_tau = 80
Lautaro2_time = 0
malpaso_rch_threshold = 1000
ccopiapo_rch_threshold = 3000

def run_swmodel(prorrata_S2_agricola, prorrata_S3_agricola, prorrata_S4_agricola, prorrata_S5_agricola, prorrata_S6_agricola, compliance,
                ST_swap_89_a_17, ST_swap_89_a_ACH, ST_swap_89_a_S56_rio, ST_swap_89_a_S5_tubo_rio, ST_swap_89_a_S5_tubo_mar,
                ST_Lautaro2, ST_entubamiento_canales,
                ST_recarga_artificial_S3Nantoco, MAR_capacity_S3Nantoco, ST_recarga_artificial_S4AntesKaukari, MAR_capacity_S4AntesKaukari,
                ST_recarga_artificial_S4DespuesKaukari, MAR_capacity_S4DespuesKaukari, ST_recarga_artificial_S5PiedraColgada, MAR_capacity_S5PiedraColgada,
                ModeloEmbalseLautaro_df_M, LaPuerta_GWSW_df_M,
                irrigationdemands_S234_df, irrigationdemands_S56_df, demandcurves_df):

    def reparto_distritos(Q_LaPuerta):

        if ST_swap_89_a_17 == False:                

            Q_D1 = int(Q_LaPuerta*0.9*0.12)
            Q_D2 = int(Q_LaPuerta*0.9*0.12)
            Q_D3 = int(Q_LaPuerta*0.9*0.12)
            Q_D4 = int(Q_LaPuerta*0.9*0.12)
            Q_D5 = int(Q_LaPuerta*0.9*0.12)
            Q_D6 = int(Q_LaPuerta*0.9*0.12)
            Q_D7 = int(Q_LaPuerta*0.9*0.12)
            Q_D89 = int(Q_LaPuerta*0.9*0.16)

        if ST_swap_89_a_17 == True:                

            Q_D1 = int(Q_LaPuerta*0.9*1/7)
            Q_D2 = int(Q_LaPuerta*0.9*1/7)
            Q_D3 = int(Q_LaPuerta*0.9*1/7)
            Q_D4 = int(Q_LaPuerta*0.9*1/7)
            Q_D5 = int(Q_LaPuerta*0.9*1/7)
            Q_D6 = int(Q_LaPuerta*0.9*1/7)
            Q_D7 = int(Q_LaPuerta*0.9*1/7)
            Q_D89 = 0   # i.e., D89 stop operating, and delivery rule is adjusted to apportion D89's quota among the other districts

        return [Q_D1,Q_D2,Q_D3,Q_D4,Q_D5,Q_D6,Q_D7,Q_D89]

    def balance_distrito(distrito, month, Q_rio_in, Q_reparto, irrigationdemands_df, demandcurves_df):

        # factor correccion demanda por estacionalidad de riego
        factor_demanda=demandcurves_df[demandcurves_df['Distrito'] == distrito][month].values[0]

        # estrategia prorrata
        if ((distrito == 1) | (distrito == 2) | (distrito == 3)):
            factor_prorrata_sup = prorrata_S2_agricola

        if ((distrito == 4) | (distrito == 5) | (distrito == 6)):
            factor_prorrata_sup = prorrata_S3_agricola

        if ((distrito == 7) | (distrito == 89)):
            factor_prorrata_sup = prorrata_S4_agricola

        if factor_prorrata_sup != 1:
            factor_prorrata_sup = (factor_prorrata_sup + (1 - factor_prorrata_sup) * (1 - compliance))

        # DEMANDA BRUTAS — predios fuente canal (C) y mixto (M)
        Q_dda_C = irrigationdemands_df[(irrigationdemands_df['Fuen_Riego'].str.match('C')) & (irrigationdemands_df['Distrito_riego'] == distrito)]['demanda_bruta'].values[0]
        Q_dda_M = irrigationdemands_df[(irrigationdemands_df['Fuen_Riego'].str.match('M')) & (irrigationdemands_df['Distrito_riego'] == distrito)]['demanda_bruta'].values[0]
        if ((distrito == 7) | (distrito == 89)): Q_dda_P = 0
        else: Q_dda_P = irrigationdemands_df[(irrigationdemands_df['Fuen_Riego'].str.match('P')) & (irrigationdemands_df['Distrito_riego'] == distrito)]['demanda_riego'].values[0]

        # corregir demandas brutas por factor estacional y prorrata
        Q_dda_C = Q_dda_C * factor_demanda
        Q_dda_M = Q_dda_M * factor_demanda
        Q_dda_P = Q_dda_P * factor_demanda

        # PERDIDAS RIEGO — predios fuente canal (C) y mixto (M)
        Q_perdidariego_C = irrigationdemands_df[(irrigationdemands_df['Fuen_Riego'].str.match('C')) & (irrigationdemands_df['Distrito_riego'] == distrito)]['perdidas_riego'].values[0]
        Q_perdidariego_M = irrigationdemands_df[(irrigationdemands_df['Fuen_Riego'].str.match('M')) & (irrigationdemands_df['Distrito_riego'] == distrito)]['perdidas_riego'].values[0]
        if ((distrito == 7) | (distrito == 89)): Q_perdidariego_P = 0
        else: Q_perdidariego_P = irrigationdemands_df[(irrigationdemands_df['Fuen_Riego'].str.match('P')) & (irrigationdemands_df['Distrito_riego'] == distrito)]['perdidas_riego'].values[0]

        # corregir perdidas riego por factor estacional y prorrata
        Q_perdidariego_C = Q_perdidariego_C * factor_demanda
        Q_perdidariego_M = Q_perdidariego_M * factor_demanda
        Q_perdidariego_P = Q_perdidariego_P * factor_demanda

        # PERDIDAS CANALES — fuente canal (C) y mixto (M)
        Q_perdidacanales_C = irrigationdemands_df[(irrigationdemands_df['Fuen_Riego'].str.match('C')) & (irrigationdemands_df['Distrito_riego'] == distrito)]['perdidas_canales'].values[0]
        Q_perdidacanales_M = irrigationdemands_df[(irrigationdemands_df['Fuen_Riego'].str.match('M')) & (irrigationdemands_df['Distrito_riego'] == distrito)]['perdidas_canales'].values[0]

        # corregir perdidas canales por factor estacional y prorrata
        Q_perdidacanales_C = Q_perdidacanales_C * factor_demanda
        Q_perdidacanales_M = Q_perdidacanales_M * factor_demanda

        # ESTRATEGIA entubamiento canales

        if ST_entubamiento_canales == True:
            Q_dda_C = Q_dda_C - Q_perdidacanales_C
            Q_dda_M = Q_dda_M - Q_perdidacanales_M
            Q_perdidacanales_C = 0
            Q_perdidacanales_M = 0

        if Q_reparto > Q_rio_in: Q_reparto = Q_rio_in    # river does not have enough supply to satisfy this district's delivery


        # Qreparto = 0
        if Q_reparto == 0:

            Q_entrega = 0

            Satisfaccion_dda_C = 0
            Satisfaccion_dda_M = 0
            Satisfaccion_dda_SUP = 0

            Perdidas_riego = 0
            Perdidas_canales = 0

            Q_dda_M_a_P = 0

            Q_dda_P_new = 0


        # Qreparto satisface parcialmente dda C, toda la dda M pasa a P 
        elif ((Q_reparto > 0) & (Q_reparto < Q_dda_C)):   

            Q_entrega = Q_reparto

            Satisfaccion_dda_C = Q_entrega / Q_dda_C
            Satisfaccion_dda_M = 0
            Satisfaccion_dda_SUP = Q_entrega / (Q_dda_C + Q_dda_M)

            Perdidas_riego = Q_perdidariego_C * Satisfaccion_dda_C + (Q_perdidariego_M + Q_perdidariego_P) * factor_prorrata_sup
            Perdidas_canales = Q_perdidacanales_C * Satisfaccion_dda_C

            Q_dda_M_a_P = Q_dda_M

            Q_dda_P_new = (Q_dda_P + Q_dda_M_a_P) * factor_prorrata_sup


        # Qreparto satisface completamente dda C y solo parcialmente dda M, dda insatisfecha M pasa a P
        elif ((Q_reparto >= Q_dda_C) & (Q_reparto < (Q_dda_C + Q_dda_M ))):              

            Q_entrega = Q_reparto

            Satisfaccion_dda_C = 1
            Satisfaccion_dda_M = (Q_entrega - Q_dda_C) / Q_dda_M
            Satisfaccion_dda_SUP = Q_entrega / (Q_dda_C + Q_dda_M)

            Perdidas_riego = Q_perdidariego_C + Q_perdidariego_M * Satisfaccion_dda_M + (Q_perdidariego_M * (1 - Satisfaccion_dda_M) + Q_perdidariego_P) * factor_prorrata_sup
            Perdidas_canales = Q_perdidacanales_C + Q_perdidacanales_M * Satisfaccion_dda_M

            Q_dda_M_a_P = (Q_dda_C + Q_dda_M) - Q_entrega

            Q_dda_P_new = (Q_dda_P + Q_dda_M_a_P) * factor_prorrata_sup


        # Qreparto satisface completamente dda C y M   
        else:                                               # i.e, (Q_reparto >= (Q_dda_C + Q_dda_M))

            Q_entrega = Q_dda_C + Q_dda_M

            Satisfaccion_dda_C = 1
            Satisfaccion_dda_M = 1
            Satisfaccion_dda_SUP = 1

            Perdidas_riego = Q_perdidariego_C + Q_perdidariego_M + (Q_perdidariego_P) * factor_prorrata_sup
            Perdidas_canales = Q_perdidacanales_C + Q_perdidacanales_M

            Q_dda_M_a_P = 0

            Q_dda_P_new = Q_dda_P * factor_prorrata_sup


        Q_rio_out = Q_rio_in - Q_entrega

        if Q_rio_out <= 0:                                          # no hay excedentes despues de reparto
            Q_rio_out = 0

        if ((distrito == 89) & (Q_rio_out > 0)):                    # se asume que en Distrito 89 la totalidad de los excedentes van a RCH
            Perdidas_canales += Q_rio_out
            Q_rio_out = 0

        # estrategia swap D89 a D17
        if ((distrito == 89) & (ST_swap_89_a_17 == True)):

            Q_dda_C = 0
            Q_dda_M = 0 
            Q_dda_P = 0
            Q_perdidariego_C = 0
            Q_perdidariego_M = 0  
            Q_perdidariego_P = 0
            Q_perdidacanales_C = 0
            Q_perdidacanales_M = 0
            Q_entrega = 0
            Satisfaccion_dda_C = 0
            Satisfaccion_dda_M = 0
            Satisfaccion_dda_SUP = 0
            Perdidas_riego = 0
            Perdidas_canales = 0
            Q_dda_M_a_P = 0
            Q_dda_P_new = 0

        # estrategia swap D89 a Aguas Chañar
        if ((distrito == 89) & (ST_swap_89_a_ACH == True)):

            Q_dda_C = 0
            Q_dda_M = 0 
            Q_dda_P = 0
            Q_perdidariego_C = 0
            Q_perdidariego_M = 0  
            Q_perdidariego_P = 0
            Q_perdidacanales_C = 0
            Q_perdidacanales_M = 0
            Q_entrega = 0
            Satisfaccion_dda_C = 0
            Satisfaccion_dda_M = 0
            Satisfaccion_dda_SUP = 0
            Perdidas_riego = 0
            Perdidas_canales = 0
            Q_dda_M_a_P = 0
            Q_dda_P_new = 0    

        # ESTRATEGIA swap D89 a S56 por Rio Copiapo
        if ((distrito == 89) & (ST_swap_89_a_S56_rio == True)):

            Q_dda_C = 0
            Q_dda_M = 0 
            Q_dda_P = 0
            Q_perdidariego_C = 0
            Q_perdidariego_M = 0  
            Q_perdidariego_P = 0
            Q_perdidacanales_C = 0
            Q_perdidacanales_M = 0
            Q_entrega = 0
            Satisfaccion_dda_C = 0
            Satisfaccion_dda_M = 0
            Satisfaccion_dda_SUP = 0
            Perdidas_riego = 0
            Perdidas_canales = 0
            Q_dda_M_a_P = 0
            Q_dda_P_new = 0

        # ESTRATEGIA swap D89 a agricultura S5 por tubo — excedente a Rio Copiapo cabecera S6
        if ((distrito == 89) & (ST_swap_89_a_S5_tubo_rio == True)):

            Q_dda_C = 0
            Q_dda_M = 0 
            Q_dda_P = 0
            Q_perdidariego_C = 0
            Q_perdidariego_M = 0  
            Q_perdidariego_P = 0
            Q_perdidacanales_C = 0
            Q_perdidacanales_M = 0
            Q_entrega = 0
            Satisfaccion_dda_C = 0
            Satisfaccion_dda_M = 0
            Satisfaccion_dda_SUP = 0
            Perdidas_riego = 0
            Perdidas_canales = 0
            Q_dda_M_a_P = 0
            Q_dda_P_new = 0

        # ESTRATEGIA swap D89 a agricultura S5 por tubo — excedente a obras de recarga artificial en Rio Copiapo S5
        if ((distrito == 89) & (ST_swap_89_a_S5_tubo_mar == True)):

            Q_dda_C = 0
            Q_dda_M = 0 
            Q_dda_P = 0
            Q_perdidariego_C = 0
            Q_perdidariego_M = 0  
            Q_perdidariego_P = 0
            Q_perdidacanales_C = 0
            Q_perdidacanales_M = 0
            Q_entrega = 0
            Satisfaccion_dda_C = 0
            Satisfaccion_dda_M = 0
            Satisfaccion_dda_SUP = 0
            Perdidas_riego = 0
            Perdidas_canales = 0
            Q_dda_M_a_P = 0
            Q_dda_P_new = 0

        return Q_reparto, Q_entrega, Q_rio_in, Q_rio_out, Satisfaccion_dda_C, Satisfaccion_dda_M, Satisfaccion_dda_SUP, Perdidas_riego, Perdidas_canales, Q_dda_M_a_P, Q_dda_P_new

    def balance_SectorAcuifero(sector, month, irrigationdemands_df, demandcurves_df):

        if sector == 'S5': sector_DGA = 'Sector 5'
        if sector == 'S6': sector_DGA = 'Sector 6'

        # factor correccion demanda por estacionalidad de riego
        factor_demanda=demandcurves_df[demandcurves_df['Distrito'] == sector][month].values[0]

        # DEMANDA BRUTAS — predios fuente pozo (P)    
        Q_dda_P = irrigationdemands_df[irrigationdemands_df['Sector_DGA'].str.match(sector_DGA)]['demanda_riego'].values[0]

        # corregir demandas brutas por factor estacional y prorrata
        Q_dda_P = Q_dda_P * factor_demanda

        # PERDIDAS RIEGO — predios fuente canal (C) y mixto (M)
        Q_perdidariego_P = irrigationdemands_df[irrigationdemands_df['Sector_DGA'].str.match(sector_DGA)]['perdidas_riego'].values[0]

        # corregir perdidas riego por factor estacional
        Q_perdidariego_P = Q_perdidariego_P * factor_demanda

        return Q_dda_P, Q_perdidariego_P

    # infiltration factor for Mal Paso irrigation canal
    I_CNegras_MalPaso = 0.25

    # scaling factor for infiltration equation (see DICTUC report)
    c=0.9 

    # infiltration factors Copiapo River        
    I_Lautaro_Capilla = 0.01         
    I_Capilla_SanAntonio = 0.01 
    I_SanAntonio_LosLoros = 0.00  
    I_LosLoros_LaPuerta = 0.00  
    I_LaPuerta_LaTurbina = 0.14 
    I_LaTurbina_ElYeso = 0.14 
    I_ElYeso_CNegras = 0.12
    I_CNegras_Pabellon = 0.05  
    I_Pabellon_Cerrillos = 0.22 
    I_Cerrillos_Nantoco = 0.00  
    I_Nantoco_TAmarilla = 0.20 
    I_TAmarilla_CCopiapo = 0.20
    I_CCopiapo_Chamonate = 0.30
    I_Chamonate_PColgada = 0.30
    I_PColgada_SanJuan = 0.30
    I_SanJuan_VFertil = 0.30
    I_VFertil_Angostura = 0.30

    def SW_DELIVERY_submodel(year, month, timestep):
        
        h_regla = ModeloEmbalseLautaro_df_M[(ModeloEmbalseLautaro_df_M.index.month == month) & 
                                              (ModeloEmbalseLautaro_df_M.index.year == year)]['h_regla'].values[0]

        Vi = ModeloEmbalseLautaro_df_M[(ModeloEmbalseLautaro_df_M.index.month == month) & 
                                              (ModeloEmbalseLautaro_df_M.index.year == year)]['Vi'].values[0]
        
        Q_Pastillo = ModeloEmbalseLautaro_df_M[(ModeloEmbalseLautaro_df_M.index.month == month) & 
                                              (ModeloEmbalseLautaro_df_M.index.year == year)]['Q_Pastillo'].values[0] * 1000
        
        Q_LautaroControlada = ModeloEmbalseLautaro_df_M[(ModeloEmbalseLautaro_df_M.index.month == month) & 
                                              (ModeloEmbalseLautaro_df_M.index.year == year)]['Q_Lautaro_sim'].values[0] * 1000            # <------ deploy: _sim / calibrate: _obs
        
        Q_Vertedero = ModeloEmbalseLautaro_df_M[(ModeloEmbalseLautaro_df_M.index.month == month) & 
                                              (ModeloEmbalseLautaro_df_M.index.year == year)]['Q_Vertedero_sim'].values[0] * 1000
        
        Q_Afloramiento_LaPuerta = LaPuerta_GWSW_df_M[(LaPuerta_GWSW_df_M.index.month == month) & 
                                              (LaPuerta_GWSW_df_M.index.year == year)]['Q_Afloramiento'].values[0] * 1000
        
        Q_LaPuerta = LaPuerta_GWSW_df_M[(LaPuerta_GWSW_df_M.index.month == month) & 
                                              (LaPuerta_GWSW_df_M.index.year == year)]['Q_LaPuerta_sim'].values[0] * 1000
        
        Q_InfiltracionLautaro = LaPuerta_GWSW_df_M[(LaPuerta_GWSW_df_M.index.month == month) & 
                                              (LaPuerta_GWSW_df_M.index.year == year)]['Q_Infiltracion_Lautaro_sim'].values[0] * 1000      
        
        repartos_mes = reparto_distritos(Q_LaPuerta)
        
        P_full = Vi / 25000000
        
                      ###################################################
                           ############ EMBALSE LAUTARO ###########
                                 ############################
                                       ################
                        
        ### LAUTARO 2.0 STRATEGY ###

        global Lautaro2_Afloramiento_inicial, Lautaro2_endvalue, Lautaro2_alfa, Lautaro2_tau, Lautaro2_time

        if (ST_Lautaro2 == True) & (timestep == 60):
            Lautaro2_Afloramiento_inicial = Q_Afloramiento_LaPuerta
            Lautaro2_alfa = Lautaro2_endvalue / Lautaro2_Afloramiento_inicial
        
        if (ST_Lautaro2 == True) & (timestep >= 60):
            Q_Afloramiento_LaPuerta = Lautaro2_Afloramiento_inicial + Lautaro2_Afloramiento_inicial * (Lautaro2_alfa - 1) * (1 - exp(-Lautaro2_time/Lautaro2_tau))
            Lautaro2_time += 1


        ############ ESTACION FLUVIOMETRICA RIO COPIAPO EN LAUTARO ###########

        Q_rio_in_D1 = Q_LautaroControlada + Q_Vertedero

        ### D1: Lautaro-La Capilla ###
        Q_reparto_D1, Q_entrega_D1, Q_rio_in_D1, Q_rio_out_D1, Satisfaccion_dda_C_D1, Satisfaccion_dda_M_D1, Satisfaccion_dda_SUP_D1, Perdidas_riego_D1, Perdidas_canales_D1, Q_dda_M_a_P_D1, Q_dda_P_new_D1 = balance_distrito(1, month, Q_rio_in_D1, repartos_mes[0], irrigationdemands_S234_df, demandcurves_df)


        RCH_rio_Lautaro_LaCapilla = I_Lautaro_Capilla * Q_rio_out_D1 ** c
        Q_rio_in_D2 = Q_rio_out_D1 - RCH_rio_Lautaro_LaCapilla
        if Q_rio_in_D2 < 0: Q_rio_in_D2 = 0


        ### D2: La Capilla-San Antonio ###
        Q_reparto_D2, Q_entrega_D2, Q_rio_in_D2, Q_rio_out_D2, Satisfaccion_dda_C_D2, Satisfaccion_dda_M_D2, Satisfaccion_dda_SUP_D2, Perdidas_riego_D2, Perdidas_canales_D2, Q_dda_M_a_P_D2, Q_dda_P_new_D2 = balance_distrito(2, month, Q_rio_in_D2 + Q_Afloramiento_LaPuerta, repartos_mes[1], irrigationdemands_S234_df, demandcurves_df)


        RCH_rio_LaCapilla_SanAntonio = I_Capilla_SanAntonio * Q_rio_out_D2 ** c
        Q_rio_in_D3 = Q_rio_out_D2 - RCH_rio_LaCapilla_SanAntonio
        if Q_rio_in_D3 < 0: Q_rio_in_D3 = 0


        ### D3: San Antonio-La Puerta + La Puerta-La Turbina ###
        Q_reparto_D3, Q_entrega_D3, Q_rio_in_D3, Q_rio_out_D3, Satisfaccion_dda_C_D3, Satisfaccion_dda_M_D3, Satisfaccion_dda_SUP_D3, Perdidas_riego_D3, Perdidas_canales_D3, Q_dda_M_a_P_D3, Q_dda_P_new_D3 = balance_distrito(3, month, Q_rio_in_D3, repartos_mes[2], irrigationdemands_S234_df, demandcurves_df)


        RCH_rio_SanAntonio_LaTurbina = (I_SanAntonio_LosLoros + I_LosLoros_LaPuerta + I_LaPuerta_LaTurbina) / 3 * Q_rio_out_D3 ** c 
        Q_rio_in_D4 = Q_rio_out_D3 - RCH_rio_SanAntonio_LaTurbina
        if Q_rio_in_D4 < 0: Q_rio_in_D4 = 0


        ############ ESTACION FLUVIOMETRICA RIO COPIAPO EN LA PUERTA ###########

        ### D4: La Turbina-ElYeso + El Yeso-Compuertas Negras ###
        Q_reparto_D4, Q_entrega_D4, Q_rio_in_D4, Q_rio_out_D4, Satisfaccion_dda_C_D4, Satisfaccion_dda_M_D4, Satisfaccion_dda_SUP_D4, Perdidas_riego_D4, Perdidas_canales_D4, Q_dda_M_a_P_D4, Q_dda_P_new_D4 = balance_distrito(4, month, Q_rio_in_D4, repartos_mes[3], irrigationdemands_S234_df, demandcurves_df)


        RCH_rio_LaTurbina_CNegras = (I_LaTurbina_ElYeso + I_ElYeso_CNegras) / 2 * Q_rio_out_D4 ** c 
        Q_rio_in_D5 = Q_rio_out_D4 - RCH_rio_LaTurbina_CNegras        # caudal en rio justo aguas arriba bocatoma CNegras
        if Q_rio_in_D5 < 0: Q_rio_in_D5 = 0


        ############ PUNTO BIFURCACION RIO COPIAPO - CANAL COMPUERTAS NEGRAS ##############

        #if year <= 2004: Qmax_MalPaso = 3000     # uncomment for calibration
        #if year > 2004: Qmax_MalPaso = 1000      # uncomment for calibration

        Qmax_MalPaso = 1000    # uncomment for deployment
        total_reparto_distritos_MalPaso = np.sum(reparto_distritos(Q_LaPuerta)[4:])
        if (total_reparto_distritos_MalPaso > Qmax_MalPaso): 
            total_reparto_distritos_MalPaso = Qmax_MalPaso    # se supera capacidad conduccion canal Compuertas Negras / Mal Paso, desviar Qmax

        if Q_rio_in_D5 >= total_reparto_distritos_MalPaso:

            Q_canal_in_D5 = total_reparto_distritos_MalPaso
            Q_rio_CNegras = Q_rio_in_D5 - total_reparto_distritos_MalPaso

        else:

            Q_canal_in_D5 = Q_rio_in_D5 
            Q_rio_CNegras = 0      

        ############ ADUCCION CANAL COMPUERTAS NEGRAS / MAL PASO (HASTA CIUDAD COPIAPO) ##############        

        ### D5: Compuertas Negras-Pabellon + Pabellon-Cerillos ###
        Q_reparto_D5, Q_entrega_D5, Q_canal_in_D5, Q_canal_out_D5, Satisfaccion_dda_C_D5, Satisfaccion_dda_M_D5, Satisfaccion_dda_SUP_D5, Perdidas_riego_D5, Perdidas_canales_D5, Q_dda_M_a_P_D5, Q_dda_P_new_D5 = balance_distrito(5, month, Q_canal_in_D5, repartos_mes[4], irrigationdemands_S234_df, demandcurves_df)


        RCH_canal_CNegras_Cerrillos = I_CNegras_MalPaso * Q_canal_out_D5 ** c 
        Q_canal_in_D6 = Q_canal_out_D5 - RCH_canal_CNegras_Cerrillos
        if Q_canal_in_D6 < 0: Q_canal_in_D6 = 0


        ### D6: Cerrillos-Mal Paso + Mal Paso-Palermo ###
        Q_reparto_D6, Q_entrega_D6, Q_canal_in_D6, Q_canal_out_D6, Satisfaccion_dda_C_D6, Satisfaccion_dda_M_D6, Satisfaccion_dda_SUP_D6, Perdidas_riego_D6, Perdidas_canales_D6, Q_dda_M_a_P_D6, Q_dda_P_new_D6 = balance_distrito(6, month, Q_canal_in_D6, repartos_mes[5], irrigationdemands_S234_df, demandcurves_df)


        RCH_canal_Cerrillos_Palermo = I_CNegras_MalPaso * Q_canal_out_D6 ** c 
        Q_canal_in_D7 = Q_canal_out_D6 - RCH_canal_Cerrillos_Palermo
        if Q_canal_in_D7 < 0: Q_canal_in_D7 = 0


        ##########  ESTACION FLUVIOMETRICA EN CANAL MAL PASO ##########

        ### D7: Palermo-La Florida ###
        Q_reparto_D7, Q_entrega_D7, Q_canal_in_D7, Q_canal_out_D7, Satisfaccion_dda_C_D7, Satisfaccion_dda_M_D7, Satisfaccion_dda_SUP_D7, Perdidas_riego_D7, Perdidas_canales_D7, Q_dda_M_a_P_D7, Q_dda_P_new_D7 = balance_distrito(7, month, Q_canal_in_D7, repartos_mes[6], irrigationdemands_S234_df, demandcurves_df)


        RCH_canal_Palermo_LaFlorida = I_CNegras_MalPaso * Q_canal_out_D7 ** c
        Q_canal_in_D89 = Q_canal_out_D7 - RCH_canal_Palermo_LaFlorida
        if Q_canal_in_D89 < 0: Q_canal_in_D89 = 0

        ### D89: LA FLORIDA-COPIAPO  ###
        Q_reparto_D89, Q_entrega_D89, Q_canal_in_D89, Q_canal_out_D89, Satisfaccion_dda_C_D89, Satisfaccion_dda_M_D89, Satisfaccion_dda_SUP_D89, Perdidas_riego_D89, Perdidas_canales_D89, Q_dda_M_a_P_D89, Q_dda_P_new_D89 = balance_distrito(89, month, Q_canal_in_D89, repartos_mes[7], irrigationdemands_S234_df, demandcurves_df)

        # NOTE TO SELF: se asume que no hay excedente a la salida de Distrito 8/9 (Q_canal_out_89 = 0), 
        # el remanente va a perdida de canales; ver codigo balance(distrito) mas arriba    

        ############ RIO COPIAPO (AGUAS ABAJO BIFURCACION COMPUERTAS NEGRAS) ##############


        RCH_rio_CNegras_Pabellon = I_CNegras_Pabellon * Q_rio_CNegras ** c
        Q_rio_Pabellon = Q_rio_CNegras - RCH_rio_CNegras_Pabellon
        if Q_rio_Pabellon < 0: Q_rio_Pabellon = 0


        RCH_rio_Pabellon_Cerrillos = I_Pabellon_Cerrillos * Q_rio_Pabellon ** c
        Q_rio_Cerrillos = Q_rio_Pabellon - RCH_rio_Pabellon_Cerrillos
        if Q_rio_Cerrillos < 0: Q_rio_Cerrillos = 0


        RCH_rio_Cerrillos_Nantoco = I_Cerrillos_Nantoco * Q_rio_Cerrillos ** c
        Q_rio_Nantoco = Q_rio_Cerrillos - RCH_rio_Cerrillos_Nantoco


        ##########  ESTACION FLUVIOMETRICA RIO COPIAPO EN MAL PASO ##########

        #global malpaso_rch_threshold, ccopiapo_rch_threshold

        malpaso_rch_threshold = 1000

        if Q_rio_Nantoco < malpaso_rch_threshold:

            RCH_rio_Nantoco_TAmarilla = Q_rio_Nantoco/2
            RCH_rio_TAmarilla_CCopiapo = Q_rio_Nantoco/2

            Q_rio_Nantoco = 0
            Q_rio_TAmarilla = 0
            Q_rio_CCopiapo = 0

            if ST_swap_89_a_17 == True:
                Q_rio_CCopiapo += Q_canal_in_D89

            if ST_swap_89_a_S56_rio == True:
                Q_rio_CCopiapo += Q_canal_in_D89

        else:

            RCH_rio_Nantoco_TAmarilla = I_Nantoco_TAmarilla * Q_rio_Nantoco ** c

            if ST_recarga_artificial_S3Nantoco == True:
                RCH_rio_Nantoco_TAmarilla += MAR_capacity_S3Nantoco

            Q_rio_TAmarilla = Q_rio_Nantoco - RCH_rio_Nantoco_TAmarilla

            if Q_rio_TAmarilla < 0: Q_rio_TAmarilla = 0

            RCH_rio_TAmarilla_CCopiapo = I_TAmarilla_CCopiapo * Q_rio_TAmarilla ** c

            if ST_recarga_artificial_S4AntesKaukari == True:
                RCH_rio_TAmarilla_CCopiapo += MAR_capacity_S4AntesKaukari

            Q_rio_CCopiapo = Q_rio_TAmarilla - RCH_rio_TAmarilla_CCopiapo

            if Q_rio_CCopiapo < 0: Q_rio_CCopiapo = 0

            if ST_swap_89_a_17 == True:
                Q_rio_CCopiapo += Q_canal_in_D89

            if ST_swap_89_a_S56_rio == True:
                Q_rio_CCopiapo += Q_canal_in_D89


        ##########  ESTACION FLUVIOMETRICA RIO COPIAPO EN CIUDAD ##########
        
                  ##################################
                  ######## CIUDAD COPIAPO ##########
                  ##################################
        
        ############  SECTORES ACUIFERO 5 Y 6 ##############  

        Q_dda_P_S5, Q_perdidariego_P_S5 = balance_SectorAcuifero('S5', month, irrigationdemands_S56_df, demandcurves_df)

        # ESTRATEGIA swap D89 a S56 por tubo — excedente a Rio Copiapo cabecera S6
        if ((ST_swap_89_a_S5_tubo_rio == True) | (ST_swap_89_a_S5_tubo_mar == True)):

            Q_dda_P_S5 = Q_dda_P_S5 - Q_canal_in_D89

            if Q_dda_P_S5 < 0: 
                Q_excedente = - Q_dda_P_S5
                Q_dda_P_S5 = 0
            else: Q_excedente = 0

        ccopiapo_rch_threshold = 3000

        if Q_rio_CCopiapo < ccopiapo_rch_threshold:

            RCH_rio_CCopiapo_Chamonate = 2 * Q_rio_CCopiapo / 5
            RCH_rio_Chamonate_PColgada = 2 * Q_rio_CCopiapo / 5
            RCH_rio_PColgada_SanJuan = 1 * Q_rio_CCopiapo / 5
            RCH_rio_SanJuan_VFertil = 0
            RCH_rio_VFertil_Angostura = 0

            if (ST_swap_89_a_S5_tubo_mar == True):
                RCH_rio_CCopiapo_Chamonate += Q_excedente/2
                RCH_rio_Chamonate_PColgada += Q_excedente/2

            if (ST_swap_89_a_S5_tubo_rio == True):
                RCH_rio_PColgada_SanJuan += Q_excedente

            Q_rio_Chamonate = 0
            Q_rio_PColgada = 0
            Q_rio_SanJuan = 0
            Q_rio_VFertil = 0
            Q_rio_Angostura = 0

        else:

            RCH_rio_CCopiapo_Chamonate = I_CCopiapo_Chamonate * Q_rio_CCopiapo ** c
            if ST_recarga_artificial_S4DespuesKaukari == True:
                RCH_rio_CCopiapo_Chamonate += MAR_capacity_S4DespuesKaukari
            if (ST_swap_89_a_S5_tubo_mar == True):
                RCH_rio_CCopiapo_Chamonate = I_CCopiapo_Chamonate * Q_rio_CCopiapo ** c + Q_excedente/2
            Q_rio_Chamonate = Q_rio_CCopiapo - RCH_rio_CCopiapo_Chamonate
            if Q_rio_Chamonate < 0: Q_rio_Chamonate = 0

            RCH_rio_Chamonate_PColgada = I_Chamonate_PColgada * Q_rio_Chamonate ** c
            if  ST_recarga_artificial_S5PiedraColgada == True:
                RCH_rio_Chamonate_PColgada += MAR_capacity_S5PiedraColgada
            if (ST_swap_89_a_S5_tubo_mar == True):
                RCH_rio_Chamonate_PColgada = I_Chamonate_PColgada * Q_rio_Chamonate ** c + Q_excedente/2
            Q_rio_PColgada = Q_rio_Chamonate - RCH_rio_Chamonate_PColgada
            if (ST_swap_89_a_S5_tubo_rio == True):
                Q_rio_PColgada = Q_rio_Chamonate - RCH_rio_Chamonate_PColgada + Q_excedente
            if Q_rio_PColgada < 0: Q_rio_PColgada = 0


        ############  SECTOR ACUIFERO 6  ##############

            RCH_rio_PColgada_SanJuan = I_PColgada_SanJuan * Q_rio_PColgada ** c
            Q_rio_SanJuan = Q_rio_PColgada - RCH_rio_PColgada_SanJuan 
            if Q_rio_SanJuan < 0: Q_rio_SanJuan = 0    

            RCH_rio_SanJuan_VFertil = I_SanJuan_VFertil * Q_rio_SanJuan ** c
            Q_rio_VFertil = Q_rio_SanJuan - RCH_rio_SanJuan_VFertil
            if Q_rio_VFertil < 0: Q_rio_VFertil = 0    

            RCH_rio_VFertil_Angostura = I_VFertil_Angostura * Q_rio_VFertil ** c
            Q_rio_Angostura = Q_rio_VFertil - RCH_rio_VFertil_Angostura
            if Q_rio_Angostura < 0: Q_rio_Angostura = 0 


    ############ RECARGAS TOTALES A SECTORES ACUIFEROS S2-S3-S4-S5-S6 ##############

        RCH_rio_S2 = RCH_rio_Lautaro_LaCapilla + RCH_rio_LaCapilla_SanAntonio + RCH_rio_SanAntonio_LaTurbina

        RCH_rio_S3 = RCH_rio_LaTurbina_CNegras + RCH_rio_CNegras_Pabellon + RCH_rio_Pabellon_Cerrillos + RCH_rio_Cerrillos_Nantoco + RCH_canal_CNegras_Cerrillos + RCH_canal_Cerrillos_Palermo 

        RCH_rio_S4 = RCH_canal_Palermo_LaFlorida + RCH_rio_Nantoco_TAmarilla + RCH_rio_TAmarilla_CCopiapo

        RCH_rio_S5 = RCH_rio_CCopiapo_Chamonate + RCH_rio_Chamonate_PColgada

        RCH_rio_S6 = RCH_rio_PColgada_SanJuan + RCH_rio_SanJuan_VFertil + RCH_rio_VFertil_Angostura

    ############ RECARGAS TOTALES PERDIDAS RIEGO+CANALES S2-S3-S4-S5-S6 ##############

        RCH_riegoycanales_S2 = (Perdidas_riego_D1 + Perdidas_riego_D2 + Perdidas_riego_D3) + (Perdidas_canales_D1 + Perdidas_canales_D2 + Perdidas_canales_D3)
        RCH_riegoycanales_S3 = (Perdidas_riego_D4 + Perdidas_riego_D5 + Perdidas_riego_D6) + (Perdidas_canales_D4 + Perdidas_canales_D5 + Perdidas_canales_D6)
        RCH_riegoycanales_S4 = (Perdidas_riego_D7 + Perdidas_riego_D89) + (Perdidas_canales_D7 + Perdidas_canales_D89)

        Q_dda_P_S6, Q_perdidariego_P_S6 = balance_SectorAcuifero('S6', month, irrigationdemands_S56_df, demandcurves_df)

    ############ SALIDAS MODELO  ##############    

        return [Q_reparto_D1, 
                Q_entrega_D1, 
                Q_rio_in_D1, 
                Q_rio_out_D1, 
                Satisfaccion_dda_C_D1, 
                Satisfaccion_dda_M_D1, 
                Satisfaccion_dda_SUP_D1, 
                Perdidas_riego_D1, 
                Perdidas_canales_D1, 
                Q_dda_M_a_P_D1, 
                Q_dda_P_new_D1,
                
                Q_reparto_D2, 
                Q_entrega_D2, 
                Q_rio_in_D2, 
                Q_rio_out_D2, 
                Satisfaccion_dda_C_D2, 
                Satisfaccion_dda_M_D2, 
                Satisfaccion_dda_SUP_D2, 
                Perdidas_riego_D2, 
                Perdidas_canales_D2, 
                Q_dda_M_a_P_D2, 
                Q_dda_P_new_D2,
                
                Q_reparto_D3, 
                Q_entrega_D3, 
                Q_rio_in_D3, 
                Q_rio_out_D3, 
                Satisfaccion_dda_C_D3, 
                Satisfaccion_dda_M_D3, 
                Satisfaccion_dda_SUP_D3, 
                Perdidas_riego_D3, 
                Perdidas_canales_D3, 
                Q_dda_M_a_P_D3, 
                Q_dda_P_new_D3,            
               
                Q_reparto_D4, 
                Q_entrega_D4, 
                Q_rio_in_D4, 
                Q_rio_out_D4, 
                Satisfaccion_dda_C_D4, 
                Satisfaccion_dda_M_D4, 
                Satisfaccion_dda_SUP_D4, 
                Perdidas_riego_D4, 
                Perdidas_canales_D4, 
                Q_dda_M_a_P_D4, 
                Q_dda_P_new_D4,

                Q_reparto_D5, 
                Q_entrega_D5, 
                Q_rio_in_D5, 
                Q_canal_out_D5, 
                Satisfaccion_dda_C_D5, 
                Satisfaccion_dda_M_D5, 
                Satisfaccion_dda_SUP_D5, 
                Perdidas_riego_D5, 
                Perdidas_canales_D5, 
                Q_dda_M_a_P_D5, 
                Q_dda_P_new_D5,

                Q_reparto_D6, 
                Q_entrega_D6, 
                Q_canal_in_D6, 
                Q_canal_out_D6, 
                Satisfaccion_dda_C_D6, 
                Satisfaccion_dda_M_D6, 
                Satisfaccion_dda_SUP_D6, 
                Perdidas_riego_D6, 
                Perdidas_canales_D6, 
                Q_dda_M_a_P_D6, 
                Q_dda_P_new_D6,
                
                Q_reparto_D7, 
                Q_entrega_D7, 
                Q_canal_in_D7, 
                Q_canal_out_D7, 
                Satisfaccion_dda_C_D7, 
                Satisfaccion_dda_M_D7, 
                Satisfaccion_dda_SUP_D7, 
                Perdidas_riego_D7, 
                Perdidas_canales_D7, 
                Q_dda_M_a_P_D7, 
                Q_dda_P_new_D7,
                
                Q_reparto_D89, 
                Q_entrega_D89, 
                Q_canal_in_D89, 
                Q_canal_out_D89, 
                Satisfaccion_dda_C_D89, 
                Satisfaccion_dda_M_D89, 
                Satisfaccion_dda_SUP_D89, 
                Perdidas_riego_D89, 
                Perdidas_canales_D89, 
                Q_dda_M_a_P_D89, 
                Q_dda_P_new_D89,
                
                Q_rio_Pabellon,
                Q_rio_Cerrillos,
                Q_rio_Nantoco, 
                Q_rio_TAmarilla, 
                Q_rio_CCopiapo, 
                Q_rio_Chamonate,
                Q_rio_PColgada, 
                Q_rio_SanJuan,
                Q_rio_VFertil, 
                Q_rio_Angostura,
                
                Q_canal_in_D5,
                Q_rio_CNegras,
                
                Q_Pastillo,
                Q_LautaroControlada,
                Q_Vertedero,
                Q_Afloramiento_LaPuerta,
                Q_LaPuerta,
                Q_InfiltracionLautaro,
                
                RCH_rio_S2,
                RCH_rio_S3,
                RCH_rio_S4,
                RCH_rio_S5,
                RCH_rio_S6,
                
                Q_dda_P_S5, 
                Q_perdidariego_P_S5,
                Q_dda_P_S6, 
                Q_perdidariego_P_S6,
                
                RCH_riegoycanales_S2,
                RCH_riegoycanales_S3,
                RCH_riegoycanales_S4,
                
                h_regla,
                Vi,
                P_full
               ]

    SWMODEL_out_df = ModeloEmbalseLautaro_df_M.iloc[:,[0]].drop(['Q_Lautaro_obs'], axis=1)
    SWMODEL_out_df['year']=SWMODEL_out_df.index.year
    SWMODEL_out_df['month']=SWMODEL_out_df.index.month
    SWMODEL_out_df['timestep'] = np.arange(len(SWMODEL_out_df)) + 1

    SWMODEL_out_df=SWMODEL_out_df.apply(lambda x: SW_DELIVERY_submodel(x.year, x.month, x.timestep), axis=1, result_type='expand')
    
    New_Labels=['Q_reparto_D1', 
            'Q_entrega_D1', 
            'Q_rio_in_D1', 
            'Q_rio_out_D1', 
            'Satisfaccion_dda_C_D1', 
            'Satisfaccion_dda_M_D1', 
            'Satisfaccion_dda_SUP_D1', 
            'Perdidas_riego_D1', 
            'Perdidas_canales_D1', 
            'Q_dda_M_a_P_D1', 
            'Q_dda_P_new_D1',
            
            'Q_reparto_D2', 
            'Q_entrega_D2', 
            'Q_rio_in_D2', 
            'Q_rio_out_D2', 
            'Satisfaccion_dda_C_D2', 
            'Satisfaccion_dda_M_D2', 
            'Satisfaccion_dda_SUP_D2', 
            'Perdidas_riego_D2', 
            'Perdidas_canales_D2', 
            'Q_dda_M_a_P_D2', 
            'Q_dda_P_new_D2',
            
            'Q_reparto_D3', 
            'Q_entrega_D3', 
            'Q_rio_in_D3', 
            'Q_rio_out_D3', 
            'Satisfaccion_dda_C_D3', 
            'Satisfaccion_dda_M_D3', 
            'Satisfaccion_dda_SUP_D3', 
            'Perdidas_riego_D3', 
            'Perdidas_canales_D3', 
            'Q_dda_M_a_P_D3', 
            'Q_dda_P_new_D3',            
           
            'Q_reparto_D4', 
            'Q_entrega_D4', 
            'Q_rio_in_D4', 
            'Q_rio_out_D4', 
            'Satisfaccion_dda_C_D4', 
            'Satisfaccion_dda_M_D4', 
            'Satisfaccion_dda_SUP_D4', 
            'Perdidas_riego_D4', 
            'Perdidas_canales_D4', 
            'Q_dda_M_a_P_D4', 
            'Q_dda_P_new_D4',

            'Q_reparto_D5', 
            'Q_entrega_D5', 
            'Q_rio_in_D5', 
            'Q_canal_out_D5', 
            'Satisfaccion_dda_C_D5', 
            'Satisfaccion_dda_M_D5', 
            'Satisfaccion_dda_SUP_D5', 
            'Perdidas_riego_D5', 
            'Perdidas_canales_D5', 
            'Q_dda_M_a_P_D5', 
            'Q_dda_P_new_D5',

            'Q_reparto_D6', 
            'Q_entrega_D6', 
            'Q_canal_in_D6', 
            'Q_canal_out_D6', 
            'Satisfaccion_dda_C_D6', 
            'Satisfaccion_dda_M_D6', 
            'Satisfaccion_dda_SUP_D6', 
            'Perdidas_riego_D6', 
            'Perdidas_canales_D6', 
            'Q_dda_M_a_P_D6', 
            'Q_dda_P_new_D6',
            
            'Q_reparto_D7', 
            'Q_entrega_D7', 
            'Q_canal_in_D7', 
            'Q_canal_out_D7', 
            'Satisfaccion_dda_C_D7', 
            'Satisfaccion_dda_M_D7', 
            'Satisfaccion_dda_SUP_D7', 
            'Perdidas_riego_D7', 
            'Perdidas_canales_D7', 
            'Q_dda_M_a_P_D7', 
            'Q_dda_P_new_D7',
            
            'Q_reparto_D89', 
            'Q_entrega_D89', 
            'Q_canal_in_D89', 
            'Q_canal_out_D89', 
            'Satisfaccion_dda_C_D89', 
            'Satisfaccion_dda_M_D89', 
            'Satisfaccion_dda_SUP_D89', 
            'Perdidas_riego_D89', 
            'Perdidas_canales_D89', 
            'Q_dda_M_a_P_D89', 
            'Q_dda_P_new_D89',
            
            'Q_rio_Pabellon',
            'Q_rio_Cerrillos',
            'Q_rio_Nantoco', 
            'Q_rio_TAmarilla', 
            'Q_rio_CCopiapo', 
            'Q_rio_Chamonate',
            'Q_rio_PColgada', 
            'Q_rio_SanJuan',
            'Q_rio_VFertil', 
            'Q_rio_Angostura',
            
            'Q_canal_in_D5',
            'Q_rio_CNegras',
            
            'Q_Pastillo',
            'Q_LautaroControlada',
            'Q_Vertedero',
            'Q_Afloramiento_LaPuerta',
            'Q_LaPuerta',
            'Q_InfiltracionLautaro',
            
            'RCH_rio_S2',
            'RCH_rio_S3',
            'RCH_rio_S4',
            'RCH_rio_S5',
            'RCH_rio_S6',
            
            'Q_dda_P_S5', 
            'Q_perdidariego_P_S5',
            'Q_dda_P_S6', 
            'Q_perdidariego_P_S6',
            
            'RCH_riegoycanales_S2',
            'RCH_riegoycanales_S3',
            'RCH_riegoycanales_S4',
            
            'h_regla',
            'Vi',
            'P_full'
           ]

    SWMODEL_out_df.columns = New_Labels

    return SWMODEL_out_df
