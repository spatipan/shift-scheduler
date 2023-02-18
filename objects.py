# Availability class, define the availability of each person
# list of datetime interval, each interval is a tuple of (start, end)
# start and end are datetime object
# Availability can be combined by using the + operator if intervals overlap, they will be combined into one interval
# Availability can be subtracted by using the - operator, the result will be the availability of the first object minus the availability of the second object

class Availability():
    """Availability class, define the availability of each person
    list of datetime interval, each interval is a tuple of (start, end)
    start and end are datetime object
    Availability can be combined by using the + operator if intervals overlap, they will be combined into one interval
    Availability can be subtracted by using the - operator, the result will be the availability of the first object minus the availability of the second object
    """


    def __init__(self, intervals):
        self.intervals = intervals

    def __add__(self, other):
        intervals = self.intervals + other.intervals
        intervals.sort(key=lambda x: x[0])
        new_intervals = [intervals[0]]
        for i in range(1, len(intervals)):
            if intervals[i][0] <= new_intervals[-1][1]:
                new_intervals[-1] = (new_intervals[-1][0], max(intervals[i][1], new_intervals[-1][1]))
            else:
                new_intervals.append(intervals[i])
        return Availability(new_intervals)

    def __sub__(self, other):
        intervals = self.intervals
        for interval in other.intervals:
            new_intervals = []
            for i in range(len(intervals)):
                if intervals[i][1] <= interval[0] or intervals[i][0] >= interval[1]:
                    new_intervals.append(intervals[i])
                elif intervals[i][0] < interval[0] and intervals[i][1] > interval[1]:
                    new_intervals.append((intervals[i][0], interval[0]))
                    new_intervals.append((interval[1], intervals[i][1]))
                elif intervals[i][0] < interval[0] and intervals[i][1] <= interval[1]:
                    new_intervals.append((intervals[i][0], interval[0]))
                elif intervals[i][0] >= interval[0] and intervals[i][1] > interval[1]:
                    new_intervals.append((interval[1], intervals[i][1]))
            intervals = new_intervals
        return Availability(intervals)

    def get_hours(self):
        hours = 0
        for interval in self.intervals:
            hours += (interval[1] - interval[0]).total_seconds() / 3600
        return hours

    # Plot the availability
    def plot(self):
        df = pd.DataFrame(columns=['Task', 'Start', 'Finish', 'Resource'])
        for i in range(len(self.intervals)):
            df.loc[i] = ['Task', self.intervals[i][0], self.intervals[i][1], 'Resource']
        fig = ff.create_gantt(df, index_col='Resource', show_colorbar=True, group_tasks=True)
        fig.show()

