import os
import pickle

import read_results as res

if __name__ == '__main__':

    # set path to your workspace here
    workspace = os.path.join("D:\\", "tbl-cwe", "Simulation", "TABS_30_Panel_TABS_alpha_neu")
    print("Your workspace is set to: " + workspace)

    load_pickle = os.path.join(workspace, "building_simulation_pickle.p")
    pickle_prj = pickle.load(open(load_pickle, "rb"))

    output_path = os.path.join(workspace, "calc_results")
    print("Your calculation results are stored in: " + output_path)

    plot_path = os.path.join(workspace, "plots")
    print("Your plots are stored in: " + plot_path)

    csv_results_path = os.path.join(workspace, "csv_results", )
    print("Your .csv  files are stored in: " + csv_results_path)

    print("##########")
    res.calc_results(
        buildings=pickle_prj.buildings,
        csv_path=csv_results_path,
        output_path=output_path)
    
    print("##########")
    res.plot_results(
        buildings=pickle_prj.buildings,
        csv_path=csv_results_path,
        output_path=plot_path)
    
    print("##########")
    res.excel_export(
        buildings=pickle_prj.buildings,
        csv_path=csv_results_path,
        output_path=output_path)

    print("##########")
    res.boxplot_results(
        buildings=pickle_prj.buildings,
        csv_path=csv_results_path,
        output_path=plot_path)