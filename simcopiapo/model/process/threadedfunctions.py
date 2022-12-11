import numpy as np

def dw_wel_sp(rcs, dw_schedule, stress_periods, dw_wells):

    sp_dict_DW = {}

    for stress_period in stress_periods:

        sp_data = []

        for well in dw_wells:

            i, j = rcs[well]

            sp_data_well = [0, i, j, -dw_schedule[stress_period][well] / 1000.0 * 86400.0]

            sp_data.append(sp_data_well)

        sp_dict_DW[stress_period] = sp_data

    return sp_dict_DW

def min_wel_sp(rcs, mine_wells_gdf, stress_periods, mine_wells):

    sp_dict_MINE = {}

    for stress_period in stress_periods:

        sp_data = []

        for well in mine_wells:

            i, j = rcs[well]

            sp_data_well = [0, i, j, mine_wells_gdf.Rate[well] / 1000.0 * 86400.0]       # rate is already negative

            sp_data.append(sp_data_well)

        sp_dict_MINE[stress_period] = sp_data

    return sp_dict_MINE

def irr_wel_sp(rcs, irrigation_wells_schedule, stress_periods, irrigation_wells):

    sp_dict_IRR = {}

    for stress_period in stress_periods:

        sp_data = []

        for well in irrigation_wells:

            row, col = rcs[well]
            flux = -irrigation_wells_schedule.Q_schedule[well][stress_period] / 1000.0 * 86400.0

            sp_data_well = [0, row, col, flux]

            sp_data.append(sp_data_well)

        sp_dict_IRR[stress_period] = sp_data

    return sp_dict_IRR

def rch(model_irrcells_gdf, model_rivcells_gdf, model_laucells_gdf, model_citcells_gdf, RCH_irr_df_3M, RCH_riv_df_3M, RCH_lau_df_3M, RCH_cit_df_3M, stress_periods):

    sectores_acuiferos = ['Sector 2','Sector 3','Sector 4','Sector 5','Sector 6']

    # Prepare IRR data
    model_irrcells_rows = np.zeros((len(model_irrcells_gdf)), dtype='int')
    model_irrcells_cols = np.zeros((len(model_irrcells_gdf)), dtype='int')
    rch_irr_3m = np.zeros((len(sectores_acuiferos),len(stress_periods)))

    for i in range(len(model_irrcells_gdf)):
        model_irrcells_rows[i] = int(model_irrcells_gdf['row'][i])
        model_irrcells_cols[i] = int(model_irrcells_gdf['column'][i])
    for i in range(len(sectores_acuiferos)):
        for j in range(len(stress_periods)):
            rch_irr_3m[i][j] = RCH_irr_df_3M[sectores_acuiferos[i]][stress_periods[j]]

    # Prepare RIV data
    model_rivcells_rows = np.zeros((len(model_rivcells_gdf)), dtype='int')
    model_rivcells_cols = np.zeros((len(model_rivcells_gdf)), dtype='int')
    rch_riv_3m = np.zeros((len(sectores_acuiferos),len(stress_periods)))

    for i in range(len(model_rivcells_gdf)):
        model_rivcells_rows[i] = int(model_rivcells_gdf['row'][i])
        model_rivcells_cols[i] = int(model_rivcells_gdf['column'][i])
    for i in range(len(sectores_acuiferos)):
        for j in range(len(stress_periods)):
            rch_riv_3m[i][j] = RCH_riv_df_3M[sectores_acuiferos[i]][stress_periods[j]]

    # Preare LAU data
    model_laucells_rows = np.zeros((len(model_laucells_gdf)), dtype='int')
    model_laucells_cols = np.zeros((len(model_laucells_gdf)), dtype='int')
    rch_lau_3m = np.zeros((len(stress_periods)))

    for i in range(len(model_laucells_gdf)):
        model_laucells_rows[i] = int(model_laucells_gdf['row'][i])
        model_laucells_cols[i] = int(model_laucells_gdf['column'][i])
    for i in range(len(stress_periods)):
        rch_lau_3m[i] = RCH_lau_df_3M['Q_InfiltracionLautaro'][stress_periods[i]]

    # Prepare CIT data
    model_citcells_rows = np.zeros((len(model_citcells_gdf)), dtype='int')
    model_citcells_cols = np.zeros((len(model_citcells_gdf)), dtype='int')
    rch_cit_3m = np.zeros((len(stress_periods)))

    for i in range(len(model_citcells_gdf)):
        model_citcells_rows[i] = int(model_citcells_gdf['row'][i])
        model_citcells_cols[i] = int(model_citcells_gdf['column'][i])
    for i in range(len(stress_periods)):
        rch_cit_3m[i] = RCH_cit_df_3M['Perdidas'][stress_periods[i]]

    def rch_inner(model_irrcells_rows, model_irrcells_cols, rch_irr_3m,
                  model_rivcells_rows, model_rivcells_cols, rch_riv_3m,
                  model_laucells_rows, model_laucells_cols, rch_lau_3m,
                  model_citcells_rows, model_citcells_cols, rch_cit_3m,
                  stress_periods):

        rch = {}

        for stress_period in range(len(stress_periods)):

            sp_array_irr = np.zeros((520,510),dtype='float')
            sp_array_riv = np.zeros((520,510),dtype='float')
            sp_array_lau = np.zeros((520,510),dtype='float')
            sp_array_cit = np.zeros((520,510),dtype='float')

            for lau_cell in range(len(model_laucells_rows)):

                row_lau = model_laucells_rows[lau_cell]
                col_lau = model_laucells_cols[lau_cell]
                flux_lau = rch_lau_3m[stress_period] / 1000.0 * 86400.0 / 200.0 / 200.0 / 43.0
                sp_array_lau[row_lau - 1][col_lau - 1] = flux_lau

            for cit_cell in range(len(model_citcells_rows)):

                row_cit = model_citcells_rows[cit_cell]
                col_cit = model_citcells_cols[cit_cell]
                flux_city = rch_cit_3m[stress_period] / 1000.0 * 86400.0 / 200.0 / 200.0 / 590.0
                sp_array_cit[row_cit - 1][col_cit - 1] = round(flux_city, 4)

            for sector_acuifero in range(5):

                if sector_acuifero == 0: # 'Sector 2'
                    n_rch_cells_irr = 927
                    n_rch_cells_riv = 165

                if sector_acuifero == 1: # 'Sector 3'
                    n_rch_cells_irr = 1568
                    n_rch_cells_riv = 253

                if sector_acuifero == 2: # 'Sector 4'
                    n_rch_cells_irr = 519
                    n_rch_cells_riv = 140

                if sector_acuifero == 3: # 'Sector 5'
                    n_rch_cells_irr = 940
                    n_rch_cells_riv = 94

                if sector_acuifero == 4: # 'Sector 6'
                    n_rch_cells_irr = 878
                    n_rch_cells_riv = 287

                for irr_cell in range(len(model_irrcells_rows)):
                    row_irr = model_irrcells_rows[irr_cell]
                    col_irr = model_irrcells_cols[irr_cell]
                    flux_irr = rch_irr_3m[sector_acuifero][stress_period] / 1000.0 * 86400.0 / 200.0 / 200.0 / n_rch_cells_irr
                    sp_array_irr[row_irr - 1][col_irr - 1] = flux_irr

                for riv_cell in range(len(model_rivcells_rows)):
                    row_riv = model_rivcells_rows[riv_cell]
                    col_riv = model_rivcells_cols[riv_cell]
                    flux_riv = rch_riv_3m[sector_acuifero][stress_period] / 1000.0 * 86400.0 / 200.0 / 200.0 / n_rch_cells_riv
                    sp_array_riv[row_riv - 1][col_riv - 1] = flux_riv

            rch[stress_periods[stress_period]] = sp_array_irr + sp_array_riv + sp_array_lau # + sp_array_cit

        return rch

    result = rch_inner(model_irrcells_rows, model_irrcells_cols, rch_irr_3m,
                       model_rivcells_rows, model_rivcells_cols, rch_riv_3m,
                       model_laucells_rows, model_laucells_cols, rch_lau_3m,
                       model_citcells_rows, model_citcells_cols, rch_cit_3m,
                       stress_periods)
    return result
