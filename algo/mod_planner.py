from ortools.sat.python import cp_model
from collections import defaultdict
from utils.helpers import url_generator, int_to_days, parse_time, format_time, single_timeslot_filter, check_overlaps

class ModPlanner:
    def __init__(self, modules: list, mod_info: list, sem: str, max_hours: int, blocked_timings: dict, filtered_info: list):
        self.modules = modules
        self.mod_info = mod_info
        self.filtered_info = filtered_info
        self.sem = sem
        self.max_hours = max_hours
        self.max_mins = max_hours * 60
        self.blocked_timings = blocked_timings
        self.interval_name_map = {}
        self.hard_url = True
    
    def _add_constraints(self, hard=True):
        overlap_vars = []
        excess_lesson_vars = []

        if not hard:
            for day, blocked in self.blocked_timings.items():
                for interval, presence, _ in self.intervals_per_day[day]:
                    for block in blocked:
                        block_start, block_end = map(parse_time, block.split('-'))
                        # Define overlap variable for each interval
                        overlap_var = self.model.NewBoolVar(f'overlap_{interval.Name()}_{block}')
                        overlap_vars.append(overlap_var)

                        # Determine if the interval overlaps with the block
                        interval_start = interval.StartExpr()
                        interval_end = interval.EndExpr()

                        # Calculate if there's an overlap
                        self.model.Add(interval_start < block_end).OnlyEnforceIf(overlap_var)
                        self.model.Add(interval_end > block_start).OnlyEnforceIf(overlap_var)
                        self.model.AddImplication(overlap_var, presence)

        for day, interval_pairs in self.intervals_per_day.items():
            if len(interval_pairs) > 1:
                active_intervals = []
                daily_durations = []
                total_duration_var = self.model.NewIntVar(0, self.horizon, f'total_duration_day_{day}')
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
                self.model.Add(total_duration_var == sum(daily_durations))

                if hard:
                    self.model.Add(total_duration_var <= self.max_mins)
                else:
                    # Define excess lesson variable
                    excess_lesson_var = self.model.NewBoolVar(f'excess_lesson_day_{day}')
                    excess_lesson_vars.append(excess_lesson_var)

                    # Add constraint to calculate excess lessons
                    self.model.Add(total_duration_var > self.max_mins).OnlyEnforceIf(excess_lesson_var)

        return overlap_vars, excess_lesson_vars
    
    def _reinitialize_model(self, hard=True):
        self.model = cp_model.CpModel()
        self.intervals_per_day = defaultdict(list)
        self.starts = {}
        self.ends = {}
        self.presences = {}
        self.durations = {}
        self.all_intervals = []
        self.horizon = 0

        info_source = self.filtered_info if hard else self.mod_info

        for module_idx, module in enumerate(self.modules):
            module_data = info_source[module_idx]
            for class_type, lessons in module_data.items():
                for class_no, class_list in lessons.items():
                    presence_var = self.model.NewBoolVar(f'presence_{module}_{class_type}_{class_no}')
                    self.presences[(module_idx, class_type, class_no)] = presence_var
                    for class_instance_idx, class_info in enumerate(class_list):
                        day = class_info['day']
                        start_time = parse_time(class_info['start_time'])
                        end_time = parse_time(class_info['end_time'])
                        duration = end_time - start_time
                        self.horizon = max(self.horizon, end_time)

                        start_var = self.model.NewIntVar(0, self.horizon, f'start_{module}_{class_type}_{class_no}_{class_instance_idx}')
                        end_var = self.model.NewIntVar(0, self.horizon, f'end_{module}_{class_type}_{class_no}_{class_instance_idx}')
                        interval_var = self.model.NewIntervalVar(start_var, duration, end_var, f'interval_{module}_{class_type}_{class_no}_{class_instance_idx}')

                        self.interval_name_map[interval_var.Name()] = f'{module} {class_type} {class_no}'

                        self.starts[(module_idx, class_type, class_no, class_instance_idx)] = start_var
                        self.ends[(module_idx, class_type, class_no, class_instance_idx)] = end_var
                        self.durations[(module_idx, class_type, class_no, class_instance_idx)] = duration
                        self.intervals_per_day[day].append((interval_var, presence_var, duration))

                        self.model.Add(start_var == start_time).OnlyEnforceIf(presence_var)
                        self.model.Add(end_var == end_time).OnlyEnforceIf(presence_var)

        for module_idx, module in enumerate(self.modules):
            module_data = info_source[module_idx]
            for class_type in module_data.keys():
                class_nos = list(module_data[class_type].keys())
                presence_vars = [self.presences[(module_idx, class_type, class_no)] for class_no in class_nos]
                self.model.Add(sum(presence_vars) == 1)

        self.overlap_vars, self.excess_lesson_vars = self._add_constraints(hard=hard)
        
        if not hard:
            self.model.Minimize(sum(self.overlap_vars) + sum(self.excess_lesson_vars))
                
    def solve(self):
        # Initial solve with hard constraints
        self._reinitialize_model(hard=True)

        # Solve the model with hard constraints
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 600.0  # Allow more time for the solver
        status = solver.Solve(self.model)
        best_info = ""
        errormsg = ""

        if status != cp_model.OPTIMAL and status != cp_model.FEASIBLE:
            print("Unable to find solution with all the constraints, finding a good possible solution...\n")
            # If no solution found, reinitialize model with soft constraints to minimize overlap
            self.hard_url = False
            self._reinitialize_model(hard=False)

            best_breach = float('inf')
            best_solver = None
            best_status = None

            # Multiple runs with different seeds
            for seed in range(10):
                solver = cp_model.CpSolver()
                solver.parameters.random_seed = seed
                solver.parameters.max_time_in_seconds = 600.0  # Increase time limit
                status = solver.Solve(self.model)
                if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:  
                    current_breach_info = self.calculate_total_overlap(solver)
                    current_breach = current_breach_info[0]
                    if current_breach < best_breach:
                        best_breach = current_breach
                        best_solver = solver
                        best_status = status
                        best_info = current_breach_info[1]

            if best_solver is not None and best_status is not None:
                result = self._parse_results(best_solver, best_status)
            else:
                #Reinitialise again to find out clashes in lessons
                print("No feasible solution found with relaxed constraints.\n")
                result = ""
                single_info = single_timeslot_filter(self.mod_info) #filtering only lesson_info that only has 1 possible timing and day
                length = len(self.modules)
                for i in range(length):
                    #checking for filtered info
                    if not single_info[i]:
                        continue

                    for j in range(i+1, length):
                        if not single_info[j]:
                            continue

                        overlaps = check_overlaps(single_info[i], single_info[j])
                        if overlaps:
                            print(f"Irreconcilable clashes found between {self.modules[i]} and {self.modules[j]}:")
                            errormsg += f"\nIrreconcilable clashes found between {self.modules[i]} and {self.modules[j]}:\n"

                            for overlap in overlaps:
                                print(f"{self.modules[i]} {overlap['module1']}, clashes with {self.modules[j]} {overlap['module2']}.")
                                errormsg += f"{self.modules[i]} {overlap['module1']}, clashes with {self.modules[j]} {overlap['module2']}.\n\n"
        else:
            result = self._parse_results(solver, status)

        print(best_info)
        return (result, best_info, errormsg)

    def _parse_results(self, solver, status):
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            url_info = [[] for _ in range(len(self.modules))]
            info_source = self.filtered_info if self.hard_url else self.mod_info
            for module_idx, module in enumerate(self.modules):
                for class_type in info_source[module_idx].keys():
                    for class_no in info_source[module_idx][class_type].keys():
                        if solver.Value(self.presences[(module_idx, class_type, class_no)]):
                            url_info[module_idx].append(f"{class_type}:{class_no},")
                            for class_instance_idx, class_info in enumerate(info_source[module_idx][class_type][class_no]):
                                start = solver.Value(self.starts[(module_idx, class_type, class_no, class_instance_idx)])
                                end = solver.Value(self.ends[(module_idx, class_type, class_no, class_instance_idx)])
                                day = class_info['day']
                                start_time = format_time(start)
                                end_time = format_time(end)
                                print(f"Module {module}, {class_type} {class_no}: Day {day}, starts at {start_time} and ends at {end_time}")
            print("\nStatistics")
            print(f"  - conflicts      : {solver.NumConflicts()}")
            print(f"  - branches       : {solver.NumBranches()}")
            print(f"  - wall time      : {solver.WallTime()} s")
            return url_generator(self.modules, url_info, self.sem)
        else:
            print("No solution found.")

        print("\nStatistics")
        print(f"  - conflicts      : {solver.NumConflicts()}")
        print(f"  - branches       : {solver.NumBranches()}")
        print(f"  - wall time      : {solver.WallTime()} s")

        return ""
    
    def calculate_total_overlap(self, solver):
        if not (solver.StatusName() == 'OPTIMAL' or solver.StatusName() == 'FEASIBLE'):  
            return (float('inf'), 'Solver did not find a feasible solution.')
        total_overlap = 0
        total_excess_lessons = 0
        overlap_info = "\nLessons that overlap with blocked days or timings:\n\n"
        excess_info = ""
        
        sorted_days = sorted(self.intervals_per_day.keys())

        for day in sorted_days:
            intervals = self.intervals_per_day[day]
            blocked = self.blocked_timings.get(day, [])
            total_duration = 0
            day_excess_info = f'Lessons exceeding attention span limiter of {self.max_hours} on {int_to_days(day)}:\n'
            for interval, presence, duration in intervals:
                if solver.BooleanValue(presence):
                    interval_start = solver.Value(interval.StartExpr())
                    interval_end = solver.Value(interval.EndExpr())
                    
                    # Check for overlaps with blocked timings
                    for block in blocked:
                        block_start, block_end = map(parse_time, block.split('-'))
                        if block == '0000-2359':
                            block_string = 'blocked day'
                        else:
                            block_string = f'blocked timing {block}'
                        if interval_start < block_end and interval_end > block_start:
                            total_overlap += 1
                            interval_name = self.interval_name_map[interval.Name()]
                            overlap_info += f'{interval_name} overlaps with {block_string} on {int_to_days(day)}.\n'
                    
                    # Check for excess duration
                    total_duration += duration
                    if total_duration > self.max_mins:
                        total_excess_lessons += 1
                        interval_name = self.interval_name_map[interval.Name()]
                        day_excess_info += f'{interval_name}\n'

            if total_duration > self.max_mins:
                excess_info += day_excess_info + '\n'

        if total_overlap:
            overlap_info += f'\nTotal overlapping classes: {total_overlap}\n\n'
        else:
            overlap_info = '\nNo classes that overlaps with blocked day or timings.\n\n'

        if total_excess_lessons:
            excess_info += f'Total lessons exceeding maximum number of lesson hours: {total_excess_lessons}\n'
        else:
            excess_info = 'No classes that exceeds the maximum lesson hours a day.\n'

        #Final check in case hard constraints algorithm did not run correctly
        total_breach = total_overlap + total_excess_lessons
        if total_breach:
            return (total_breach, overlap_info + excess_info)
        else:
            return (0, "")
        