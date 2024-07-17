from ortools.sat.python import cp_model
from collections import defaultdict
from utils.helpers import url_generator

class ModPlanner:
    def __init__(self, modules: list, mod_info: list, sem: str, max_hours: int):
        self.modules = modules
        self.mod_info = mod_info
        self.sem = sem
        self.max_mins = max_hours * 60

    def _parse_time(self, time_str):
        """Convert time in HHMM format to minutes since midnight."""
        hours = int(time_str[:2])
        minutes = int(time_str[2:])
        return hours * 60 + minutes
    
    def solve(self) -> str:
        # Model initialization
        self.model = cp_model.CpModel()

        # Global storage of variables
        self.intervals_per_day = defaultdict(list)
        self.starts = {}  # indexed by (module_idx, class_type, class_no, class_instance_idx)
        self.ends = {}
        self.presences = {}  # indexed by (module_idx, class_type, class_no)
        self.durations = {}
        self.all_intervals = []
        self.horizon = 0

        # Parsing mod_info and creating variables
        for module_idx, module in enumerate(self.modules):
            module_data = self.mod_info[module_idx]
            for class_type, lessons in module_data.items():
                for class_no, class_list in lessons.items():
                    presence_var = self.model.NewBoolVar(f'presence_{module}_{class_type}_{class_no}')
                    self.presences[(module_idx, class_type, class_no)] = presence_var
                    for class_instance_idx, class_info in enumerate(class_list):
                        day = class_info['day']
                        start_time = self._parse_time(class_info['start_time'])
                        end_time = self._parse_time(class_info['end_time'])
                        duration = end_time - start_time
                        self.horizon = max(self.horizon, end_time)

                        # Create interval variable
                        start_var = self.model.NewIntVar(0, self.horizon, f'start_{module}_{class_type}_{class_no}_{class_instance_idx}')
                        end_var = self.model.NewIntVar(0, self.horizon, f'end_{module}_{class_type}_{class_no}_{class_instance_idx}')
                        interval_var = self.model.NewIntervalVar(start_var, duration, end_var, f'interval_{module}_{class_type}_{class_no}_{class_instance_idx}')

                        self.starts[(module_idx, class_type, class_no, class_instance_idx)] = start_var
                        self.ends[(module_idx, class_type, class_no, class_instance_idx)] = end_var
                        self.durations[(module_idx, class_type, class_no, class_instance_idx)] = duration
                        self.intervals_per_day[day].append((interval_var, presence_var, duration))

                        # Add presence constraints
                        self.model.Add(start_var == start_time).OnlyEnforceIf(presence_var)
                        self.model.Add(end_var == end_time).OnlyEnforceIf(presence_var)

        # Each module should have exactly one class_no selected for each class_type
        for module_idx, module in enumerate(self.modules):
            module_data = self.mod_info[module_idx]
            for class_type in module_data.keys():
                class_nos = list(module_data[class_type].keys())
                presence_vars = [self.presences[(module_idx, class_type, class_no)] for class_no in class_nos]
                self.model.Add(sum(presence_vars) == 1)

        # Apply No-Overlap constraint across all intervals on the same day, enforcing only if presence variable is true
        for day, interval_pairs in self.intervals_per_day.items():
            if len(interval_pairs) > 1:
                active_intervals = []
                daily_durations = []

                for interval, presence, duration in interval_pairs:
                    active_interval = self.model.NewOptionalIntervalVar(
                        interval.StartExpr(), 
                        interval.SizeExpr(), 
                        interval.EndExpr(), presence, 
                        f'active_{interval.Name()}'
                    )
                    active_intervals.append(active_interval)
                    daily_durations.append(duration * presence)

                self.model.AddNoOverlap(active_intervals)
                
                self.model.Add(sum(daily_durations) <= self.max_mins)

        # Solve the model
        solver = cp_model.CpSolver()
        status = solver.Solve(self.model)
        result = self._parse_results(solver, status)
        return result

    def _parse_results(self, solver, status):
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            url_info = [[] for _ in range(len(self.modules))]
            for module_idx, module in enumerate(self.modules):
                for class_type in self.mod_info[module_idx].keys():
                    for class_no in self.mod_info[module_idx][class_type].keys():
                        if solver.Value(self.presences[(module_idx, class_type, class_no)]):
                            url_info[module_idx].append(f"{class_type}:{class_no},")
                            for class_instance_idx, class_info in enumerate(self.mod_info[module_idx][class_type][class_no]):
                                start = solver.Value(self.starts[(module_idx, class_type, class_no, class_instance_idx)])
                                end = solver.Value(self.ends[(module_idx, class_type, class_no, class_instance_idx)])
                                day = class_info['day']
                                print(f"Module {module}, {class_type} {class_no}: Day {day}, starts at {start} and ends at {end}")
            return url_generator(self.modules, url_info, self.sem)
        else:
            print("No solution found.")

        print("\nStatistics")
        print(f"  - conflicts      : {solver.NumConflicts()}")
        print(f"  - branches       : {solver.NumBranches()}")
        print(f"  - wall time      : {solver.WallTime()} s")

        return ""