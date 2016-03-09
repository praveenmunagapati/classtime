
from classtime.logging import logging
logging = logging.getLogger(__name__) # pylint: disable=C0103

import re

class Schedule(object):
    """Represents a 5-day week of 24-hour days

    Each day is split into 48 thirty-minute blocks
    """
    NUM_BLOCKS = 24*2
    """Number of blocks in one day"""

    NUM_DAYS = 5
    DAYS = 'MTWRF'
    """Number of days in a week, and the letters representing each"""

    OPEN = -1
    """Free time"""
    BUSY = -2
    """Busy with a non-school activity"""
    SYMBOLS = 'ABCDEFGHIJKLMNOPQRSTUVWx '
    """Symbols used for drawing a Schedule to the console"""

    SELF_IS_WORSE = True
    SELF_IS_BETTER = False
    """Semantic sorting constants"""

    SIMILARITY_THRESHOLD = 1.00
    """Fraction which must be identical to be similar"""
    DIFFERENCE_THRESHOLD = 1 - SIMILARITY_THRESHOLD

    def __init__(self, sections=None, busy_times=None, preferences=None):
        """Creates a schedule with the given initial conditions

        :param sections: one or more sections to include in the
                         class-schedule and the timetable
        :type sections: section dict or list of section dicts

        :param busy_times: one or more sections to include only
                           in the timetable
        :type busy_times: section dict or list of section dicts
        """
        self.timetable = [[Schedule.OPEN]*Schedule.NUM_BLOCKS
                         for _ in range(Schedule.NUM_DAYS)]
        self.timetable_bitmap = [0 for _ in range(Schedule.NUM_DAYS)]

        self.scorer = ScheduleScorer(self, preferences)
        self.preferences = preferences

        self.more_like_this = list()

        self.sections = list()
        self._add_initial_sections(sections)
        self.busy_times = list()
        self._add_initial_busy_times(busy_times)

    def __repr__(self):
        def timetable_repr(sched, indent):
            all_time_columns = '   0 1 2 3 4 5 6 7 8 9 A B C 1 2 3 4 5 6 7 8 9 A B '
            time_columns = all_time_columns.replace('0 1 2 3 4 5 6 ', '')
            block_offset = len(all_time_columns) - len(time_columns)

            timetable = str()
            timetable += ' '*indent
            timetable += 'scores: ' + str(sched.scorer.read()) + '\n'
            timetable += time_columns
            for daynum, blocks in enumerate(sched.timetable):
                timetable += '\n'
                timetable += ' '*indent
                timetable += '{}: '.format(Schedule.DAYS[daynum])
                for block in blocks[block_offset:]:
                    timetable += Schedule.SYMBOLS[block]
            return timetable + '\n'
        retstr = '\n\n' + \
                 '==============\n' + \
                 '   Schedule\n' + \
                 '==============\n' + \
                 timetable_repr(self, 0)
        if self.more_like_this:
            retstr += 'and {} more like this (similarity >= {})'.format(
                len(self.more_like_this),
                Schedule.SIMILARITY_THRESHOLD)
        return retstr

    def _add_initial_sections(self, sections):
        """Add sections when building a new :py:class:`Schedule`

        :param sections: one or more sections to add
        :type sections: section dict or list of section dicts
        """
        if sections is not None:
            if not isinstance(sections, list):
                sections = [sections]
            for section in sections:
                self.add_section(section)

    def _add_initial_busy_times(self, busy_times):
        """Add busy_times when building a new :py:class:`Schedule`

        :param busy_times: one or more busy_times to add
        :type busy_times: section dict or list of section dicts
        """
        if busy_times is not None:
            if not isinstance(busy_times, list):
                busy_times = [busy_times]
            for busy_time in busy_times:
                self.add_busy_time(busy_time)

    def add_section(self, section):
        """Attempts to add a section to the timetable.
        On success, adds it to the section list.

        :param section: the section to add
        :type section: section dict

        If a section has null timetable info (day, startTime, endTime),
        it will not be added.
        """
        try:
            self.attempt_add_to_timetable(section, len(self.sections))
        except ValueError:
            pass
        self.sections.append(section)
        return self

    def add_busy_time(self, busy_time):
        """Attempts to add a busy_time to the timetable.
        On success, adds it to the busy_time list.

        :param busy_time: the busy_time to add
        :type busy_time: section dict

        If a busy_time has null timetable info (day, startTime, endTime),
        it will not be added.
        """
        try:
            self.attempt_add_to_timetable(busy_time, Schedule.BUSY)
        except ValueError:
            logging.error('Failed to schedule busy time {}'.format(
                busy_time))
        else:
            self.busy_times.append(busy_time)
        return self

    def conflicts(self, section):
        """Checks for a conflict between this :py:class:`Schedule`
        and a section

        :param section: the section to check for conflicts with
        :type sections: section dict

        :returns: whether it conflicts or not
        :rtype: boolean
        """
        if self._has_timetable_conflict(section):
            return True
        if self._has_dependency_conflict(section):
            return True
        return False

    def _has_timetable_conflict(self, section):
        other = Schedule(section)
        for day in range(Schedule.NUM_DAYS):
            if other.timetable_bitmap[day] & self.timetable_bitmap[day] != 0:
                return True
        return False

    def _has_dependency_conflict(self, section):
        potential_dependencies = [other
            for other in self.sections
            if other.get('course') == section.get('course')
            and other.get('component') != section.get('component')]

        for other in potential_dependencies:
            if section.get('autoEnroll') is None \
            and other.get('autoEnroll') is None:
                continue
            if section.get('component') != other.get('autoEnrollComponent') \
            and section.get('autoEnrollComponent') != other.get('component'):
                continue
            if section.get('autoEnroll') == other.get('section') \
            or section.get('section') == other.get('autoEnroll'):
                continue
            return True
        return False

    def is_similar(self, other):
        return self._similarity(other) >= Schedule.SIMILARITY_THRESHOLD

    def _similarity(self, other):
        return 1 - self._difference(other)

    def _difference(self, other):
        _difference = 0.0
        _scheduled_blocks = sum([bin(day).count('1')
                                 for day in self.timetable_bitmap])
        for day in range(Schedule.NUM_DAYS):
            xordiff = other.timetable_bitmap[day] ^ self.timetable_bitmap[day]
            # each real block difference produces two 1's in the xordiff
            _difference += bin(xordiff).count('1') / 2.0
        if not _scheduled_blocks:
            _other_scheduled_blocks = sum([bin(day).count('1')
                                          for day in other.timetable_bitmap])
            return _other_scheduled_blocks # guard against div by zero
        return 1.0 * _difference / _scheduled_blocks

    def num_similar_schedules(self):
        return len(self.more_like_this)

    def attempt_add_to_timetable(self, section, section_num):
        """Attempts to add a section to the timetable

        :param section: the section to add
        :type section: section dict
        :param int section_num: the index of :py:attr:`Schedule.SYMBOLS` to
                                represent this section with
        :raises ValueError: if one or more of:
                            * day
                            * startTime
                            * endTime
                            is null
        """
        days = section.get('day')
        start = section.get('startTime')
        end = section.get('endTime')
        if None in [days, start, end]:
            raise ValueError(section.get('class_', '??'))
        start = Schedule._timestr_to_blocknum(start)
        end = Schedule._timestr_to_blocknum(end)
        for day in days:
            self._add_to_timetable(day, start, end, section_num)            

    def _add_to_timetable(self, day, start, end, section_num):
        """Adds one or more blocks to the timetable

        :param day: the timetable day to add to
        :type day: str of length one
        :param int start: the first block
        :param int end: the last block (inclusive)
        :param int section_num: the index of Schedule.SYMBOLS to
                                represent these blocks with
        """
        daynum = Schedule._daystr_to_daynum(day)
        for block in range(start, end+1):
            self.timetable_bitmap[daynum] |= 1 << (Schedule.NUM_BLOCKS-block-1)
            self.timetable[daynum][block] = section_num

    def clone(self):
        """Clones this schedule

        :returns: a new schedule with identical
                  * section list
                  * busy_time list
                  * timetable
                  * preferences
        :rtype: Schedule
        """
        return Schedule(sections=self.sections,
                        busy_times=self.busy_times,
                        preferences=self.preferences)

    def __lt__(self, other):
        if len(self.sections) > len(other.sections):
            return Schedule.SELF_IS_BETTER
        elif len(self.sections) < len(other.sections):
            return Schedule.SELF_IS_WORSE

        if self.overall_score() < other.overall_score():
            return Schedule.SELF_IS_WORSE
        else:
            return Schedule.SELF_IS_BETTER

    def overall_score(self):
        return self.scorer.read('overall')

    @staticmethod
    def _timestr_to_blocknum(time):
        """Converts a time string to a block number

        :param str time: string in :ref:`time format <time-format>`
        :returns: block number this time is inside of
        :rtype: int

        :raises ValueError: if time does not match
                            :ref:`time format <time-format>`
        """
        if not isinstance(time, str):
            time = str(time)
        match = re.search(r'(\d\d):(\d\d) (\w\w)', time)
        if match is None:
            raise ValueError(r'time must match "\d\d:\d\d [AP]M')
        hour = int(match.group(1))
        minute = int(match.group(2))
        ampm_offset = 0
        if hour != 12 and match.group(3) == 'PM':
            ampm_offset = 12

        block = (hour+ampm_offset)*2 + minute/30
        return block

    @staticmethod
    def _daystr_to_daynum(day):
        """Converts a day string to a day number

        :param day: day in Schedule.DAYS
        :type day: str of length one
        :returns: day number this day string represents

        :raises ValueError: if day is not in Schedule.DAYS
        """
        if day not in Schedule.DAYS:
            raise ValueError('day must be in "{}"'.format(Schedule.DAYS))
        return Schedule.DAYS.index(day)


class ScheduleScorer(object):
    """Scores a schedule using a suite of scoring functions
    """
    def __init__(self, schedule, preferences=None):
        """Creates a new ScheduleScorer to score the given schedule

        :param Schedule schedule: the schedule to be scored
        """
        self.schedule = schedule
        self.score_values = dict()

        if preferences is None:
            preferences = dict()

        for preference in ['no-marathons', 'day-classes', 'start-early']:
            if preference not in preferences or preferences[preference] is None:
                preferences[preference] = 1

        self.score_info = {
            'no-marathons': {
                'weight': preferences.get('no-marathons', 1),
                'function': self._no_marathons
            },
            'day-classes': {
                'weight': preferences.get('day-classes', 1),
                'function': self._day_classes
            },
            'start-early': {
                'weight': preferences.get('start-early', 1),
                'function': self._start_early
            }
        }

    def read(self, name='all'):
        """Returns a particular score, or all scores

        :param str name: the name of a particular scoring function.
                         Defaults to 'all', which returns a dictionary
                         of all scoring functions and their values.
                         **Special value:** 'overall', which is a
                         weighted sum of all scores.
        """
        self._update()
        if name == 'all':
            return self.score_values
        else:
            return self.score_values.get(name)

    def _update(self):
        """Update all scores by calculating them individually

        Also calculates 'overall', which is a weighted sum of all
        scoring functions.
        """
        self.score_values['overall'] = 0
        if not len(self.schedule.sections):
            return
        for name in self.score_info.keys():
            self.score_values.update({
                name: self._weight(name) * self._score(name)
            })
        self.score_values['overall'] = sum(self.score_values.values())

    def _weight(self, name):
        """Return the weight of a particular scoring function

        :param str name: the name of the scoring function
        """
        info = self.score_info.get(name)
        if info is not None:
            return info.get('weight', 1)
        return None

    def _score(self, name):
        """Run a particular scoring function, and return its result

        :param str name: the name of the scoring function
        """
        info = self.score_info.get(name)
        if info is not None:
            if info.get('weight', 0) == 0:
                return 0
            return info.get('function', lambda: 0)()
        else:
            return 0

    def _no_marathons(self):
        """Scores based on the class spread throughout the day

        * + weight: spread out. More breaks in between classes
        * 0 weight: -no effect-
        * - weight: clumped up. Less breaks in between classes
        """
        _decent_average_length = 4 # 2 blocks per hour
        def average_session(day_timetable):
            session_length = 0
            session_lengths = 0
            num_sessions = 0
            for block in day_timetable:
                if block != Schedule.OPEN:
                    session_length += 1
                else:
                    session_lengths += session_length
                    num_sessions += 1
                    session_length = 0
            if not num_sessions:
                num_session = 1 # guard against div by zero
            return (1.0 * session_lengths) / num_sessions
        _decent_sum_of_longest = 2 * 3 * 5 # 2block/hr, 3 hours, 5 days
        def longest_session(day_bitmap):
            longest_marathon = 0
            while day_bitmap:
                day_bitmap &= (day_bitmap << 1)
                longest_marathon += 1
            return longest_marathon

        maxes = [longest_session(day_bitmap)
                 for day_bitmap in self.schedule.timetable_bitmap]
        avges = [average_session(day_timetable)
                 for day_timetable in self.schedule.timetable]

        sum_of_longest = sum(maxes)
        average_length = sum(avges) / len(avges)

        # decent - actual, since smaller values are better
        score = 0
        score += _decent_sum_of_longest - sum_of_longest
        score += _decent_average_length - average_length

        return 0.5 * score

    def _day_classes(self):
        """Scores based on having day classes versus night classes

        * + weight: classes end before 5pm
        * 0 weight: -no effect-
        * - weight: classes start at or after 5pm
        """
        #               0 1 2 3 4 5 6 7 8 9 A B C 1 2 3 4 5 6 7 8 9 A B 
        night_zone = int('111111111111111100000000000000000011111111111111', 2)
        _decent_avg_night_blocks = 0
        def num_night_blocks(day_bitmap):
            return bin(day_bitmap & night_zone).count('1')

        night_blocks = [num_night_blocks(day_bitmap)
                        for day_bitmap in self.schedule.timetable_bitmap]

        avg_night_blocks = 1.0 * sum(night_blocks) / len(night_blocks)
        # decent - actual, because smaller values are better
        score = 0
        score += _decent_avg_night_blocks - avg_night_blocks

        return 1.5 * score

    def _start_early(self):
        """Scores based on starting early or late

        * + weight: start early
        * 0 weight: -no effect-
        * - weight: start late
        """
        _decent_early_start_block = 9*2 # 2 blocks per hour
        def start_block(day_timetable):
            for i, block in enumerate(day_timetable):
                if block not in [Schedule.OPEN, Schedule.BUSY]:
                    return i
            return None

        start_blocks = [start_block(day_timetable)
                        for day_timetable in self.schedule.timetable]
        start_blocks = [start_block for start_block in start_blocks
                        if start_block is not None]

        if not len(start_blocks):
            return 0 # guard against div by zero

        avg_start_block = 1.0 * sum(start_blocks) / len(start_blocks)

        # decent - actual
        score = 0
        score += _decent_early_start_block - avg_start_block

        return score

# http://bytes.com/topic/python/answers/552476-why-cant-you-pickle-instancemethods#edit2155350
def _pickle_method(method):
    """Allow pickling of Schedule object

    This is necessary for multiprocessing.Queue.put() and
    multiprocessing.Queue.get()
    """
    func_name = method.im_func.__name__
    obj = method.im_self
    cls = method.im_class
    return _unpickle_method, (func_name, obj, cls)

def _unpickle_method(func_name, obj, cls):
    """Allow pickling of Schedule object

    This is necessary for multiprocessing.Queue.put() and
    multiprocessing.Queue.get()
    """
    for cls in cls.mro():
        try:
            func = cls.__dict__[func_name]
        except KeyError:
            pass
        else:
            break
    return func.__get__(obj, cls)

import copy_reg
import types
copy_reg.pickle(types.MethodType, _pickle_method, _unpickle_method)
