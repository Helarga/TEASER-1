"""Module to test UseCondition functions."""
import os

import pytest
import helptest
import pandas as pd
import json
from pathlib import Path

from teaser.logic import utilities
from teaser.project import Project

prj = Project(True)


class Test_useconditions(object):
    """Unit Tests for TEASER."""

    global prj

    def test_load_use_conditions_new(self):
        """Test of load_use_conditions, no parameter checking."""
        prj.set_default()
        helptest.building_test2(prj)
        use_cond = prj.buildings[-1].thermal_zones[-1].use_conditions
        use_cond.load_use_conditions("Living", data_class=prj.data)

    def test_save_use_conditions(self):
        """Test of save_use_conditions, no parameter checking."""
        try:
            os.remove(os.path.join(utilities.get_default_path(), "UseCondUT.json"))
        except OSError:
            pass
        path = os.path.join(utilities.get_default_path(), "UseCondUT.json")
        prj.data.path_uc = path
        prj.data.load_uc_binding()
        use_cond = prj.buildings[-1].thermal_zones[-1].use_conditions
        use_cond.save_use_conditions(data_class=prj.data)

    def test_save_duplicate_use_conditions(self):
        """Test of save_use_conditions, no parameter checking."""

        use_cond = prj.buildings[-1].thermal_zones[-1].use_conditions
        use_cond.save_use_conditions(data_class=prj.data)
        assert len(prj.data.conditions_bind.keys()) == 2
        use_cond.usage = "UnitTest"
        use_cond.save_use_conditions(data_class=prj.data)
        assert len(prj.data.conditions_bind.keys()) == 3

    def test_ahu_profiles(self):
        """Test setting AHU profiles of different lengths

        Related to issue 553 at https://github.com/RWTH-EBC/TEASER/issues/553
        """

        prj_test = Project(load_data=True)
        prj_test.name = "TestAHUProfiles"

        prj_test.add_non_residential(
            method="bmvbs",
            usage="office",
            name="OfficeBuilding",
            year_of_construction=2015,
            number_of_floors=4,
            height_of_floors=3.5,
            net_leased_area=1000.0,
        )

        prj_test.used_library_calc = "AixLib"
        prj_test.number_of_elements_calc = 2

        heating_profile_workday = [
            293,
            293,
            293,
            293,
            293,
            293,
            293,
            293,
            293,
            293,
            293,
            293,
            293,
            293,
            293,
            293,
            293,
            293,
            293,
            293,
            293,
            293,
            293,
            293,
        ]

        heating_profile_week = []
        for day in range(7):
            for val in heating_profile_workday:
                if day < 5:
                    set_point = val
                else:
                    set_point = 290.0
                heating_profile_week.append(set_point)

        for zone in prj_test.buildings[-1].thermal_zones:
            zone.use_conditions.heating_profile = heating_profile_week
            zone.use_conditions.cooling_profile = heating_profile_week
            zone.use_conditions.persons_profile = heating_profile_week
            zone.use_conditions.machines_profile = heating_profile_week
            zone.use_conditions.lighting_profile = heating_profile_week
        assert (
            prj_test.buildings[-1].thermal_zones[-1].use_conditions.heating_profile
            == heating_profile_week
        )
        assert (
            prj_test.buildings[-1].thermal_zones[-1].use_conditions.cooling_profile
            == heating_profile_week
        )
        assert (
            prj_test.buildings[-1].thermal_zones[-1].use_conditions.persons_profile
            == heating_profile_week
        )
        assert (
            prj_test.buildings[-1].thermal_zones[-1].use_conditions.machines_profile
            == heating_profile_week
        )
        assert (
            prj_test.buildings[-1].thermal_zones[-1].use_conditions.lighting_profile
            == heating_profile_week
        )

    def test_ahu_threshold_true(self):
        prj.set_default()
        helptest.building_test2(prj)
        use_cond = prj.buildings[-1].thermal_zones[-1].use_conditions
        use_cond.with_ahu = True
        use_cond.with_ideal_thresholds = True

    def test_ahu_threshold_false(self):
        prj.set_default()
        helptest.building_test2(prj)
        use_cond = prj.buildings[-1].thermal_zones[-1].use_conditions
        use_cond.with_ahu = False
        with pytest.raises(Exception):
            use_cond.with_ideal_thresholds = True

    def test_profile_adjust_opening_times(self):
        prj.set_default()
        helptest.building_test2(prj)
        use_cond = prj.buildings[-1].thermal_zones[-1].use_conditions
        profile_before = use_cond.machines_profile
        use_cond.adjusted_opening_times = [10, 15]
        use_cond.calc_adj_schedules()
        schedules = use_cond.schedules
        profile_after = use_cond.machines_profile
        assert (profile_after[8] != profile_before[8])
        assert (profile_after[7] != profile_before[7])
        assert (profile_after[9] == profile_before[9])
        assert (profile_after[8] == 0.0)
        assert (isinstance(schedules, pd.DataFrame))

    def test_profile_adjust_weekend_profiles(self):
        prj.set_default()
        helptest.building_test2(prj)
        use_cond = prj.buildings[-1].thermal_zones[-1].use_conditions
        profile_before = use_cond.machines_profile
        use_cond.first_saturday_of_year = 4
        use_cond.profiles_weekend_factor = 0.4
        use_cond.calc_adj_schedules()
        schedules = use_cond.schedules
        profile_after = use_cond.machines_profile
        assert (profile_after[81] != profile_before[9])
        assert (profile_after[105] != profile_before[9])
        assert (
            profile_after[105]
            == profile_before[9] * use_cond.profiles_weekend_factor
        )
        assert (isinstance(schedules, pd.DataFrame))

    def test_profile_setback(self):
        prj.set_default()
        helptest.building_test2(prj)
        use_cond = prj.buildings[-1].thermal_zones[-1].use_conditions
        profile_heating_before = use_cond.heating_profile
        profile_cooling_before = use_cond.cooling_profile
        use_cond.set_back_times = [5, 22]
        use_cond.heating_set_back = -2
        use_cond.cooling_set_back = 3
        use_cond.calc_adj_schedules()
        schedules = use_cond.schedules
        profile_heating_after = use_cond.heating_profile
        profile_cooling_after = use_cond.cooling_profile
        assert (profile_heating_after[4] != profile_heating_before[4])
        assert (
                profile_heating_after[4]
                == profile_heating_before[4] + use_cond.heating_set_back
        )
        assert (profile_cooling_after[4] != profile_cooling_before[4])
        assert (
                profile_cooling_after[4]
                == profile_cooling_before[4] + use_cond.cooling_set_back
        )
        assert (isinstance(schedules, pd.DataFrame))


    def test_use_maintained_illuminance(self):
        #pass
        # TODO
        # Test in which bool use_maintained_illuminance is set to TRUE, FALSE and NONE.
        # If True: check if lighting_power == maintained_illuminance / lighting_efficiency_lumen
        # If False or NONE: check if lighting_power == lighting_power

        project_dir = Path(__file__).parent.parent
        json_path = Path(project_dir, 'teaser', 'data', 'input', 'inputdata', 'UseConditions.json')

        # use_maintained_illuminance == True
        with open(fr"D:\dja-jho\Git\TEASER\teaser\data\input\inputdata\UseConditions.json", 'r') as json_file:
            data = json.load(json_file)

        data["Living"]["use_maintained_illuminance"] = True

        with open(json_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)

        prj_test_1 = Project(True)
        prj_test_1.set_default()
        helptest.building_test2(prj_test_1)
        use_cond = prj_test_1.buildings[-1].thermal_zones[-1].use_conditions
        use_cond.load_use_conditions("Living", data_class=prj_test_1.data)

        assert (use_cond.lighting_power == use_cond.maintained_illuminance / use_cond.lighting_efficiency_lumen)


        # use_maintained_illuminance == False
        with open(json_path, 'r') as json_file:
            data = json.load(json_file)

        data["Living"]["use_maintained_illuminance"] = False
        lighting_power_test = 10
        data["Living"]["lighting_power"] = lighting_power_test

        with open(json_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)

        use_cond = prj.buildings[-1].thermal_zones[-1].use_conditions
        use_cond.load_use_conditions("Living", data_class=prj.data)

        assert (use_cond.lighting_power == lighting_power_test)


        # use_maintained_illuminance == None
        with open(json_path, 'r') as json_file:
            data = json.load(json_file)

        data["Living"]["use_maintained_illuminance"] = False
        lighting_power_test = 10
        data["Living"]["lighting_power"] = lighting_power_test

        with open(json_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)

        use_cond = prj.buildings[-1].thermal_zones[-1].use_conditions
        use_cond.load_use_conditions("Living", data_class=prj.data)

        assert (use_cond.lighting_power == lighting_power_test)


    def test(self):
        prj = Project(True)
        prj.set_default()
        helptest.building_test2(prj)
        use_cond = prj.buildings[-1].thermal_zones[-1].use_conditions
        use_cond.load_use_conditions("Living", data_class=prj.data)

        use_cond.use_maintained_illuminance = True
        test1 = use_cond.lighting_power
        print(test1)

        use_cond.use_maintained_illuminance = False
        test1 = use_cond.lighting_power
        print(test1)




