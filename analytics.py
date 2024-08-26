def best(habit_list):
    """
    Takes in a list of habits and sorts them descending based on habit streak.

    Args:
        habit_list (list): list of habits
    Returns:
        sorted list of habits
    """

    return sorted(habit_list, key=lambda x: x.streak, reverse=True)


def worst(habit_list):
    """
    Takes in a list of habits and sorts them descending based on number of times broken.

    Args:
        habit_list (list): list of habits
    Returns:
        sorted list of habits
    """
    return sorted(habit_list, key=lambda x: x.fail_count, reverse=True)


def group_by_periodicity(habit_list):
    """
    Takes a list of habits and groups them based on periodicity, sorting the habits in each of the three sublists.

    Args:
        habit_list (list): list of habits
    Returns:
        dictionary
            keys: the three habit periodicity values
            values: sorted lists of habits with that periodicity
    """

    daily_habits = []
    weekly_habits = []
    monthly_habits = []

    for habit in habit_list:
        match habit.period:
            case 'Daily':
                daily_habits.append(habit)
            case 'Weekly':
                weekly_habits.append(habit)
            case 'Monthly':
                monthly_habits.append(habit)

    return {'Daily': best(daily_habits),
            'Weekly': best(weekly_habits),
            'Monthly': best(monthly_habits)}


def ui_parse(raw_list, mode):
    """
    Parses list for use in the best and worst habits part of the analytics module.

    Args:
        raw_list (list): list of habits
        mode (str): can be either 'Best', 'Worst' or 'Period', dictates how list is turned into text
    Returns:
        final_string (string): a text paragraph loaded into the Tkinter text widgets, containing
        the prepared and final form of the information
    """

    # list which stores the "unwrapped" habit information. Takes list of habit instances and expands into list of lists,
    # with each sublist containing certain traits about the habit
    unwrapped_list = []

    if mode == 'Period':
        for habit in raw_list:
            unwrapped_list.append([habit.name, "streak:", str(habit.streak)])
    else:
        for habit in raw_list:
            if mode == 'Best':
                int_label = 'streak:'
                int_attr = habit.streak
            elif mode == 'Worst':
                int_label = 'breaks:'
                int_attr = habit.fail_count
            else:
                raise ValueError("Incorrect mode entered for ui_parse function!")

            if int_attr != 0:
                unwrapped_list.append([habit.name, habit.period, int_label, str(int_attr)])

    # Takes every line (list of attributes) of the unwrapped list, turns every sublist into a string separated by a dash
    line_list = []

    for line in unwrapped_list:
        # convert streak back to a string with appropriate formatting
        line_list.append(" - ".join(line))
    # Turns list of strings into a single string in the form of a paragraph that is loaded into Tkinter text widget
    final_string = "\n".join(line_list)
    return final_string
