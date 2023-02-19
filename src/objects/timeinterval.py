from datetime import datetime, timedelta
import pandas as pd
from bisect import bisect_left, bisect_right
import numpy as np
import plotly.express as px
import unittest

class TimeInterval:
    """
    A class representing a time interval with a start and end time.

    Attributes:
    - start_time (int): the start time of the interval
    - end_time (int): the end time of the interval
    """

    def __init__(self, start_time: datetime, end_time: datetime):
        """
        Initializes a TimeInterval with a given start and end time.
        Raises a ValueError if end_time is less than or equal to start_time.

        Args:
        - start_time (int): the start time of the interval
        - end_time (int): the end time of the interval
        """
        if end_time <= start_time:
            raise ValueError('end_time must be greater than start_time')

        self.start_time = start_time
        self.end_time = end_time

    def __repr__(self):
        return f'TimeInterval({self.start_time}, {self.end_time})'

    def __str__(self):
        return f'{self.start_time} - {self.end_time}'

    def __eq__(self, other):
        return self.start_time == other.start_time and self.end_time == other.end_time

    def __lt__(self, other):
        return self.end_time <= other.start_time

    def __gt__(self, other):
        return self.start_time >= other.end_time

    def __add__(self, other):
        if self > other:
            return TimeIntervals([other, self])
        elif self < other:
            return TimeIntervals([self, other])
        else:
            return TimeIntervals([self])

    def __sub__(self, other):
        if self == other:
            return TimeIntervals([])
        elif self < other:
            return TimeIntervals([self])
        elif self > other:
            return TimeIntervals([TimeInterval(other.end_time, self.end_time)])

    def duration(self) -> int:
        """
        Returns the duration of the time interval as the difference between the end and start times.

        Returns:
        - The duration of the time interval as an int.
        """
        return self.end_time - self.start_time
    

    def contains(self, other):
        return self.start_time <= other.start_time and self.end_time >= other.end_time

    def overlap(self, other: 'TimeInterval') -> bool:
        """
        Returns True if the current time interval overlaps with the other time interval.

        Args:
        - other (TimeInterval): the other time interval to check for overlap

        Returns:
        - True if the current time interval overlaps with the other time interval, False otherwise
        """
        return (self.start_time < other.end_time) and (other.start_time < self.end_time)


class TimeIntervals:
    """
    A class representing a list of time intervals. Each interval is represented as an instance of the TimeInterval class.
    
    Attributes:
    -----------
    intervals : List[TimeInterval]
        A list of TimeInterval instances representing the time intervals.
        
    Methods:
    --------
    __init__(intervals: List[TimeInterval])
        Initializes a new instance of the TimeIntervals class with the specified list of intervals.
        
    __repr__() -> str
        Returns a string representation of the TimeIntervals instance.
        
    __str__() -> str
        Returns a string representation of the TimeIntervals instance.
        
    __add__(other: TimeIntervals) -> TimeIntervals
        Adds the intervals of another TimeIntervals instance to this instance and returns a new TimeIntervals instance.
        
    __sub__(other: TimeIntervals) -> TimeIntervals
        Subtracts the intervals of another TimeIntervals instance from this instance and returns a new TimeIntervals instance.
        
    combine_intervals(intervals: List[TimeInterval]) -> List[TimeInterval]
        Combines a list of overlapping intervals into a list of non-overlapping intervals and returns the result.
        
    visualize_gantt()
        Generates a Gantt chart visualization of the time intervals using Plotly.
    """

    def __init__(self, intervals):
        """
        Initializes a TimeIntervals object with a list of non-overlapping TimeInterval objects.

        Args:
        - intervals (List[TimeInterval]): a list of non-overlapping TimeInterval objects.
        """
        self.intervals = self.combine_intervals(intervals)

    def __repr__(self):
        return f'TimeIntervals({self.intervals})'

    def __str__(self):
        return ', '.join(str(interval) for interval in self.intervals)

    def __add__(self, other):
        intervals = self.intervals + other.intervals
        return TimeIntervals(intervals)

    def __sub__(self, other):
        intervals = self.intervals + other.intervals
        events = []
        for interval in intervals:
            events.append((interval.start_time, 1))
            events.append((interval.end_time, -1))
        events.sort()
        result_intervals = []
        count = 0
        start_time = None
        for time, delta in events:
            if count == 0 and start_time is not None:
                result_intervals.append(TimeInterval(start_time, time))
            count += delta
            if count == 0:
                start_time = None
            else:
                start_time = time
        return TimeIntervals(result_intervals)


    def contains(self, interval):
        """
        Returns True if the current time intervals contain the specified time interval.

        Args:
        - interval (TimeInterval): the time interval to check for containment

        Returns:
        - True if the current time intervals contain the specified time interval, False otherwise
        """
        for iv in self.intervals:
            if iv.contains(interval):
                return True
        return False
    
    def overlap(self, other: 'TimeIntervals') -> bool:
        """
        Returns True if the current time intervals overlap with the other time intervals.

        Args:
        - other (TimeIntervals): the other time intervals to check for overlap

        Returns:
        - True if the current time intervals overlap with the other time intervals, False otherwise
        """
        for interval in self.intervals:
            for other_interval in other.intervals:
                if interval.overlap(other_interval):
                    return True
        return False

    def duration(self) -> int:
        """
        Returns the total duration of the time intervals as the sum of the durations of the individual intervals.

        Returns:
        - The total duration of the time intervals as an int.
        """
        return sum(interval.duration().total_seconds() for interval in self.intervals)

    @staticmethod
    def combine_intervals(intervals):
        intervals.sort(key=lambda x: x.start_time)
        merged_intervals = []
        for interval in intervals:
            idx = bisect_right(merged_intervals, interval)
            if idx == 0 or interval.start_time > merged_intervals[idx-1].end_time:
                merged_intervals.insert(idx, interval)
            else:
                merged_intervals[idx-1].end_time = max(merged_intervals[idx-1].end_time, interval.end_time)
        return merged_intervals

    def visualize_gantt(self):
        """
        Generates a Gantt chart visualization of the time intervals using Plotly.
        """
        # Combine intervals into a single interval
        combined_intervals = self.combine_intervals(self.intervals)

        # Create a Pandas DataFrame with the interval data
        data = pd.DataFrame({'Task': ['Time Intervals'] * len(combined_intervals),
                                    'Start': [interval.start_time for interval in combined_intervals],
                                    'Finish': [interval.end_time for interval in combined_intervals]})

        # Create the Gantt chart
        fig = px.timeline(data, x_start='Start', x_end='Finish', y='Task', title='Time Intervals')

        # Format the chart
        fig.update_yaxes(autorange="reversed", showgrid=False, showticklabels=True)
        fig.update_xaxes(showgrid=True, showticklabels=True)
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))

        # Show the chart
        fig.show()

