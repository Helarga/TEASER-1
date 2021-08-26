import datetime
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
#plt.style.use(os.path.join("D:\\", "tbl-cwe", "Repos", "TEASER", "teaser", "examples", "utils", "ebc.paper.mplstyle"))
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from matplotlib.ticker import FormatStrFormatter
import seaborn as sns
import pandas as pd
import locale
locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
from scipy.interpolate import make_interp_spline, BSpline
from scipy.interpolate import interp1d

from statistics import mean
from dymola.dymola_interface import DymolaInterface

# rcParams
sitewidth = 6.224
fontsize = 11
font = {'family': 'serif',
        'weight': 'normal',
        'size': fontsize}
params = {'legend.fontsize': fontsize,
          'xtick.labelsize': fontsize,
          'ytick.labelsize': fontsize,
          'axes.labelsize': fontsize,
          'axes.titlesize': fontsize,
          'axes.grid.axis': 'y',
          'axes.grid': True,
          'grid.color': '#DDDDDD',
          'figure.figsize': (sitewidth, sitewidth / 16 * 9),
          'figure.subplot.hspace': 0.3,
          'axes.ymargin': 0.1,
          'mathtext.default': "rm"
          }
matplotlib.rc('font', **font)
matplotlib.rcParams.update(params)

# parameters for axis definition
months_locator = mdates.MonthLocator(
    bymonth=None,
    bymonthday=15,
    interval=1,
    tz=None)
allmonths = mdates.MonthLocator()
months_formatter = mdates.DateFormatter("%b")

minor_days = mdates.DayLocator(interval=1)
major_days = mdates.DayLocator(interval=5)
minormonths = mdates.MonthLocator(interval=1)
majormonths = mdates.MonthLocator(interval=2)
format = mdates.DateFormatter("%d. %b")
locator = matplotlib.dates.MonthLocator(
    bymonth=None,
    bymonthday=15,
    interval=1,
    tz=None)

def read_bldg(bldg_name, bldg_area, csv_results):
    building1_name = bldg_name
    bldg1_area = bldg_area
    temp_data1 = pd.read_csv(os.path.join(csv_results, building1_name + "_temp.csv"), index_col=0)
    heat_data1 = pd.read_csv(os.path.join(csv_results, building1_name + "_heat.csv"), index_col=0)
    cool_data1 = pd.read_csv(os.path.join(csv_results, building1_name + "_cool.csv"), index_col=0)

    data1 = pd.DataFrame(
        index=pd.date_range(
            start=datetime.datetime(2021, 1, 1, 0, 0, 0),
            end=datetime.datetime(2021, 12, 31, 23, 55),
            freq="H", ),
        columns=["Wärmeleistung", "Kälteleistung", "Tope", "Tair", "Trad", "Wärmeverlust"], )

    # data building1
    # divide demands by 1000 to get kW
    data1.loc[:, "Wärmeleistung"] = heat_data1.loc[:, building1_name + " PHeat"].values / 1000
    data1.loc[:, "Kälteleistung"] = -cool_data1.loc[:, building1_name + " PCool"].values / 1000
    #data1.loc[:, "Wärmeverlust"] = heat_data1.loc[:, building1_name + " extWall.Q_flow"].values / 1000

    if "Office" in building1_name:
        data1.loc[:, "Tope"] = ((temp_data1.loc[:, building1_name + " TOpe[1]"].values * 0.5 * bldg1_area
                                 + temp_data1.loc[:, building1_name + " TOpe[2]"].values * 0.25 * bldg1_area
                                 + temp_data1.loc[:, building1_name + " TOpe[3]"].values * 0.15 * bldg1_area
                                 + temp_data1.loc[:, building1_name + " TOpe[4]"].values * 0.04 * bldg1_area
                                 + temp_data1.loc[:, building1_name + " TOpe[5]"].values * 0.04 * bldg1_area
                                 + temp_data1.loc[:, building1_name + " TOpe[6]"].values * 0.02 * bldg1_area)
                                / bldg1_area) - 273.15
        data1.loc[:, "Tair"] = ((temp_data1.loc[:, building1_name + " TAir[1]"].values * 0.5 * bldg1_area
                                 + temp_data1.loc[:, building1_name + " TAir[2]"].values * 0.25 * bldg1_area
                                 + temp_data1.loc[:, building1_name + " TAir[3]"].values * 0.15 * bldg1_area
                                 + temp_data1.loc[:, building1_name + " TAir[4]"].values * 0.04 * bldg1_area
                                 + temp_data1.loc[:, building1_name + " TAir[5]"].values * 0.04 * bldg1_area
                                 + temp_data1.loc[:, building1_name + " TAir[6]"].values * 0.02 * bldg1_area)
                                / bldg1_area) - 273.15
        data1.loc[:, "Trad"] = ((temp_data1.loc[:, building1_name + " TRad[1]"].values * 0.5 * bldg1_area
                                 + temp_data1.loc[:, building1_name + " TRad[2]"].values * 0.25 * bldg1_area
                                 + temp_data1.loc[:, building1_name + " TRad[3]"].values * 0.15 * bldg1_area
                                 + temp_data1.loc[:, building1_name + " TRad[4]"].values * 0.04 * bldg1_area
                                 + temp_data1.loc[:, building1_name + " TRad[5]"].values * 0.04 * bldg1_area
                                 + temp_data1.loc[:, building1_name + " TRad[6]"].values * 0.02 * bldg1_area)
                                / bldg1_area) - 273.15
    else:
        data1.loc[:, "Tope"] = temp_data1.loc[:, building1_name + " TOpe"].values - 273.15
        data1.loc[:, "Tair"] = temp_data1.loc[:, building1_name + " TAir"].values - 273.15
        data1.loc[:, "Trad"] = temp_data1.loc[:, building1_name + " TRad"].values - 273.15

    if "tabsplusair" in building1_name:
        data1.loc[:, "tabs_heat_demand"] = heat_data1.loc[:, building1_name + " tabsHeatingPower"].values / 1000
        data1.loc[:, "tabs_cool_demand"] = -cool_data1.loc[:, building1_name + " tabsCoolingPower"].values / 1000
        data1.loc[:, "convective_heat_demand"] = heat_data1.loc[:, building1_name + " pITempHeatRem.y"].values / 1000
        data1.loc[:, "convective_cool_demand"] = -cool_data1.loc[:, building1_name + " pITempCoolRem.y"].values / 1000

    return data1

def plot_compare_bldgs(building1, building2, output_path):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    # plot the indoor temperature and heating/cooling demand for one year in two subplots
    # print("plotting building {}".format(building1))
    fig, (ax1, ax2) = plt.subplots(2)
    ax1.plot(building1.loc[:, "Tope"], linewidth=0.5, color="black")
    ax1.plot(building2.loc[:, "Tope"], linewidth=0.5, color="green")
    # ax1.set_title("Operative Temperatur")
    ax1.set_ylabel('Temperatur [°C]')
    ax1.set_ylim([20, 25])
    ax1.set_xlim(datetime.datetime(2021, 3, 1, 0, 0, 0), datetime.datetime(2021, 3, 31, 23, 55))
    ax1.yaxis.set_major_locator(mticker.MultipleLocator(2))
    ax1.yaxis.set_minor_locator(mticker.MultipleLocator(1))
    ax1.margins(0)
    # ax1.axvspan(datetime.datetime(2021, 4, 1, 0, 0, 0), datetime.datetime(2021, 4, 30, 23, 55), facecolor='#EDEDED')
    #ax1.xaxis.set_major_locator(allmonths)
    #ax1.xaxis.set_minor_locator(months_locator)
    #ax1.xaxis.set_major_formatter(mticker.NullFormatter())
    #ax1.xaxis.set_minor_formatter(months_formatter)
    #ax1.tick_params(axis="x", which="minor", length=0)
    ax1.xaxis.set_major_locator(major_days)
    ax1.xaxis.set_minor_locator(minor_days)
    ax1.xaxis.set_major_formatter(format)


    ax2.plot(building1.loc[:, "Wärmeleistung"], linewidth=0.5, label="Konvektiv", color="black")
    #ax2.plot(-building1.loc[:, "Kälteleistung"].resample('D').mean(), linewidth=0.5, label="Kühlleistung", color="b")
    ax2.plot(building2.loc[:, "Wärmeleistung"], linewidth=0.5, label="TABS + Konvektiv", color="green")
    #ax2.plot(-building2.loc[:, "Kälteleistung"].resample('D').mean(), linewidth=0.5, label="Kühlleistung", color="black")
    # ax2.set_title("Heiz- und Kühllast")
    ax2.set_ylabel('Leistung [kW]')
    ax2.set_ylim([0.0, 45.0])
    ax2.set_xlim(datetime.datetime(2021, 3, 1, 0, 0, 0), datetime.datetime(2021, 3, 31, 23, 55))
    # ax2.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
    # ax2.yaxis.set_major_locator(mticker.AutoLocator())
    # ax2.yaxis.set_minor_locator(mticker.AutoMinorLocator())
    ax2.yaxis.set_major_locator(mticker.MultipleLocator(20))
    ax2.yaxis.set_minor_locator(mticker.MultipleLocator(10))
    ax2.margins(0)
    # ax2.axvspan(datetime.datetime(2021, 4, 1, 0, 0, 0), datetime.datetime(2021, 4, 30, 23, 55),facecolor='#EDEDED')
    #ax2.xaxis.set_major_locator(allmonths)
    #ax2.xaxis.set_minor_locator(months_locator)
    #ax2.xaxis.set_major_formatter(mticker.NullFormatter())
    #ax2.xaxis.set_minor_formatter(months_formatter)
    #ax2.tick_params(axis="x", which="minor", length=0)
    ax2.xaxis.set_major_locator(major_days)
    ax2.xaxis.set_minor_locator(minor_days)
    ax2.xaxis.set_major_formatter(format)

    fig.legend(loc=9, bbox_to_anchor=(0.5, 0.98,), ncol=2, fontsize="small")
    # bbox_to_anchor=(0.5, 1.06,), ncol=1
    # plt.tight_layout()
    plt.savefig(os.path.join(output_path, "zoom_bldgs" + "_plot.pdf"), dpi=200, bbox_inches="tight")

def load_duration_curve(building1, building2, building3, building4, output_path):
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    load1 = building1.loc[:, "Wärmeleistung"].sort_values(ascending=False)
    load2 = building2.loc[:, "Wärmeleistung"].sort_values(ascending=False)
    load3 = building3.loc[:, "Wärmeleistung"].sort_values(ascending=False)
    load4 = building4.loc[:, "Wärmeleistung"].sort_values(ascending=False)
    load1.index = pd.Index(range(1, 8761, 1))
    load2.index = pd.Index(range(1, 8761, 1))
    load3.index = pd.Index(range(1, 8761, 1))
    load4.index = pd.Index(range(1, 8761, 1))

    fig, ax = plt.subplots()
    ax.plot(load1, linewidth=0.5, color="black", label="Konvektiv")
    ax.plot(load2, linewidth=0.5, color="blue", label="Radiator")
    ax.plot(load4, linewidth=0.5, color="red", label="TABS + Konvektiv")
    ax.plot(load3, linewidth=0.5, color="green", label="FT FO")

    ax.set_ylabel('Leistung [kW]')
    ax.set_xlabel('Stunden [h]')
    ax.set_xlim([-25.0, 5000.0])
    ax.margins(0.01)
    plt.tight_layout()

    ax.legend(loc="best", ncol=2)
    # bbox_to_anchor = (0.5, 1.05,)

    plt.savefig(os.path.join(output_path, "_load_duration_curve" + "_plot.pdf"), dpi=200, bbox_inches="tight")

def plot_year_charts(building, bldg_name, output_path):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    fig, (ax1, ax2) = plt.subplots(2)
    ax1.plot(building.loc[:, "Tope"], linewidth=0.5, color="black", label="Operative Temperatur")
    #ax1.plot(building.loc[:, "Tair"].resample('D').mean(), linewidth=0.5, color="blue", label="Lufttemperatur")
    #x1.plot(building.loc[:, "Trad"].resample('D').mean(), linewidth=0.5, color="red", label="Strahlungstemperatur")
    ax1.set_ylabel('Temperatur [°C]')
    ax1.set_ylim([19, 27])
    #17, 28]) 20 27
    ax1.yaxis.set_major_locator(mticker.MultipleLocator(5))
    ax1.yaxis.set_minor_locator(mticker.MultipleLocator(2.5))
    ax1.margins(0)
    #ax1.axvspan(datetime.datetime(2021, 2, 7, 23, 55), datetime.datetime(2021, 2, 15, 0, 0, 0), facecolor='#EDEDED')
    #ax1.axvspan(datetime.datetime(2021, 8, 8, 23, 55), datetime.datetime(2021, 8, 16, 0, 0, 0), facecolor='#EDEDED')
    ax1.xaxis.set_major_locator(allmonths)
    ax1.xaxis.set_minor_locator(months_locator)
    ax1.xaxis.set_major_formatter(mticker.NullFormatter())
    #ax1.xaxis.set_minor_formatter(months_formatter)
    ax1.tick_params(axis="x", which="minor", length=0)
    ax1.legend(loc="upper left", fontsize="x-small",  frameon=True, edgecolor="white")
    #.resample('D').mean()
    ax2.plot(building.loc[:, "Wärmeleistung"], linewidth=0.5, label="Heizleistung", color="r")
    ax2.plot(-building.loc[:, "Kälteleistung"], linewidth=0.5, label="Kühlleistung", color="b")
    ax2.set_ylabel('Leistung [kW]')
    ax2.set_ylim([0.0, 45.0])
    ax2.yaxis.set_major_locator(mticker.MultipleLocator(20))
    ax2.yaxis.set_minor_locator(mticker.MultipleLocator(10))
    #20 10
    ax2.margins(0)
    #ax2.axvspan(datetime.datetime(2021, 2, 7, 23, 55), datetime.datetime(2021, 2, 15, 0, 0, 0), facecolor='#EDEDED')
    #ax2.axvspan(datetime.datetime(2021, 8, 8, 23, 55), datetime.datetime(2021, 8, 16, 0, 0, 0), facecolor='#EDEDED')
    ax2.xaxis.set_major_locator(allmonths)
    ax2.xaxis.set_minor_locator(months_locator)
    ax2.xaxis.set_major_formatter(mticker.NullFormatter())
    ax2.xaxis.set_minor_formatter(months_formatter)
    ax2.tick_params(axis="x", which="minor", length=0)
    ax2.legend(loc="upper left", fontsize="x-small", frameon=True, edgecolor="white", ncol=2)

    #fig.suptitle("30 % TABS, 70 % Zusatzsystem", fontsize="small", y=0.93)
    plt.savefig(os.path.join(output_path, bldg_name + "_plot.pdf"), dpi=200, bbox_inches="tight")
    #_H .resample('D').mean()
    # clear plot lines, keep axes
    for artist in ax1.lines + ax1.collections + ax2.lines + ax2.collections:
        artist.remove()
    """
    # plot only week in February
    fig, (ax3, ax4) = plt.subplots(2)
    ax3.plot(building.loc[:, "Tope"], linewidth=0.5, color="black")
    ax3.plot(building.loc[:, "Tair"], linewidth=0.5, color="blue", label="Lufttemperatur")
    ax3.plot(building.loc[:, "Trad"], linewidth=0.5, color="red", label="Strahlungstemperatur")
    ax3.set_ylabel('Temperatur [°C]')
    ax3.set_ylim([19, 23])
    ax3.set_xlim(datetime.datetime(2021, 2, 7, 23, 55), datetime.datetime(2021, 2, 15, 0, 0, 0))
    ax3.margins(0)
    ax3.grid(True)
    # ax3.axvspan(datetime.datetime(2021, 4, 1, 0, 0, 0), datetime.datetime(2021, 4, 30, 23, 55),facecolor='#EDEDED')
    ax3.yaxis.set_major_locator(mticker.MultipleLocator(1))
    ax3.yaxis.set_minor_locator(mticker.MultipleLocator(1))
    ax3.xaxis.set_minor_locator(minor_days)
    ax3.xaxis.set_major_locator(minor_days)
    ax3.xaxis.set_major_formatter(format)
    ax3.legend(loc="best", fontsize="x-small", frameon=True, edgecolor="white")

    ax4.plot(building.loc[:, "Wärmeleistung"], linewidth=0.5, color="r", label="Heizleistung")
    ax4.plot(-building.loc[:, "Kälteleistung"], linewidth=0.5, color="b", label="Kühlleistung")
    # ax4.set_title("Heiz- und Kühllast")
    ax4.set_ylabel('Leistung [kW]')
    ax4.set_ylim([0.0, 45.0])
    ax4.set_xlim(datetime.datetime(2021, 2, 7, 23, 55), datetime.datetime(2021, 2, 15, 0, 0, 0))
    ax4.yaxis.set_major_locator(mticker.MultipleLocator(20))
    ax4.yaxis.set_minor_locator(mticker.MultipleLocator(10))
    ax4.xaxis.set_minor_locator(minor_days)
    ax4.xaxis.set_major_locator(minor_days)
    ax4.xaxis.set_major_formatter(format)
    ax4.margins(0)
    ax4.grid(True)
    # ax4.axvspan(datetime.datetime(2021, 4, 1, 0, 0, 0), datetime.datetime(2021, 4, 30, 23, 55),facecolor='#EDEDED')

    plt.savefig(os.path.join(output_path, bldg_name + "_feb_plot.pdf"), dpi=200, bbox_inches="tight")


    # plot only week in August
    ax3.yaxis.set_major_locator(mticker.MultipleLocator(5))
    ax3.set_ylim([18, 32])
    ax3.set_xlim(datetime.datetime(2021, 8, 8, 23, 55), datetime.datetime(2021, 8, 16, 0, 0, 0))
    ax4.set_xlim(datetime.datetime(2021, 8, 8, 23, 55), datetime.datetime(2021, 8, 16, 0, 0, 0))

    plt.savefig(os.path.join(output_path, bldg_name + "_aug_plot.pdf"), dpi=200, bbox_inches="tight")
    """

def plot_bar_charts(building1, building2, building3, building4, name1, name2, name3, name4, output_path):
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    sum1 = building1.loc[:, "Wärmeleistung"].sum() / 1000
    sum2 = building2.loc[:, "Wärmeleistung"].sum() / 1000
    sum3 = building3.loc[:, "Wärmeleistung"].sum() / 1000
    sum4 = building4.loc[:, "Wärmeleistung"].sum() / 1000

    X = np.arange(4)

    fig, ax = plt.subplots()
    ax.bar(X + 0.00, sum1)
    ax.bar(X + 0.25, sum2)
    ax.bar(X + 0.50, sum3)
    ax.bar(X + 0.75, sum4)

    plt.savefig(os.path.join(output_path, "_bar_plot.pdf"), dpi=200, bbox_inches="tight")

def plot_heat_loss(building1, building2, output_path):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    #.resample('D').mean()
    fig, (ax1, ax2) = plt.subplots(2)
    ax1.plot(building1.loc[:, "Tope"], linewidth=0.5, color="black")
    ax1.plot(building2.loc[:, "Tope"], linewidth=0.5, color="green")
    ax1.set_ylabel('Temperatur [°C]')
    ax1.set_ylim([20, 27])
    ax1.set_xlim(datetime.datetime(2021, 6, 19, 0, 0, 0), datetime.datetime(2021, 7, 19, 0, 0, 0))
    ax1.yaxis.set_major_locator(mticker.MultipleLocator(2))
    ax1.yaxis.set_minor_locator(mticker.MultipleLocator(1))
    ax1.margins(0)
    # ax1.axvspan(datetime.datetime(2021, 4, 1, 0, 0, 0), datetime.datetime(2021, 4, 30, 23, 55), facecolor='#EDEDED')
    ax1.xaxis.set_major_locator(major_days)
    ax1.xaxis.set_minor_locator(minor_days)
    ax1.xaxis.set_major_formatter(format)
    #ax1.xaxis.set_minor_formatter(months_formatter)
    #ax1.tick_params(axis="x", which="minor", length=0)

    ax2.plot(building1.loc[:, "Wärmeverlust"], linewidth=0.5, label="Konvektiv", color="black")
    ax2.plot(building2.loc[:, "Wärmeverlust"], linewidth=0.5, label="Flächentemperierung",
             color="green")
    # ax2.set_title("Heiz- und Kühllast")
    ax2.set_ylabel('Wärmestrom \nAußenwand [kW]')
    ax2.set_ylim([-15.0, 10.0])
    ax2.set_xlim(datetime.datetime(2021, 6, 19, 0, 0, 0), datetime.datetime(2021, 7, 19, 0, 0, 0))
    # ax2.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
    # ax2.yaxis.set_major_locator(mticker.AutoLocator())
    # ax2.yaxis.set_minor_locator(mticker.AutoMinorLocator())
    #ax2.yaxis.set_major_locator(mticker.MultipleLocator(20))
    ax2.yaxis.set_minor_locator(mticker.MultipleLocator(5))
    #ax2.margins(0)
    # ax2.axvspan(datetime.datetime(2021, 4, 1, 0, 0, 0), datetime.datetime(2021, 4, 30, 23, 55),facecolor='#EDEDED')
    ax2.xaxis.set_major_locator(major_days)
    ax2.xaxis.set_minor_locator(minor_days)
    ax2.xaxis.set_major_formatter(format)
    #ax2.xaxis.set_minor_formatter(months_formatter)
    #ax2.tick_params(axis="x", which="minor", length=0)

    fig.align_ylabels()
    fig.legend(loc=9, bbox_to_anchor=(0.5, 1.0,), ncol=2)
    # bbox_to_anchor=(0.5, 1.06,), ncol=1
    # plt.tight_layout()
    plt.savefig(os.path.join(output_path, "heat_loss" + "_plot.pdf"), dpi=200, bbox_inches="tight")

def boxplot_max_power_charts(building1, building2, building3, building4, name1, name2, name3, name4, output_path):
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    data = pd.DataFrame(columns=["Konvektiv", "Radiator", "FT FO", "TABS + Konvektiv"])
    data2 = pd.DataFrame()
    data3 = pd.DataFrame()
    data4 = pd.DataFrame()

    # resample data to daily mean values and filter out top "x" values
    data.loc[:, "Konvektiv"] = building1.loc[:, "Wärmeleistung"].resample('D').max().nlargest(100, keep='all')
    data2.loc[:, "Radiator"] = building2.loc[:, "Wärmeleistung"].resample('D').max().nlargest(100, keep='all')
    data3.loc[:, "FT FO"] = building3.loc[:, "Wärmeleistung"].resample('D').max().nlargest(100, keep='all')
    data4.loc[:, "TABS + Konvektiv"] = building4.loc[:, "Wärmeleistung"].resample('D').max().nlargest(100, keep='all')

    data.reset_index(drop=True, inplace=True)
    data2.reset_index(drop=True, inplace=True)
    data3.reset_index(drop=True, inplace=True)
    data4.reset_index(drop=True, inplace=True)

    data.loc[:, "Radiator"] = data2.loc[:, "Radiator"]
    data.loc[:, "FT FO"] = data3.loc[:, "FT FO"]
    data.loc[:, "TABS + Konvektiv"] = data4.loc[:, "TABS + Konvektiv"]
    #d_resample_spec_heat = data.loc[:, "Spez Wärmeleistung"].resample('D').max().nlargest(50, keep='all')


    # drop datetime index

    #d_resample_spec_heat.reset_index(drop=True, inplace=True)


    fig, ax = plt.subplots()
    #data.plot(kind='box', xlabel=["Konvektiv", "Radiator", "FT FO", "TABS + Konvektiv"], ylabel="Spitzenlast [kW]")
    #ax = sns.boxplot(data=data)
    ax.boxplot(data, labels=data.columns)
    #ax.boxplot(data.loc[:, name2], labels=["Rad"])
    #ax.set_title("EFH 1990 100 $m^2$")
    ax.set_ylabel(r"Spitzenlast [$W/m^2$]")
    #ax.set_ylim([24, 46])
    #plt.tight_layout()
    plt.savefig(os.path.join(output_path, "Ref_boxplot.pdf"), dpi=200)
    """ax.clear()
    ax.boxplot(d_resample_heat_EFH_1990_200, labels=d_resample_heat_EFH_1990_200.columns)
    ax.set_title("EFH 1990 200 $m^2$")
    ax.set_ylabel("Max Heat [kW]")
    plt.tight_layout()
    plt.savefig(os.path.join(boxplot_path, "EFH_1990_200_boxplot.pdf"), dpi=200)"""

if __name__ == '__main__':
    # set path to your workspace here
    workspace = os.path.join("D:\\", "tbl-cwe", "Final_Simulations", "Complete_17_08_TABS_plow5_HC_Tl_0")
    print("Your workspace is set to: " + workspace)
    # set path to your csv_results here
    csv_results_path = os.path.join(workspace, "csv_results")

    output_path4 = os.path.join(workspace, "Plots_Kap_4")
    output_path3 = os.path.join(workspace, "Plots_Kap_3_TABS")
    print("Your plots are stored in: " + output_path4)

    bldg1_name = "MFHconvective2010light1000"
    bldg2_name = "MFHradiator2010light1000"
    bldg3_name = "MFHpanel2010light1000"
    bldg4_name = "MFHtabsplusair2010light1000"

    bldg1 = read_bldg(bldg1_name, 1000, csv_results=csv_results_path)
    bldg2 = read_bldg(bldg2_name, 1000, csv_results=csv_results_path)
    bldg3 = read_bldg(bldg3_name, 1000, csv_results=csv_results_path)
    bldg4 = read_bldg(bldg4_name, 1000, csv_results=csv_results_path)

    #plot_heat_loss(bldg1, bldg2, output_path4)

    #plot_compare_bldgs(bldg1, bldg2, output_path4)

    load_duration_curve(bldg1, bldg2, bldg3, bldg4, output_path=output_path4)

    # ax1.set_ylim([18, 32])
    # ax1.set_ylim([20, 27])

    #plot_year_charts(bldg1, bldg1_name, output_path3)
    #plot_year_charts(bldg2, bldg2_name, output_path3)
    #plot_year_charts(bldg3, bldg3_name, output_path3)
    #plot_year_charts(bldg4, bldg4_name, output_path4)

    boxplot_max_power_charts(bldg1, bldg2, bldg3, bldg4, bldg1_name, bldg2_name, bldg3_name, bldg4_name, output_path4)

    #plot_bar_charts(bldg1, bldg2, bldg3, bldg4, bldg1_name, bldg2_name, bldg3_name, bldg4_name, output_path4)