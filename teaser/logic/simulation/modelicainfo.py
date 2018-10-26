# created November 2015
# by TEASER4 Development Team


class ModelicaInfo():
    """ModelicaInfo Class

    This class holds information specific for Modelica Simulation. Some of
    these solver or flags might only be applicable to Dymola.


    Attributes
    ----------

    runtime_simulation : str [s]
        Total duration of simulation, default 31536000 for one year
    interval_output : str [s]
        Interval for one time step, default 3600 for one hour
    solver : list
        list of available solvers for Modelica
    current_solver : str
        solver that should be used in simulation, default 'Radau'
    simulation_start:str[s]
        Start time of simulation in s from beginning of current year
    equidistant_output : bool
        Use of Equidistant time grid flag in Modelica.
    variables_at_events : bool
        Use of events flag in Modelica.
    version : str
        Version of Modelica and Modelica Standard Library
    weekday:int[]
        day of the week for start of simulation. 0-Monday, 6-Sunday
    """

    def __init__(self):
        """Constructor of ModelicaInfo Class.
        """

        # Base-Values for the simulation tab
        self.runtime_simulation = "31536000"
        self.interval_output = "3600"
        self.weekday = 0
        self.simulation_start = "0"
        self.solver = ["Lsodar", "dassl", "Radau", "Cvode"]
        self.current_solver = "Cvode"
        self.equidistant_output = True
        self.results_at_events = False
        self.version = "3.2.2"
