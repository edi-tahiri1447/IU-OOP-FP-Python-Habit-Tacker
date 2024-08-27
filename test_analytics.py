"""This module is used to test the core functionality of the analytics module.

Please note that the "habit history" feature is not part of the analytics module, but rather part of the GUI,
as the habit history is rendered by accessing the Habit.data attribute with no further g needed.
To see how that works with example data, please run tracker_test.py and enter the analytics window.

Keep in mind that the changes made to the habits in the db integration test (restarting 'Take a walk' and creating
'Drink green tea') are not persisted for this unit test."""

import pytest

from habit import Habit
from test_habit import testing_data, testing_habits
import analytics


# taking the regular testing_habits fixture and drawing from it only the values, as we will only need them for this test
@pytest.fixture
def habits(testing_habits):
    yield testing_habits.values()


def test_best(habits):
    # verifying which habit is the best
    assert analytics.best(habits)[0].name == 'Take a walk'

    # comparing best function with calculating highest streak of habit group through lambda
    assert analytics.best(habits)[0].streak == max([x.streak for x in habits])


def test_worst(habits):
    # verifying which habit is the worst
    assert analytics.worst(habits)[0].name == 'Read for 15 minutes'

    # comparing worst function with calculating highest frequency of breakages through lambda
    assert analytics.worst(habits)[0].fail_count == max([x.fail_count for x in habits])


def test_group_by_periodicity(habits):
    grouped_habits = analytics.group_by_periodicity(habits)

    # seeing if the grouping is done properly. There are:
    #   2 daily habits
    #   2 weekly habits
    #   1 monthly habit

    assert len(grouped_habits['Daily']) == 2
    assert len(grouped_habits['Weekly']) == 2
    assert len(grouped_habits['Monthly']) == 1

    # seeing if the groups are sorted properly
    assert grouped_habits['Daily'][0].name == 'Take a walk'
    assert grouped_habits['Daily'][0].streak == max([x.streak for x in habits if x.period == 'Daily'])