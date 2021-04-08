# -*- coding: utf-8 -*-
"""
Created on Mon Jul 27 16:25:12 2020

Last modified 2020-09-25 for Project 'Energieeffizienz in Schwimmbädern - Neubau und Bestand'
"""

import math
import collections
from teaser.logic.archetypebuildings.nonresidential import NonResidential
from teaser.logic.buildingobjects.useconditions import UseConditions as UseCond
from teaser.logic.buildingobjects.buildingphysics.ceiling import Ceiling
from teaser.logic.buildingobjects.buildingphysics.floor import Floor
from teaser.logic.buildingobjects.buildingphysics.groundfloor import GroundFloor
from teaser.logic.buildingobjects.buildingphysics.innerwall import InnerWall
from teaser.logic.buildingobjects.buildingphysics.outerwall import OuterWall
from teaser.logic.buildingobjects.buildingphysics.rooftop import Rooftop
from teaser.logic.buildingobjects.buildingphysics.window import Window
from teaser.logic.buildingobjects.thermalzone import ThermalZone
import teaser.data.input.ExcelToTeaser as excel_input


class SwimmingPool(NonResidential):
    """Archetype Office Building according to BMVBS

    Subclass from NonResidential archetype class based on the teaser office module.

    The model contains up to 8 zones of the swimming pool according to
    'Erneuerbare Energien in Schwimmbädern - Neubau und Bestand' + additional zones
    for each pool.     
    Each of the normal zones has variable outer walls, windows, roofs and ground floors. 
    The net zone areas as well as the building element areas are read from an individual
    Excel file.

    Parameters
    ----------

    parent: Project()
        The parent class of this object, the Project the Building belongs to.
        Allows for better control of hierarchical structures. If not None it
        adds this Building instance to Project.buildings.
        (default: None)
    name : str
        Individual name
    year_of_construction : int
        Year of first construction
    height_of_floors : float [m]
        Average height of the buildings' floors
    number_of_floors : int
        Number of building's floors above ground
    net_leased_area : float [m2]
        Total net leased area of building. This is area is NOT the footprint
        of a building
    with_ahu : Boolean
        If set to True, an empty instance of BuildingAHU is instantiated and
        assigned to attribute central_ahu. This instance holds information for
        central Air Handling units. Default is False.
    internal_gains_mode: int [1, 2, 3]
        mode for the internal gains calculation by persons:
        1: Temperature and activity degree dependent calculation. The
           calculation is based on  SIA 2024 (default)
        2: Temperature and activity degree independent calculation, the max.
           heatflowrate is prescribed by the parameter
           fixed_heat_flow_rate_persons.
        3: Temperature and activity degree dependent calculation with
           consideration of moisture. The calculation is based on SIA 2024
    office_layout : int
        Structure of the floor plan of office buildings, default is 1,
        which is representative for one elongated floor.
            1: elongated 1 floor
            2: elongated 2 floors
            3: compact (e.g. for a square base building)
    window_layout : int
        Structure of the window facade type, default is 0, which is a generic facade
        representing a statistical mean value of window area. This is the foundation
        for calculating the other window layouts with correction factors.
            0: generic facade
            1: punctuated facade (individual windows)
            2: banner facade (continuous windows)
            3: full glazing
    construction_type : str
        Construction type of used wall constructions default is "heavy")
            heavy: heavy construction
            light: light construction
    filePath: str
        Path to Excel file with stored information
    sheetNameAreas: dict
        Stored zone areas
    swimmingPoolCategory: str
        Category of the swimming pool

    Note
    ----------
    The listed attributes are just the ones that are set by the user
    calculated values are not included in this list. Changing these values is
    expert mode.

    Attributes
    ----------

    zone_area_factors : dict
        This dictionary contains the name of the zone (str), the
        zone area factor (float), the zone volume factor (float) and the zone usage from BoundaryConditions json
        (str). (Default see doc string above)
    outer_wall_names : dict
        This dictionary contains a random name for the outer walls,
        their orientation and tilt. Default is a building in north-south
        orientation)
    roof_names : dict
        This dictionary contains the name of the roofs, their orientation
        and tilt. Default is one flat roof.
    ground_floor_names : dict
        This dictionary contains the name of the ground floors, their
        orientation and tilt. Default is one ground floor.
    window_names : dict
        This dictionary contains the name of the window, their
        orientation and tilt. Default is a building in north-south
        orientation)
    inner_wall_names : dict
        This dictionary contains the name of the inner walls, their
        orientation and tilt. Default is one cumulated inner wall.
    ceiling_names : dict
        This dictionary contains the name of the ceilings, their
        orientation and tilt. Default is one cumulated ceiling.
    floor_names : dict
        This dictionary contains the name of the floors, their
        orientation and tilt. Default is one cumulated floor.
    gross_factor : float
        gross factor used to correct the rooftop and floor area (default is
        1.15)
    est_factor_wall_area : float
        estimation factor to calculate outer wall area
    est_exponent_wall : float
        estimation factor exponent to calculate outer wall area
    est_factor_win_area : float
        estimation factor to calculate window area
    est_exponent_win : float
        estimation factor exponent to calculate window area
    isSwimmingPool : boolean
        Indicates for other classes that a swimming pool will be created
    """
    
    def __init__(
        self,
        parent,
        filePath,
        sheetNameAreas,
        swimmingPoolCategory,
        name=None,
        year_of_construction=None,
        number_of_floors=None,
        height_of_floors=None,
        net_leased_area=None,
        with_ahu=False,
        internal_gains_mode=1,
        office_layout=None,
        window_layout=None,
        construction_type=None        
    ):
        """Constructor of SwimmingPool archetype
        """
        super(SwimmingPool, self).__init__(
            parent,
            name,
            year_of_construction,
            net_leased_area,
            with_ahu,
            internal_gains_mode,
        )
        self.office_layout = office_layout
        self.window_layout = window_layout
        self.construction_type = construction_type
        self.number_of_floors = number_of_floors
        self.height_of_floors = height_of_floors

        # [area factor, volume factor, usage type(has to be set)]
        self.zone_area_factors = collections.OrderedDict()

        # Reading zone areas and volumes from Excel file according to filePath and sheetNameAreas

        print("Reading zone areas from Excel for:", name) 
        print()
        # List zoneAreas stores the element areas of each zone.
        # List zoneVolumes stores the element volume of each zone.
        # Pools stores additional information about the respective pool.
        # Row structure: [pool type, water area, pool floor with earth contact, 
        # water volume, water temperature]
        self.zoneAreas=excel_input.getZoneArea(filePath, sheetNameAreas)
        self.zoneVolumes=excel_input.getZoneVolume(filePath, sheetNameAreas)
        self.pools=excel_input.getPoolData(filePath, sheetNameAreas)
        self.poolsInDict=excel_input.getPoolDataInDict("ALL", filePath, sheetNameAreas)
        self.numZones=0
        for value in self.zoneAreas:
            if value>0:
                self.numZones+=1
        
                
        # Zone won't be created if net leased area is 0                           
        if (self.zoneAreas[0]!=0):
            self.zone_area_factors["Eingangsbereich"] = [self.zoneAreas[0], self.zoneVolumes[0],
                                                         "Foyer (theater and event venues)"]
        if (self.zoneAreas[1]!=0):
            self.zone_area_factors["Umkleiden"] = [self.zoneAreas[1], self.zoneVolumes[1],
                                                   "Group Office (between 2 and 6 employees)"]
        if (self.zoneAreas[2]!=0):
            self.zone_area_factors[
                "Duschen und Sanitärräume"] = [self.zoneAreas[2], self.zoneVolumes[2],
                "WC and sanitary rooms in non-residential buildings"]      
        if (self.zoneAreas[3]!=0): 
            self.zone_area_factors['Schwimmhalle'] = [self.zoneAreas[3], self.zoneVolumes[3],
                                                      "Gym (without spectator area)"]
        if (self.zoneAreas[4]!=0):
            self.zone_area_factors["Aufsichtsraum"] = [self.zoneAreas[4], self.zoneVolumes[4],
                                                  "Meeting, Conference, seminar"]
        if (self.zoneAreas[5]!=0):
            self.zone_area_factors["Saunabereich"] = [self.zoneAreas[5], self.zoneVolumes[5], "Sauna area"]
        if (self.zoneAreas[6]!=0):
            self.zone_area_factors["Fitness"] = [self.zoneAreas[6], self.zoneVolumes[6],
                                                 "Gym (without spectator area)"]
        if (self.zoneAreas[7]!=0):
            self.zone_area_factors["Technikraum"] = [self.zoneAreas[7], self.zoneVolumes[7],
                                                     "Stock, technical equipment, archives"]
        for pool in self.pools:            
            self.zone_area_factors[excel_input.getKeyword(pool[0], filePath, 
                                          sheetNameAreas)] = [pool[1], pool[6],
                                          "Gym (without spectator area)"]
            
        for key, value in self.zone_area_factors.items():
            print (key, "with zone area:", value[0], "m²")
        print()

        # Creating potential building elements
        # Warning: All the names of the building elements are saved without spaces
        # in their names!            
        # [tilt, orientation]
        
        self.outer_wall_names = {
            "Exterior Facade North": [90, 0],
            "Exterior Facade East": [90, 90],
            "Exterior Facade South": [90, 180],
            "Exterior Facade West": [90, 270],
            "PoolWall":[90, 0]}

        self.roof_names = {"Rooftop": [0, -1]}
         
        self.ground_floor_names = {
            "Floor With Earth Contact": [0, -2],
            "Pool Floor With Earth Contact": [0, -2]}

        self.window_names = {
            "Window Facade North": [90, 0],
            "Window Facade East": [90, 90],
            "Window Facade South": [90, 180],
            "Window Facade West": [90, 270]}

        self.inner_wall_names = {"InnerWall": [90, 0],
                                 "InnerPoolWall":[90, 0]}
        
        self.floor_names = {"Floor": [0, -2],
                            "Pool Area Above Technical Room": [0, -2]}
        
        self.ceiling_names = {"Ceiling": [0, -1]}



        """
        The following parameters are part of the teaser office class and won't be used 
        for the swimming pool calculation if all needed parameters are provided.
        """

        self.gross_factor = 1.15  # based on :cite:`Liebchen.2007`
        self.est_factor_wall_area = 0.7658
        self.est_exponent_wall = 0.9206
        self.est_factor_win_area = 0.074
        self.est_exponent_win = 1.0889

        # estimated intermediate calculated values
        self._est_outer_wall_area = 0
        self._est_win_area = 0
        self._est_roof_area = 0
        self._est_floor_area = 0
        self._est_facade_area = 0
        self._est_width = 0
        self._est_length = 0

        if self.window_layout == 0:
            self.corr_factor_wall = 1.0
            self.corr_factor_win = 1.0
        elif self.window_layout == 1:
            self.corr_factor_wall = 0.75
            self.corr_factor_win = 0.25
        elif self.window_layout == 2:
            self.corr_factor_wall = 0.5
            self.corr_factor_win = 0.5
        elif self.window_layout == 3:
            self.corr_factor_wall = 0.1
            self.corr_factor_win = 0.9
        else:
            raise ValueError("window_layout value has to be between 0 - 3")

        if self.office_layout == 0 or self.office_layout == 1:
            self._est_width = 13.0
        elif self.office_layout == 2:
            self._est_width = 15.0
        elif self.office_layout == 3:
            self._est_width = math.sqrt(
                (self.net_leased_area / self.number_of_floors) * self.gross_factor
            )
        else:
            raise ValueError("office_layout value has to be between 0 - 3")
        if self.net_leased_area is not None and self.number_of_floors is not None:
            self._est_length = (
                (self.net_leased_area / self.number_of_floors) * self.gross_factor
            ) / self._est_width
        else:
            pass

        
        # Default values for AHU from Teaser. Adaptation for swimming pools pending.
            if self.with_ahu is True:
                self.central_ahu.temperature_profile = (
                    7 * [293.15] + 12 * [295.15] + 6 * [293.15]
                )
                #  according to :cite:`DeutschesInstitutfurNormung.2016`
                self.central_ahu.min_relative_humidity_profile = 25 * [0.45]  #
                #  according to :cite:`DeutschesInstitutfurNormung.2016b`  and
                # :cite:`DeutschesInstitutfurNormung.2016`
                self.central_ahu.max_relative_humidity_profile = 25 * [0.65]
                self.central_ahu.v_flow_profile = (
                    7 * [0.0] + 12 * [1.0] + 6 * [0.0]
                )  # according to user
                # profile in :cite:`DeutschesInstitutfurNormung.2016`
               
            


    def generate_archetype(self, filePath, sheetNameAreas, sheetNameElements):
        """Generates an office building.

        With given values, this class generates an office archetype building
        according to TEASER requirements.
        """
        print("Generating archetype. Please wait...")
        print()
        # Creates binding for Material data of swimming pools
        self.parent.data.swimmingpool_bind = dict()
        # help area for the correct building area setting while using typeBldgs
        self.thermal_zones = None
        type_bldg_area = self.net_leased_area
        self.net_leased_area = 0.0
        # create zones with their corresponding area, name and usage
        for key, value in self.zone_area_factors.items():
            # If Volume of Zone < 1m**3 then no Zone will be created
            if value[1] < 1:
                continue
            zone = ThermalZone(self)
            zone.area = value[0] 
            zone.volume = value[1]
            zone.name = key
            #Additional Parameters for Pools 
            zone.paramRecord = dict()
            use_cond = UseCond(zone)
            use_cond.load_use_conditions(value[2], data_class=self.parent.data)
            zone.use_conditions = use_cond


        """
        The following element calculations are part of the teaser office class and 
        won't be used for the swimming pool calculation if all needed parameters 
        are provided. 
        """
        # statistical estimation of the facade
        self._est_outer_wall_area = (
            self.est_factor_wall_area * type_bldg_area ** self.est_exponent_wall
        )
        self._est_win_area = (
            self.est_factor_win_area * type_bldg_area ** self.est_exponent_win
        )
        self._est_roof_area = (
            type_bldg_area / self.number_of_floors
        ) * self.gross_factor
        self._est_floor_area = (
            type_bldg_area / self.number_of_floors
        ) * self.gross_factor
        # manipulation of wall according to facade design
        # (received from window_layout)
        self._est_facade_area = self._est_outer_wall_area + self._est_win_area
        if not self.window_layout == 0:
            self._est_outer_wall_area = self._est_facade_area * self.corr_factor_wall
            self._est_win_area = self._est_facade_area * self.corr_factor_win
        else:
            pass

        # OUTER WALLS #
        # set the facade area to the four orientations
        for key, value in self.outer_wall_names.items():

            # North and South
            if value[1] == 0 or value[1] == 180:
                self.outer_area[value[1]] = self._est_outer_wall_area * (
                    self._est_length / (2 * self._est_width + 2 * self._est_length))
            # East and West
            elif value[1] == 90 or value[1] == 270:
                self.outer_area[value[1]] = self._est_outer_wall_area * (
                    self._est_width / (2 * self._est_width + 2 * self._est_length))
         
            
            #Creates an outer wall for each zone and assigns building elements             
            for idx, zone in enumerate(self.thermal_zones):
                #Creates only for Zones which are Pools a Outer Wall as Pool Wall 
                if (idx < self.numZones and key == "PoolWall"):
                    continue
                elif (idx >= self.numZones and key != "PoolWall"):
                    continue
                # create wall and set building elements
                outer_wall = OuterWall(zone)
                outer_wall.name = key
                outer_wall.load_type_element(
                    year=self.year_of_construction,
                    construction=self.construction_type,
                    data_class=self.parent.data,
                    isSwimmingPool=True, 
                    filePath=filePath, 
                    sheetNameElements=sheetNameElements)               
                outer_wall.tilt = value[0]
                outer_wall.orientation = value[1]
                
        # WINDOWS #
        for key, value in self.window_names.items():

            if value[1] == 0 or value[1] == 180:

                self.window_area[value[1]] = self._est_win_area * (
                    self._est_length / (2 * self._est_width + 2 * self._est_length)
                )

            elif value[1] == 90 or value[1] == 270:

                self.window_area[value[1]] = self._est_win_area * (
                    self._est_width / (2 * self._est_width + 2 * self._est_length)
                )

            """
            There is no real classification for windows, so this is a bit hard
            code - will be fixed sometime.
            """
            
            """
            Due to missing building element data for some elements in the 
            actual Excel file, the respective parameter 'isSwimmingPool' 
            is set to 'False' in ExcelToTeaser to use data from the original teaser database
            """            
            
            for idx, zone in enumerate(self.thermal_zones):
                 #Only created for Zones which are not Pools
                if (idx >= self.numZones):
                    continue
                window = Window(zone)
                window.name = key
                window.load_type_element(
                    self.year_of_construction,
                    "Kunststofffenster, " "Isolierverglasung",
                    data_class=self.parent.data,
                    isSwimmingPool=True, 
                    filePath=filePath, 
                    sheetNameElements=sheetNameElements
                )                
                window.tilt = value[0]
                window.orientation = value[1]

         # ROOFTOPS #
        for key, value in self.roof_names.items():

            self.outer_area[value[1]] = self._est_roof_area

            for idx, zone in enumerate(self.thermal_zones):
                #Only created for Zones which are not Pools
                if (idx >= self.numZones):
                    continue
                roof = Rooftop(zone)
                roof.name = key
                roof.load_type_element(
                    year=self.year_of_construction,
                    construction=self.construction_type,
                    data_class=self.parent.data,
                    isSwimmingPool=True, 
                    filePath=filePath, 
                    sheetNameElements=sheetNameElements
                )
                roof.tilt = value[0]
                roof.orientation = value[1]

        # GROUNDFLOORS #
        for key, value in self.ground_floor_names.items():

            self.outer_area[value[1]] = self._est_floor_area    
            
            for idx, zone in enumerate(self.thermal_zones):  
                #Creates only for Zones which are Pools a Ground Floor as Pool Floor
                if (idx < self.numZones and key == "Pool Floor With Earth Contact"):
                    continue
                elif (idx >= self.numZones and key != "Pool Floor With Earth Contact"):
                    continue
                ground_floor = GroundFloor(zone)
                ground_floor.name = key
                ground_floor.load_type_element(
                    year=self.year_of_construction,
                    construction=self.construction_type,
                    data_class=self.parent.data,
                    isSwimmingPool=True, 
                    filePath=filePath, 
                    sheetNameElements=sheetNameElements
                )
                ground_floor.tilt = value[0]
                ground_floor.orientation = value[1]

        # INNER WALLS #
        for key, value in self.inner_wall_names.items():

            for idx, zone in enumerate(self.thermal_zones):
                #Creates only for Zones which are Pools a Inner Wall as Wall
                if (idx < self.numZones and key == "InnerPoolWall"):
                    continue
                elif (idx >= self.numZones and key != "InnerPoolWall"):
                    continue 
                inner_wall = InnerWall(zone)
                inner_wall.name = key
                inner_wall.load_type_element(
                    year=self.year_of_construction,
                    construction=self.construction_type,
                    data_class=self.parent.data,
                    isSwimmingPool=True, 
                    filePath=filePath, 
                    sheetNameElements=sheetNameElements
                )
                inner_wall.tilt = value[0]
                inner_wall.orientation = value[1]
        
       
        # Actual Excel File does not include standard floor or ceiling areas, 
        # so these areas are calculated by the standard teaser algorithm 
        # if number of floors > 1. The special types of floors and ceilings
        # are read out from the Excel file.
        # CEILINGS #
        for key, value in self.ceiling_names.items(): 
            for idx, zone in enumerate(self.thermal_zones):
                #Only created for Zones which are not Pools
                if (idx >= self.numZones):
                    continue             
                ceiling = Ceiling(zone)
                ceiling.name = key
                ceiling.load_type_element(
                    year=self.year_of_construction,
                    construction=self.construction_type,
                    data_class=self.parent.data,
                    isSwimmingPool=True, 
                    filePath=filePath, 
                    sheetNameElements=sheetNameElements
                )
                ceiling.tilt = value[0]
                ceiling.orientation = value[1] 

        # FLOORS #   
        for key, value in self.floor_names.items():
            for idx, zone in enumerate(self.thermal_zones):
                #Creates only for Zones which are Pools a Floor as Pool Floor
                if (idx < self.numZones and key == "Pool Area Above Technical Room"):
                    continue
                elif (idx >= self.numZones and key != "Pool Area Above Technical Room"):
                    continue
                floor = Floor(zone)
                floor.name = key
                floor.load_type_element(
                    year=self.year_of_construction,
                    construction=self.construction_type,
                    data_class=self.parent.data,
                    isSwimmingPool=True, 
                    filePath=filePath, 
                    sheetNameElements=sheetNameElements
                )
                floor.tilt = value[0]
                floor.orientation = value[1] 
                        

        #Calculates building surface area and surface areas of each zone and orientation.
        for key, value in self.outer_area.items():
            self.set_outer_wall_area(value, key, isSwimmingPool=True, filePath=filePath, 
                                     sheetNameAreas=sheetNameAreas, zoneAreas=self.zoneAreas, 
                                     numZones=self.numZones)

        #Calculates window surface areas for each zone and orientation.
        for key, value in self.window_area.items():
            self.set_window_area(value, key, isSwimmingPool=True, filePath=filePath, 
                                 sheetNameAreas=sheetNameAreas, zoneAreas=self.zoneAreas,
                                 numZones=self.numZones)

        #Calculates inner wall area as sum of innerWalls, ceiling and floor for each zone
        zoneId=0
        for idx, zone in enumerate(self.thermal_zones):
            while zoneId < len(self.zoneAreas) and self.zoneAreas[zoneId]==0:                    
                zoneId+=1 
            zone.set_inner_wall_area(zoneId=zoneId, isSwimmingPool=True, filePath=filePath, 
                                     sheetNameAreas=sheetNameAreas, zoneAreas=self.zoneAreas,
                                     numZones=self.numZones)
            zoneId+=1
        
        # Calculate additional Parameters for Pools out of the input from Excel stored in "poolsInDict"
        # Results will be stored in paramRecord Dict for each Pool Zone
        numOfPools = 0
        for id, zone in enumerate(self.thermal_zones):
            if "becken" in zone.name:
                numOfPools += 1
                paramRecord = dict()

                ## T_pool ##
                paramRecord["T_pool"] = self.poolsInDict[zone.name]["Pool temperature"]

                ## A_pool ##
                paramRecord["A_pool"] = self.poolsInDict[zone.name]["Water surface"]

                ## d_pool ##
                paramRecord["d_pool"] = self.poolsInDict[zone.name]["Tiefe Becken"]

                ## V_pool ##
                paramRecord["V_pool"] = self.poolsInDict[zone.name]["Water volume"]
                
                ## Q ## 
                # Hilfsparameter zur Berechnung von Q
                # k
                if self.poolsInDict[zone.name]["Filterkombination"] == "ohne Ozon" or self.poolsInDict[zone.name]["Filterkombination"] == "mit Brom":
                    k = 0.5
                elif self.poolsInDict[zone.name]["Filterkombination"] == "mit Ozon":
                    k = 0.6
                elif self.poolsInDict[zone.name]["Filterkombination"] == "mit Ultrafiltration":
                    k = 1
                else:
                    k = None
                # m, a, n
                if zone.name == "Kleinkinderbecken":
                    m = 2
                elif zone.name.startswith("Freiformbecken") or zone.name == "Nichtschwimmerbecken" or zone.name == "Mehrzweckbecken":
                    a = 2.7
                    n = 1
                elif zone.name == "Schwimmerbecken" or zone.name == "Springerbecken":
                    a = 4.5
                    n = 1
                else:
                    a = None
                    n = None
                    m = None
                # Nennbelastung N
                if zone.name == "Kleinkinderbecken" and m is not None and k is not None:
                    N = (self.poolsInDict[zone.name]["Water volume"]) * m * k
                elif n is not None and a is not None:
                    N = (self.poolsInDict[zone.name]["Water surface"]) * n/a
                else:
                    N = None
                # Berechnung von Q
                if N is not None and k is not None:
                    Q_H = N/k
                else:
                    Q_H = 0    
                if zone.name == "Kleinkinderbecken" and self.poolsInDict[zone.name]["Water surface"] < 20 and m is not None:
                    Q_K = m * self.poolsInDict[zone.name]["Water volume"]
                else:
                    Q_K = 0
                Q_B = self.poolsInDict[zone.name]["Umfang Becken"]
                if self.poolsInDict[zone.name]["Umfang Becken"] > 40:
                    Q = max(Q_B, Q_H)
                else: 
                    Q = min(Q_H, Q_K, Q_B)
                # Umrechnung in m³/h
                Q = Q/3600
                paramRecord["Q"] = Q

                ## Q_night ##
                Q_night = self.poolsInDict[zone.name]["Aufbereitungsvolumenstrom Nachts"]
                if Q_night < Q_B:
                    Q_night = Q_B
                Q_night = Q_night/3600
                paramRecord["Q_night"] = Q_night

                ## V_storage ##
                # Parameter v_f
                if self.poolsInDict[zone.name]["Filtertyp"] == "Aktivkohlefilter mit Ozon" or self.poolsInDict[zone.name]["Filtertyp"] == "Zweischichtfilter mit Ozon":
                    v_f = 50
                elif self.poolsInDict[zone.name]["Filtertyp"] == "offener Schnellfilter":
                    v_f = 15
                elif (self.poolsInDict[zone.name]["Filtertyp"] == "geschlossener Schnellfilter" 
                or self.poolsInDict[zone.name]["Filtertyp"] == "geschlossener Sorptionsfilter" 
                or self.poolsInDict[zone.name]["Filtertyp"] == "offener Saugfilter" 
                or self.poolsInDict[zone.name]["Filtertyp"] == "Quantozonfilter" 
                or self.poolsInDict[zone.name]["Filtertyp"] == "Quarzkiesfilter" 
                or self.poolsInDict[zone.name]["Filtertyp"] == "Zweischichtfilter"):
                    if self.poolsInDict[zone.name]["Wasserart"] == "Süßwasser":
                        v_f = 30
                    else:
                        v_f = 20
                else:
                    v_f = None
                v_f = v_f/3600
                # A_Filter
                if v_f is not None:
                    A_Filter = Q/v_f
                else:
                    A_Filter = None
                # V_v
                if a is not None:
                    V_v = 0.075 * self.poolsInDict[zone.name]["Water surface"] / a
                else:
                    V_v = None
                # V_w
                if self.poolsInDict[zone.name]["Umfang Becken"] > 0:
                    V_w = 0.052 * self.poolsInDict[zone.name]["Water surface"] * 10**(-0.144*Q/self.poolsInDict[zone.name]["Umfang Becken"])
                else:
                    V_w = None
                # V_fs
                if A_Filter is not None:
                    V_fs = A_Filter * 5
                else:
                    V_fs = None
                # Berechnung V_storage
                if V_fs is not None and V_w is not None and V_v is not None:
                    V_storage = V_fs + V_v + V_w
                else:
                    V_storage = 0
                paramRecord["V_storage"] = V_storage
                
                ## beta ##
                if zone.name.startswith("Freiformbecken") or zone.name == "Mehrzweckbecken":
                    beta_inUse = 40
                else:
                    if self.poolsInDict[zone.name]["Tiefe Becken"] > 1.35:
                        beta_inUse = 28
                    else:
                        beta_inUse = 40
                beta_inUse = beta_inUse/3600
                paramRecord["beta_inUse"] = beta_inUse
                
                ## use_parialLoad ##
                paramRecord["use_partialLoad"] = self.poolsInDict[zone.name]["Nachtabsenkung"]

                ## use_poolCover ##
                paramRecord["use_poolCover"] = self.poolsInDict[zone.name]["Beckenabdeckung"]

                ## use_wavePool ##
                paramRecord["use_wavePool"] = self.poolsInDict[zone.name]["Wellenbetrieb"]
                paramRecord["h_wave"] = self.poolsInDict[zone.name]["Wellenhöhe"]
                paramRecord["w_wave"] = self.poolsInDict[zone.name]["Wellenbreite"]

                ## waterRecycling ##
                paramRecord["use_waterRecycling"] = self.poolsInDict[zone.name]["Abwasseraufbereitung"]

                ## x_recycling ##
                paramRecord["x_recycling"] = self.poolsInDict[zone.name]["Abwasseraufbereitungsgrad"]

                ## m_flow_out ##
                m_Besucher = 0.03 * 995.65 * self.poolsInDict[zone.name]["Besucherzahl"] * 1/(24*3600)
                m_Filter = 995.65 * self.poolsInDict[zone.name]["Filterspülungen"] * V_fs * 1/(7*24*3600)
                m_flow_out = max(m_Besucher, m_Filter)
                paramRecord["m_flow_out"] = m_flow_out
                
                #Sets Data to Record
                zone.paramRecord = paramRecord

        self.number_of_pools = numOfPools

        """
        The following code can be used to check the building element
        areas.            
        for zone in self.thermal_zones:
            print()
            print("For zone", zone.name, "with total area", zone.area)
            for wall in zone.outer_walls:   
                print("Outer wall with orientation", wall.name, "and element area", wall.area)
            for window in zone.windows:   
                print("Window with orientation", window.name, "and element area", window.area)
            for ground_floor in zone.ground_floors:   
                print("Groundfloor with name", ground_floor.name, "and element area", ground_floor.area)
            for floor in zone.floors:   
                print("Floor with name", floor.name, "and element area", floor.area)
            for ceiling in zone.ceilings:   
                print("Ceiling with name", ceiling.name, "and element area", ceiling.area)
            for roof in zone.rooftops:   
                print("Rooftop with name", roof.name, "and element area", roof.area)
            for wall in zone.inner_walls:   
                print("Inner wall with name", wall.name, "and element area", wall.area)
        """

    def orderPoolZones(self):
        """ Orders the Zones of Pools
        pushs the zones which are actually pools into the zone "Schwimmhalle" in the parameter "pool_zones"
        and deletes it out of the thermal zones
        """
        for id, zone in enumerate(self.thermal_zones):
            if zone.name == "Schwimmhalle":
                zone.pool_zones = list()
                ids = list()
                for id, pool in enumerate(self.thermal_zones):
                    if "becken" in pool.name:
                        zone.pool_zones.append(pool)
                        ids.append(id)
                ids.sort(reverse=True)
                for id in ids:
                    del self.thermal_zones[id]



    @property
    def office_layout(self):
        return self._office_layout

    @office_layout.setter
    def office_layout(self, value):
        if value is not None:
            self._office_layout = value
        else:
            self._office_layout = 0

    @property
    def window_layout(self):
        return self._window_layout

    @window_layout.setter
    def window_layout(self, value):
        if value is not None:
            self._window_layout = value
        else:
            self._window_layout = 0

    @property
    def construction_type(self):
        return self._construction_type

    @construction_type.setter
    def construction_type(self, value):
        if value is not None:
            if value == "heavy" or value == "light":
                self._construction_type = value
            else:
                raise ValueError("Construction_type has to be light or heavy")
        else:
            self._construction_type = "heavy"
