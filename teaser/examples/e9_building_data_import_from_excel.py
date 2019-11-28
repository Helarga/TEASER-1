# -*- coding: utf-8 -*-
# @Author: Martin Rätz
# @Date:   2019-02-19 18:41:56
# @Last Modified by: Martin Rätz
# @Last Modified time: 15.10.2019

"""
This script demonstrates how a building can be generated by importing all
data from excel.
An appropriate example file with some building data is imported from
examplefiles/ExcelBuildingData_Sample.xlsx.

In the excel every room is listed by its own, via a self defined zoning
algorithm these rooms are combined to zones.
The user needs to adjust the zoning to his needs.

Limitations and assumptions:
- Outer and inner wall area depend on the calculations done in the excel
- Ground floor area is only as big the respective net area of the heated room
volume (NetArea)
- Floor area is only as big the respective net area of the heated room volume
(NetArea)
- Rooftop area is only as big the respective net area of the heated room
volume (NetArea)
- Rooftops are flat and not tilted, see "RooftopTilt"
- Ceiling area is only as big the respective net area of the heated room
volume (NetArea)
- Ceiling, floor and inner walls are only respected by half their area,
since they belong half to the respective
and half to the adjacent zone
- Orientations are clockwise in degree, 0° is directed north

-respective construction types have to be added to the TypeBuildingElements.json
-respective UsageTypes for Zones have to be added to the UseConditions.json
-excel file format has to be as shown in the "ExcelBuildingData_Sample.xlsx"
-yellowed columns are necessary input to teaser -> don´t change column
header, keep value names consistent.
-non yellowed columns may either not be used or be used for your zoning
algorithm

Information about the required excel format:
#Documentation in progress!
-Under the cell ‚Usage type‘  you will see some cells that are blank but have
their row filled.
It means the blank cell actually belongs to the Usage type above but in that
specific row we filled the characteristics
of the window/wall of a different orientation of the same exact room. That
means every row is either a new room or a
new orientation of that room. A room might have two outerwalls in two
different orientation so for each outer wall,
a an extra row defining the respective orientation is added
-The entries in the excel sheet must be consistent for python being able to
convert it.
-If an inner wall is reaching inside a room but is not the limit of the room,
it should be accounted with 2x the area
"""

import os
from teaser.project import Project
from teaser.logic.buildingobjects.building import Building
from teaser.logic.buildingobjects.thermalzone import ThermalZone
from teaser.logic.buildingobjects.useconditions import UseConditions
from teaser.logic.buildingobjects.buildingphysics.outerwall import OuterWall
from teaser.logic.buildingobjects.buildingphysics.floor import Floor
from teaser.logic.buildingobjects.buildingphysics.rooftop import Rooftop
from teaser.logic.buildingobjects.buildingphysics.groundfloor import GroundFloor
from teaser.logic.buildingobjects.buildingphysics.ceiling import Ceiling
from teaser.logic.buildingobjects.buildingphysics.window import Window
from teaser.logic.buildingobjects.buildingphysics.innerwall import InnerWall
import pandas as pd
import numpy as np
import warnings
import shutil


def import_data(path=None, sheet_names=None):
    """
    Import data from the building data excel file and perform some
    preprocessing for nan and empty cells.
    If several sheets are imported, the data is concatenated to one dataframe

    :param path: path to the excel file that should be imported
    :type path: str
    :param sheet_names: sheets of excel that should be imported
    :type sheet_names: list or str
    :return:
    :rtype:
    """

    # process an import of a single sheet as well as several sheets,
    # which will be concatenated with an continuous index
    if type(sheet_names) == list:
        data = pd.DataFrame()
        _data = pd.read_excel(io=path, sheet_name=sheet_names, header=0, index_col=None)
        for sheet in sheet_names:
            data = data.append(_data[sheet], sort=False)
        data = data.reset_index(drop=False)
        data["index"] = data["index"] + 2  # sync the index with the excel index
    else:
        data = pd.read_excel(io=path, sheet_name=sheet_names, header=0, index_col=0)

    # Cut of leading or tailing white spaces from any string in the dataframe
    data = data.applymap(lambda x: x.strip() if type(x) is str else x)

    # Convert every N/A, nan, empty strings and strings called N/a, n/A, NAN,
    # nan, na, Na, nA or NA to np.nan
    data = data.replace(
        ["", "N/a", "n/A", "NAN", "nan", "na", "Na", "nA", "NA"], np.nan, regex=True
    )
    data = data.fillna(np.nan)

    return data


def get_list_of_present_entries(list_):
    """
    Extracts a list of all in the list available entries, discarding "None"
    and "nan" entries

    :param list_: list of which the entries should be returned
    :type list_: list
    :return:
    :rtype:
    """

    _List = []
    for x in list_:
        if x not in _List:
            if not None:
                if not pd.isna(x):
                    _List.append(x)
    return _List


# Block: Zoning methodologies (define your zoning function here)
# -------------------------------------------------------------
def zoning_example(data):
    """
    This is an example on how the rooms of a building could be aggregated to
    zones.

    In this example the UsageType has to be empty in the case that the
    respective line does not represent another
    room but a different orientated wall or window belonging to a room that
    is already declared once in the excel file.

    :param data: The data which shall be zoned
    :type data: pandas dataframe
    :return: The zoning should return the imported dataset with an additional
    column called "Zone" which inhibits the
    information to which zone the respective room shall be part of.
    :rtype: pandas dataframe
    """

    # account all outer walls not adjacent to the ambient to the entity
    # "inner wall"
    # !right now the wall construction of the added wall is not respected,
    # the same wall construction as regular
    # inner wall is set
    for index, line in data.iterrows():
        if not pd.isna(line["WallAdjacentTo"]):
            data.at[index, "InnerWallArea[m²]"] = (
                data.at[index, "OuterWallArea[m²]"]
                + data.at[index, "WindowArea[m²]"]
                + data.at[index, "InnerWallArea[m²]"]
            )
            data.at[index, "WindowOrientation[°]"] = np.NaN
            data.at[index, "WindowArea[m²]"] = np.NaN
            data.at[index, "WindowConstruction"] = np.NaN
            data.at[index, "OuterWallOrientation[°]"] = np.NaN
            data.at[index, "OuterWallArea[m²]"] = np.NaN
            data.at[index, "OuterWallConstruction"] = np.NaN

    # make all rooms that belong to a certain room have the same room identifier
    _list = []
    for index, line in data.iterrows():
        if pd.isna(line["BelongsToIdentifier"]):
            _list.append(line["RoomIdentifier"])
        else:
            _list.append(line["BelongsToIdentifier"])
    data["RoomCluster"] = _list

    # check for lines in which the net area is zero, marking an second wall
    # or window
    # element for the respective room, and in which there is still stated a
    # UsageType which is wrong
    # and should be changed in the file
    for i, row in data.iterrows():
        if row["NetArea[m²]"] == 0 and not pd.isna(row["UsageType"]):
            warnings.warn(
                "In line %s the net area is zero, marking an second wall or "
                "window element for the respective room, "
                "and in which there is still stated a UsageType which is "
                "wrong and should be changed in the file" % i
            )

    # make all rooms of the cluster having the usage type of the main usage type
    _groups = data.groupby(["RoomCluster"])
    for index, cluster in _groups:
        count = 0
        for line in cluster.iterrows():
            if pd.isna(line[1]["BelongsToIdentifier"]) and not pd.isna(
                line[1]["UsageType"]
            ):
                main_usage = line[1]["UsageType"]
                for i, row in data.iterrows():
                    if row["RoomCluster"] == line[1]["RoomCluster"]:
                        data.at[i, "RoomClusterUsage"] = main_usage
                count += 1
        if count != 1:
            warnings.warn(
                "This cluster has more than one main usage type or none, "
                "check your excel file for mistakes! \n"
                "Common mistakes: \n"
                "-NetArea of a wall is not equal to 0 \n"
                "-UsageType of a wall is not empty \n"
                "Explanation: Rooms may have outer walls/windows on different orientations.\n"
                "Every row with an empty slot in the column UsageType, "
                "marks another direction of an outer wall and/or"
                "window entity of the same room.\n"
                "The connection of the same room is realised by an "
                "RoomIdentifier equal to the respective "
                "BelongsToIdentifier. \n Cluster = %s" % cluster
            )

    # name usage types after usage types available in the json
    usage_to_json_usage = {
        "IsolationRoom": "Bed room",
        "PatientRoom": "Bed room",
        "Aisle": "Corridors in the general care area",
        "Technical room": "Stock, technical equipment, archives",
        "Washing": "WC and sanitary rooms in non-residential buildings",
        "Stairway": "Corridors in the general care area",
        "WC": "WC and sanitary rooms in non-residential buildings",
        "Storage": "Stock, technical equipment, archives",
        "Lounge": "Meeting, Conference, seminar",
        "Office": "Meeting, Conference, seminar",
        "Treatment room": "Examination- or treatment room",
        "StorageChemical": "Stock, technical equipment, archives",
        "EquipmentServiceAndRinse": "WC and sanitary rooms in non-residential buildings",
    }

    # rename all zone names from the excel to the according zone name which
    # is in the UseConditions.json files
    usages = get_list_of_present_entries(data["RoomClusterUsage"])
    for usage in usages:
        data["RoomClusterUsage"] = np.where(
            data["RoomClusterUsage"] == usage,
            usage_to_json_usage[usage],
            data["RoomClusterUsage"],
        )

    # name the column where the zones are defined "Zone"
    data["Zone"] = data["RoomClusterUsage"]

    return data


# -------------------------------------------------------------
def import_building_from_excel(
    project, building_name, construction_age, path_to_excel, sheet_names
):
    """
    Import building data from excel, convert it via the respective zoning and feed it to teasers logic classes.
    Pay attention to hard coded parts, which are marked.

    :param project: Teaser project object
    :type project:
    :param building_name: name of building to be set in the project
    :type building_name:
    :param construction_age: construction age of the building
    :type construction_age: int
    :param path_to_excel: path to excel file to be imported
    :type path_to_excel: str
    :param sheet_names: sheet names which shall be imported
    :type sheet_names: str or list
    :return: Teaser project
    :rtype:
    """

    def warn_constructiontype(element):
        if element.construction_type is None:
            warnings.warn(
                'In Zone "%s" the %s construction "%s" could not be loaded from the TypeBuildingElements.json, '
                "an error will occur due to missing data for calculation."
                "Check for spelling and the correct combination of building age and construction type."
                "Here is the list of faulty entries:\n%s"
                "\nThese entries can easily be found checking the stated index in the produced ZonedInput.xlsx"
                % (
                    group["Zone"].iloc[0],
                    element.name,
                    group["OuterWallConstruction"].iloc[0],
                    group,
                )
            )

    bldg = Building(parent=project)
    bldg.name = building_name
    bldg.year_of_construction = construction_age
    bldg.with_ahu = True  # HardCodedInput
    if bldg.with_ahu is True:
        bldg.central_ahu.heat_recovery = True  # HardCodedInput
        bldg.central_ahu.efficiency_recovery = 0.35  # HardCodedInput
        bldg.central_ahu.temperature_profile = 25 * [273.15 + 18]  # HardCodedInput
        bldg.central_ahu.min_relative_humidity_profile = 25 * [0]  # HardCodedInput
        bldg.central_ahu.max_relative_humidity_profile = 25 * [1]  # HardCodedInput
        bldg.central_ahu.v_flow_profile = 25 * [1]  # HardCodedInput

    # Parameters that need hard coding in teasers logic classes
    # 1. "use_set_back" needs hard coding at aixlib.py in the init; defines
    # if the in the useconditions stated
    #   heating_time with the respective set_back_temp should be applied.
    #   use_set_back = false -> all hours of the day
    #   have same set_temp_heat actual value: use_set_back = Check!
    # 2. HeaterOn, CoolerOn, hHeat, lCool, etc. can be hard coded in the text
    # file
    #   "teaser / data / output / modelicatemplate / AixLib /
    #   AixLib_ThermalZoneRecord_TwoElement"
    #   actual changes: Check!

    # Parameters to be set for each and every zone (#HardCodedInput)
    # -----------------------------
    OutWallTilt = 90
    WindowTilt = 90
    GroundFloorTilt = 0
    FloorTilt = 0
    CeilingTilt = 0
    RooftopTilt = 0
    GroundFloorOrientation = -2
    FloorOrientation = -2
    RooftopOrientation = -1
    CeilingOrientation = -1
    # -----------------------------

    # load_building_data from excel_to_pandas dataframe:
    data = import_data(path_to_excel, sheet_names)

    # informative print
    UsageTypes = get_list_of_present_entries(data["UsageType"])
    print("List of present UsageTypes in the original Data set: \n%s" % UsageTypes)

    # define the zoning methodology/function
    data = zoning_example(data)

    # informative print
    UsageTypes = get_list_of_present_entries(data["Zone"])
    print("List of Zones after the zoning is applied: \n%s" % UsageTypes)

    # aggregate all rooms of each Zone and for each set general parameter,
    # boundary conditions
    # and parameter regarding the building physics
    Zones = data.groupby(["Zone"])
    for name, Zone in Zones:

        # Block: Thermal Zone (general parameter)
        tz = ThermalZone(parent=bldg)
        tz.name = str(name)
        tz.area = Zone["NetArea[m²]"].sum()
        # room vice calculation of volume plus summing those
        tz.volume = (
            np.array(Zone["NetArea[m²]"]) * np.array(Zone["HeatedRoomHeight[m]"])
        ).sum()

        # Block: Boundary Conditions
        # load UsageOperationTime, Lighting, RoomClimate and InternalGains
        # from the "UseCondition.json"
        tz.use_conditions = UseConditions(parent=tz)
        tz.use_conditions.load_use_conditions(Zone["Zone"].iloc[0], project.data)

        # Block: Building Physics
        # Grouping by orientation and construction type
        # aggregating and feeding to the teaser logic classes
        Grouped = Zone.groupby(["OuterWallOrientation[°]", "OuterWallConstruction"])
        for name, group in Grouped:
            # looping through a groupby object automatically discards the
            # groups where one of the attributes is nan
            # additionally check for strings, since the value must be of type
            # int or float
            if not isinstance(group["OuterWallOrientation[°]"].iloc[0], str):
                out_wall = OuterWall(parent=tz)
                out_wall.name = (
                    "outer_wall_"
                    + str(int(group["OuterWallOrientation[°]"].iloc[0]))
                    + "_"
                    + str(group["OuterWallConstruction"].iloc[0])
                )
                out_wall.area = group["OuterWallArea[m²]"].sum()
                out_wall.tilt = OutWallTilt
                out_wall.orientation = group["OuterWallOrientation[°]"].iloc[0]
                # load wall properties from "TypeBuildingElements.json"
                out_wall.load_type_element(
                    year=bldg.year_of_construction,
                    construction=group["OuterWallConstruction"].iloc[0],
                )
                warn_constructiontype(out_wall)
            else:
                warnings.warn(
                    'In Zone "%s" the OuterWallOrientation "%s" is '
                    "neither float nor int, "
                    "hence this building element is not added.\nHere is the "
                    "list of faulty entries:\n%s"
                    "\n These entries can easily be found checking the stated "
                    "index in the produced ZonedInput.xlsx"
                    % (
                        group["Zone"].iloc[0],
                        group["OuterWallOrientation[°]"].iloc[0],
                        group,
                    )
                )

        Grouped = Zone.groupby(["WindowOrientation[°]", "WindowConstruction"])
        for name, group in Grouped:
            # looping through a groupby object automatically discards the
            # groups where one of the attributes is nan
            # additionally check for strings, since the value must be of type
            # int or float
            if not isinstance(group["OuterWallOrientation[°]"].iloc[0], str):
                window = Window(parent=tz)
                window.name = (
                    "window_"
                    + str(int(group["WindowOrientation[°]"].iloc[0]))
                    + "_"
                    + str(group["WindowConstruction"].iloc[0])
                )
                window.area = group["WindowArea[m²]"].sum()
                window.tilt = WindowTilt
                window.orientation = group["WindowOrientation[°]"].iloc[0]
                # load wall properties from "TypeBuildingElements.json"
                window.load_type_element(
                    year=bldg.year_of_construction,
                    construction=group["WindowConstruction"].iloc[0],
                )
                warn_constructiontype(window)
            else:
                warnings.warn(
                    'In Zone "%s" the window orientation "%s" is neither '
                    "float nor int, "
                    "hence this building element is not added. Here is the "
                    "list of faulty entries:\n%s"
                    "\nThese entries can easily be found checking the stated "
                    "index in the produced ZonedInput.xlsx"
                    % (
                        group["Zone"].iloc[0],
                        group["WindowOrientation[°]"].iloc[0],
                        group,
                    )
                )

        Grouped = Zone.groupby(["IsGroundFloor", "FloorConstruction"])
        for name, group in Grouped:
            if group["NetArea[m²]"].sum() != 0:  # to avoid devision by 0
                if group["IsGroundFloor"].iloc[0] == 1:
                    ground_floor = GroundFloor(parent=tz)
                    ground_floor.name = "ground_floor" + str(
                        group["FloorConstruction"].iloc[0]
                    )
                    ground_floor.area = group["NetArea[m²]"].sum()
                    ground_floor.tilt = GroundFloorTilt
                    ground_floor.orientation = GroundFloorOrientation
                    # load wall properties from "TypeBuildingElements.json"
                    ground_floor.load_type_element(
                        year=bldg.year_of_construction,
                        construction=group["FloorConstruction"].iloc[0],
                    )
                    warn_constructiontype(ground_floor)
                elif group["IsGroundFloor"].iloc[0] == 0:
                    floor = Floor(parent=tz)
                    floor.name = "floor" + str(group["FloorConstruction"].iloc[0])
                    floor.area = group["NetArea[m²]"].sum() / 2  # only half of
                    # the floor belongs to this story
                    floor.tilt = FloorTilt
                    floor.orientation = FloorOrientation
                    # load wall properties from "TypeBuildingElements.json"
                    floor.load_type_element(
                        year=bldg.year_of_construction,
                        construction=group["FloorConstruction"].iloc[0],
                    )
                    warn_constructiontype(floor)
                else:
                    warnings.warn(
                        "Values for IsGroundFloor have to be either 0 or 1, "
                        "for no or yes respectively"
                    )
            else:
                warnings.warn(
                    'Zone "%s" with IsGroundFloor "%s" and construction '
                    'type "%s" '
                    "has no floor nor groundfloor, since the area equals 0."
                    % (
                        group["Zone"].iloc[0],
                        group["IsGroundFloor"].iloc[0],
                        group["FloorConstruction"].iloc[0],
                    )
                )

        Grouped = Zone.groupby(["IsRooftop", "CeilingConstruction"])
        for name, group in Grouped:
            if group["NetArea[m²]"].sum() != 0:  # to avoid devision by 0
                if group["IsRooftop"].iloc[0] == 1:
                    rooftop = Rooftop(parent=tz)
                    rooftop.name = "rooftop" + str(group["CeilingConstruction"].iloc[0])
                    rooftop.area = group[
                        "NetArea[m²]"
                    ].sum()  # sum up area of respective
                    # rooftop parts
                    rooftop.tilt = RooftopTilt
                    rooftop.orientation = RooftopOrientation
                    # load wall properties from "TypeBuildingElements.json"
                    rooftop.load_type_element(
                        year=bldg.year_of_construction,
                        construction=group["CeilingConstruction"].iloc[0],
                    )
                    warn_constructiontype(rooftop)
                elif group["IsRooftop"].iloc[0] == 0:
                    ceiling = Ceiling(parent=tz)
                    ceiling.name = "ceiling" + str(group["CeilingConstruction"].iloc[0])
                    ceiling.area = group["NetArea[m²]"].sum() / 2  # only half
                    # of the ceiling belongs to a story,
                    # the other half to the above
                    ceiling.tilt = CeilingTilt
                    ceiling.orientation = CeilingOrientation
                    # load wall properties from "TypeBuildingElements.json"
                    ceiling.load_type_element(
                        year=bldg.year_of_construction,
                        construction=group["CeilingConstruction"].iloc[0],
                    )
                    warn_constructiontype(ceiling)
                else:
                    warnings.warn(
                        "Values for IsRooftop have to be either 0 or 1, "
                        "for no or yes respectively"
                    )
            else:
                warnings.warn(
                    'Zone "%s" with IsRooftop "%s" and construction type '
                    '"%s" '
                    "has no ceiling nor rooftop, since the area equals 0."
                    % (
                        group["Zone"].iloc[0],
                        group["IsRooftop"].iloc[0],
                        group["CeilingConstruction"].iloc[0],
                    )
                )

        Grouped = Zone.groupby(["InnerWallConstruction"])
        for name, group in Grouped:
            if group["InnerWallArea[m²]"].sum() != 0:  # to avoid devision by 0
                in_wall = InnerWall(parent=tz)
                in_wall.name = "inner_wall" + str(
                    group["InnerWallConstruction"].iloc[0]
                )
                in_wall.area = group["InnerWallArea[m²]"].sum() / 2  # only
                # half of the wall belongs to each room,
                # the other half to the adjacent
                # load wall properties from "TypeBuildingElements.json"
                in_wall.load_type_element(
                    year=bldg.year_of_construction,
                    construction=group["InnerWallConstruction"].iloc[0],
                )
                warn_constructiontype(in_wall)
            else:
                warnings.warn(
                    'Zone "%s" with inner wall construction "%s" has no '
                    "inner walls, since area = 0."
                    % (group["Zone"].iloc[0], group["InnerWallConstructio" "n"].iloc[0])
                )

        # Block: AHU and infiltration #Attention hard coding
        # set the supply volume flow of the AHU per zone
        ahu_dict = {
            "Bedroom": [15.778, 15.778],
            "Corridorsinthegeneralcarearea": [5.2941, 5.2941],
            "Examinationortreatmentroom": [15.743, 15.743],
            "MeetingConferenceseminar": [16.036, 16.036],
            "Stocktechnicalequipmentarchives": [20.484, 20.484],
            "WCandsanitaryroomsinnonresidentialbuildings": [27.692, 27.692],
        }
        _i = 0
        for key in ahu_dict:
            if tz.name == key:
                tz.use_conditions.min_ahu = ahu_dict[key][0]
                tz.use_conditions.max_ahu = ahu_dict[key][1]
                _i = 1
        if _i == 0:
            warnings.warn(
                "The zone %s could not be found in your ahu_dict. Hence, "
                "no AHU flow is defined. The default value is "
                "0 (min_ahu = 0; max_ahu=0" % tz.name
            )

    return project, data


if __name__ == "__main__":
    result_path = os.path.dirname(__file__)

    prj = Project(load_data=True)
    prj.name = "BuildingGeneratedviaExcelImport"
    prj.data.load_uc_binding()
    prj.weather_file_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data",
        "input",
        "inputdata",
        "weatherdata",
        "DEU_BW_Mannheim_107290_TRY2010_12_Jahr_BBSR.mos",
    )
    prj.modelica_info.weekday = 0  # 0-Monday, 6-Sunday
    prj.modelica_info.simulation_start = 0  # start time for simulation

    PathToExcel = os.path.join(
        os.path.dirname(__file__), "examplefiles", "ExcelBuildingData_Sample.xlsx"
    )
    prj, Data = import_building_from_excel(
        prj, "ExampleImport", 2000, PathToExcel, sheet_names=["ImportSheet1"]
    )

    prj.modelica_info.current_solver = "dassl"
    prj.calc_all_buildings(raise_errors=True)
    prj.export_aixlib(internal_id=None, path=result_path)

    # if wished, export the zoned dataframe which is finally used to
    # parametrize the teaser classes
    Data.to_excel(os.path.join(result_path, prj.name, "ZonedInput.xlsx"))
    # if wished, save the current python script to the results folder to
    # track the used parameters and reproduce results
    shutil.copy(__file__, os.path.join(result_path, prj.name))

    print("%s: That's it :)" % prj.name)
