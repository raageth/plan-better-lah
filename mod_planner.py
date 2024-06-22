from ortools.sat.python import cp_model
import collections
from utils.helpers import url_generator

class ModPlanner:
    def __init__(self, modules: list, mod_info: list, sem: str) -> None:
        self.modules = modules
        self.mod_info = mod_info
        self.sem = sem

    def solve(self) -> str:
        # Model initialization
        model = cp_model.CpModel()

        # Global storage of variables
        intervals_per_day = collections.defaultdict(list)
        starts = {}  # indexed by (module_idx, class_type, class_no, class_instance_idx)
        ends = {}
        presences = {}  # indexed by (module_idx, class_type, class_no)
        all_intervals = []
        horizon = 0

        # Parsing mod_info and creating variables
        for module_idx, module in enumerate(self.modules):
            module_data = self.mod_info[module_idx]
            for class_type, lessons in module_data.items():
                for class_no, class_list in lessons.items():
                    presence_var = model.NewBoolVar(f'presence_{module}_{class_type}_{class_no}')
                    presences[(module_idx, class_type, class_no)] = presence_var
                    for class_instance_idx, class_info in enumerate(class_list):
                        day = class_info['day']
                        start_time = int(class_info['start_time'])
                        end_time = int(class_info['end_time'])
                        duration = end_time - start_time
                        horizon = max(horizon, end_time)

                        # Create interval variable
                        start_var = model.NewIntVar(0, horizon, f'start_{module}_{class_type}_{class_no}_{class_instance_idx}')
                        end_var = model.NewIntVar(0, horizon, f'end_{module}_{class_type}_{class_no}_{class_instance_idx}')
                        interval_var = model.NewIntervalVar(start_var, duration, end_var, f'interval_{module}_{class_type}_{class_no}_{class_instance_idx}')

                        starts[(module_idx, class_type, class_no, class_instance_idx)] = start_var
                        ends[(module_idx, class_type, class_no, class_instance_idx)] = end_var
                        intervals_per_day[day].append((interval_var, presence_var))

                        # Add presence constraints
                        model.Add(start_var == start_time).OnlyEnforceIf(presence_var)
                        model.Add(end_var == end_time).OnlyEnforceIf(presence_var)

        # Each module should have exactly one class_no selected for each class_type
        for module_idx, module in enumerate(self.modules):
            module_data = self.mod_info[module_idx]
            for class_type in module_data.keys():
                class_nos = list(module_data[class_type].keys())
                presence_vars = [presences[(module_idx, class_type, class_no)] for class_no in class_nos]
                model.Add(sum(presence_vars) == 1)

        # Apply No-Overlap constraint across all intervals on the same day, enforcing only if presence variable is true
        for day, interval_pairs in intervals_per_day.items():
            if len(interval_pairs) > 1:
                active_intervals = []
                for interval, presence in interval_pairs:
                    active_interval = model.NewOptionalIntervalVar(interval.StartExpr(), interval.SizeExpr(), interval.EndExpr(), presence, f'active_{interval.Name()}')
                    active_intervals.append(active_interval)
                model.AddNoOverlap(active_intervals)

        # Solve the model
        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        # Print the solution
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            url_info = [[] for _ in range(len(self.modules))]
            for module_idx, module in enumerate(self.modules):
                for class_type in self.mod_info[module_idx].keys():
                    for class_no in self.mod_info[module_idx][class_type].keys():
                        if solver.Value(presences[(module_idx, class_type, class_no)]):
                            url_info[module_idx].append(f"{class_type}:{class_no},")
                            for class_instance_idx, class_info in enumerate(self.mod_info[module_idx][class_type][class_no]):
                                start = solver.Value(starts[(module_idx, class_type, class_no, class_instance_idx)])
                                end = solver.Value(ends[(module_idx, class_type, class_no, class_instance_idx)])
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

# modules = ['CS1101S', 'MA1521', 'MA1522', 'IS1108', 'GEA1000']
# mod_info = [
#     {'TUT': {'05': [{'day': 1, 'start_time': '1400', 'end_time': '1600'}], '04': [{'day': 2, 'start_time': '1200', 'end_time': '1400'}], '06': [{'day': 2, 'start_time': '1400', 'end_time': '1600'}], '02': [{'day': 2, 'start_time': '1000', 'end_time': '1200'}]}, 
#      'REC': {'02': [{'day': 4, 'start_time': '1100', 'end_time': '1200'}], '01': [{'day': 4, 'start_time': '1000', 'end_time': '1100'}]}, 
#      'LEC': {'1': [{'day': 3, 'start_time': '1200', 'end_time': '1400'}]}}, 
#     {'TUT': {'19': [{'day': 4, 'start_time': '1200', 'end_time': '1300'}], '20': [{'day': 4, 'start_time': '1300', 'end_time': '1400'}], '7': [{'day': 2, 'start_time': '0900', 'end_time': '1000'}], 
#      '16': [{'day': 4, 'start_time': '0900', 'end_time': '1000'}], '17': [{'day': 4, 'start_time': '1000', 'end_time': '1100'}], '18': [{'day': 4, 'start_time': '1100', 'end_time': '1200'}], 
#      '21': [{'day': 5, 'start_time': '1400', 'end_time': '1500'}], '22': [{'day': 5, 'start_time': '1500', 'end_time': '1600'}], '24': [{'day': 5, 'start_time': '1700', 'end_time': '1800'}], 
#      '8': [{'day': 2, 'start_time': '1400', 'end_time': '1500'}], '9': [{'day': 2, 'start_time': '1500', 'end_time': '1600'}], '11': [{'day': 2, 'start_time': '1700', 'end_time': '1800'}], 
#      '12': [{'day': 3, 'start_time': '0900', 'end_time': '1000'}], '13': [{'day': 3, 'start_time': '1000', 'end_time': '1100'}], '15': [{'day': 3, 'start_time': '1300', 'end_time': '1400'}], 
#      '1': [{'day': 1, 'start_time': '0900', 'end_time': '1000'}], '2': [{'day': 1, 'start_time': '1000', 'end_time': '1100'}], '3': [{'day': 1, 'start_time': '1100', 'end_time': '1200'}], 
#      '4': [{'day': 1, 'start_time': '1200', 'end_time': '1300'}], '5': [{'day': 1, 'start_time': '1600', 'end_time': '1700'}], '6': [{'day': 1, 'start_time': '1700', 'end_time': '1800'}], 
#      '10': [{'day': 2, 'start_time': '1600', 'end_time': '1700'}], '23': [{'day': 5, 'start_time': '1600', 'end_time': '1700'}], '14': [{'day': 3, 'start_time': '1200', 'end_time': '1300'}]}, 
#      'LEC': {'2': [{'day': 4, 'start_time': '1400', 'end_time': '1600'}, {'day': 1, 'start_time': '1400', 'end_time': '1600'}], 
#      '1': [{'day': 5, 'start_time': '1000', 'end_time': '1200'}, {'day': 2, 'start_time': '1000', 'end_time': '1200'}]}}, 
#     {'TUT': {'2': [{'day': 1, 'start_time': '1200', 'end_time': '1300'}], '3': [{'day': 1, 'start_time': '1400', 'end_time': '1500'}], '7': [{'day': 2, 'start_time': '1300', 'end_time': '1400'}], 
#      '5': [{'day': 2, 'start_time': '1100', 'end_time': '1200'}], '8': [{'day': 2, 'start_time': '1400', 'end_time': '1500'}], '10': [{'day': 3, 'start_time': '0900', 'end_time': '1000'}], 
#      '11': [{'day': 3, 'start_time': '1000', 'end_time': '1100'}], '17': [{'day': 5, 'start_time': '1000', 'end_time': '1100'}], '18': [{'day': 5, 'start_time': '1100', 'end_time': '1200'}], 
#      '13': [{'day': 3, 'start_time': '1200', 'end_time': '1300'}], '14': [{'day': 3, 'start_time': '1300', 'end_time': '1400'}], '15': [{'day': 4, 'start_time': '1200', 'end_time': '1300'}], 
#      '16': [{'day': 4, 'start_time': '1300', 'end_time': '1400'}], '1': [{'day': 1, 'start_time': '1100', 'end_time': '1200'}], '4': [{'day': 1, 'start_time': '1500', 'end_time': '1600'}], 
#      '6': [{'day': 2, 'start_time': '1200', 'end_time': '1300'}], '9': [{'day': 2, 'start_time': '1500', 'end_time': '1600'}], '12': [{'day': 3, 'start_time': '1100', 'end_time': '1200'}]}, 
#      'LEC': {'2': [{'day': 2, 'start_time': '0800', 'end_time': '1000'}, {'day': 4, 'start_time': '0800', 'end_time': '1000'}], 
#      '1': [{'day': 1, 'start_time': '1600', 'end_time': '1800'}, {'day': 4, 'start_time': '1600', 'end_time': '1800'}]}}, 
#     {'TUT': {'13': [{'day': 3, 'start_time': '1300', 'end_time': '1500'}], '14': [{'day': 3, 'start_time': '1400', 'end_time': '1600'}], '06': [{'day': 1, 'start_time': '1400', 'end_time': '1600'}], 
#      '11': [{'day': 3, 'start_time': '1100', 'end_time': '1300'}], '01': [{'day': 1, 'start_time': '0900', 'end_time': '1100'}], '02': [{'day': 1, 'start_time': '1000', 'end_time': '1200'}], 
#      '25': [{'day': 3, 'start_time': '0900', 'end_time': '1100'}], '26': [{'day': 3, 'start_time': '1500', 'end_time': '1700'}], '05': [{'day': 1, 'start_time': '1300', 'end_time': '1500'}], 
#      '08': [{'day': 1, 'start_time': '1600', 'end_time': '1800'}], '10': [{'day': 3, 'start_time': '1000', 'end_time': '1200'}], '20': [{'day': 1, 'start_time': '1500', 'end_time': '1700'}], 
#      '04': [{'day': 1, 'start_time': '1200', 'end_time': '1400'}], '12': [{'day': 3, 'start_time': '1200', 'end_time': '1400'}], '16': [{'day': 3, 'start_time': '1600', 'end_time': '1800'}]}, 
#      'LEC': {'1': [{'day': 5, 'start_time': '1200', 'end_time': '1400'}]}}, 
#     {'TUT': {'D20': [{'day': 4, 'start_time': '1500', 'end_time': '1800'}], 'D26': [{'day': 3, 'start_time': '0900', 'end_time': '1200'}], 'D28': [{'day': 3, 'start_time': '1500', 'end_time': '1800'}], 
#      'E19': [{'day': 1, 'start_time': '0900', 'end_time': '1200'}], 'D14': [{'day': 2, 'start_time': '1500', 'end_time': '1800'}], 'D32': [{'day': 5, 'start_time': '1200', 'end_time': '1500'}], 
#      'D54': [{'day': 5, 'start_time': '1500', 'end_time': '1800'}], 'D05': [{'day': 3, 'start_time': '1200', 'end_time': '1500'}], 'E22': [{'day': 2, 'start_time': '0900', 'end_time': '1200'}], 
#      'E23': [{'day': 2, 'start_time': '1200', 'end_time': '1500'}], 'E03': [{'day': 1, 'start_time': '1500', 'end_time': '1800'}], 'D30': [{'day': 4, 'start_time': '1200', 'end_time': '1500'}], 
#      'D29': [{'day': 4, 'start_time': '0900', 'end_time': '1200'}], 'E08': [{'day': 1, 'start_time': '1200', 'end_time': '1500'}]}}
# ]

# planner = ModPlanner(modules, mod_info, 2)
# planner.solve()
