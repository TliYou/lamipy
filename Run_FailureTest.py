"""
    lamipy project - laminated composites calculations in Python.

    Run_FailureTest.py - Module containing functions for testing 
    composite layups.

    Joao Paulo Bernhardt - September 2017
"""

import numpy as np
import CLT
import Failure_Criteria as FC
#import plotresults as plotr
#import plotresults_class as plotr
from plotresults import PlotResults

def TestA():
# This temporary function tests the implementation.
    
    # Material 1 - Dictionary of properties
    #              All units are in Pa (N/m2)
    mat1 = {
     "E1"  : 69e9,       
     "E2"  : 6e9,       
     "n12" : 0.354,         
     "G12" : 3e9,       
     "Xt" : 47e6,         
     "Xc" : 14e6,
     "Yt" : 24e6,
     "Yc" : 18e6,
     "S12" : 75e6,
     "S32" : 41e6,
     "a1" : 2.1e-6,
     "a2" : 2.1e-6}

    # Assembles material list
    mat = [mat1, []]

    # Initializes dictionary of the laminate layup configurations
    # thk is thickness; ang is angle; mat_id is material id
    lam = {"thk": [], "ang": [], "mat_id" : []}

    # Adds 12 layers of 0.127mm thickness and material id 0
    for i in range(12):
        lam["thk"].append(0.127e-3)
        lam["mat_id"].append(0)
    #lam["ang"].extend((45, -45, 45, -45, 45, -45, -45, 45, -45, 45, -45, 45))
    #lam["ang"].extend((0, 30, -30, 30, -30, 90, 90, -30, 30, -30, 30, 0))
    #lam["ang"].extend((0, 0, 0, 0, 90, 90, 90, 90, 0, 0, 0, 0))
    #lam["ang"].extend((0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
    lam["ang"].extend((45, -45, 0, 90, 0, 90, 90, 0, 90, 0, -45, 45))

    # Vector F with the applied generalized stress (unit N/m / N.m/m)
    F = np.array([  0e2,   # Nx
                    1e2,   # Ny
                    0e4,   # Nxy
                    0e0,   # Mx
                    0e1,   # My
                    0])   # Mxy

    # Temperature variation (degrees)
    delta_T = -60 

    # Calculates stresses and strains based on CLT.
    # res = calculated results holder;
    # LCS = Laminate System; MCS = Material Coordinate System; 
    # inf = inferior; sup = superior.
    res = CLT.calc_stressCLT(mat, lam, F, None, delta_T)

    sfTsaiWu    = FC.tsaiwu_2D(   mat, 
                                  lam, 
                                  res["MCS"]["stress"]["inf"],
                                  res["MCS"]["stress"]["sup"])
    
    sfMaxStress = FC.maxstress_2D(mat, 
                                  lam, 
                                  res["MCS"]["stress"]["inf"], 
                                  res["MCS"]["stress"]["sup"])
    
    sfMaxStrain = FC.maxstrain_2D(mat, 
                                  lam, 
                                  res["MCS"]["strain"]["inf"], 
                                  res["MCS"]["strain"]["sup"])

    sfHashin = FC.hashin_2D(      mat, 
                                  lam, 
                                  res["MCS"]["stress"]["inf"], 
                                  res["MCS"]["stress"]["sup"])

    ProgressiveFailureTest(mat, lam, F, delta_T)

    pass

def ProgressiveFailureTest(mat, lam, F, dT):
# Progressive failure analysis function. Loops through CLT and
# failure criteria in order to catch failed layers, which are then
# discounted (Ply Discount Method).

    # Gets number of layers
    num = len(lam["ang"])
    
    # Holds the analysis data through the loops
    fail_status =  {"Failed?" : [False] * num, 
                    "Mode" : [""] * num,
                    "Load Factor" : [0] * num}
    failed_count = [0, 0]

    # Load factor control
    LF = 1.00       # Load factor
    LS = 1.02       # Load step multiplier
    
    # Holds results data (in order to plot later)
    plot_data = []

    # Main Load Factor loop (increases when there's no new failure)
    while failed_count[0] < num:

        # Sends for CLT calculations
        res = CLT.calc_stressCLT(mat, lam, F*LF, fail_status["Mode"], dT)

        # Prepares data pair for entry, then appends data.
        data_pair = [LF, res]
        #plot_data = np.concatenate((plot_data, data_pair))
        plot_data.append(data_pair)

        # Sends for SF calculations
        SF_list = FC.tsaiwu_2D(   mat, 
                                  lam, 
                                  res["MCS"]["stress"]["inf"],
                                  res["MCS"]["stress"]["sup"])

        # Loop for layer failure check
        for i in range(num):
            
            # Updates sf values
            sf_inf = SF_list["fs_inf"][i][0]
            sf_sup = SF_list["fs_sup"][i][0]
            sf = min(sf_inf, sf_sup)
            
            # Gets failure mode based on min sf
            if sf == SF_list["fs_inf"][i][0]:
                mode = SF_list["fs_inf"][i][1]
            else:
                mode = SF_list["fs_sup"][i][1]

            # Checks for new failure; saves results
            if sf < 1 and not fail_status["Failed?"][i]:
                fail_status["Failed?"][i] = True
                fail_status["Mode"][i] = mode
                fail_status["Load Factor"][i] = LF
                failed_count[1] = failed_count[1] + 1
                #print("Layer "+str(i)+" has failed. Mode: " + mode)

        # Increases LF if no new failure 
        if failed_count[1] == failed_count[0]:       
            LF = LF*LS        #increases Load Factor by 5%
            #print([int(load) for load in LF*F if load>0])

        failed_count[0] = failed_count[1]

    # Gets FPF and LPF
    fpf = min(fail_status["Load Factor"])
    lpf = max(fail_status["Load Factor"])

    # Prints results
    print("First Ply Failure at LF: " + str(round(fpf)))
    print("Last Ply Failure at LF: " + str(round(lpf)))
    print("LPF / FPF : " + str(round(lpf/fpf, 1)))

    # Sends for plotting
    plot_data = np.array(plot_data)
    plotr = PlotResults(lam, plot_data, fail_status)
    plotr.Options(save=True, display=False)
    plotr.ProgAvgStrain()
    plotr.Profile("MCS", 1, "strain", 0)  
    pass
    

TestA()