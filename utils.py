import datetime
import tkinter as tk

import dateutil.relativedelta
import dateutil.parser

"""
This module holds several "utility" functions I've had to rely on for this project.
"""


def add_midnight(date):
    """
    Function that turns datetime.date into datetime.datetime object (where the time is set to midnight.)
    Used to accept datetime.date as parameters for habit class data, and while generating test data.

    Args:
        date (datetime.date)
    Returns:
        datetime.datetime
    """

    return datetime.datetime.combine(date, datetime.datetime.min.time())


def parse_list_for_ui(list, int_element):
    """
    Parses list for use in the best and worst habits part of the analytics module.

    Args:
        list (list): a list of lists (every sublist contains the habit name, period, and streak/breaks)
        int_element (int): the index of the element inside the inner list which is an int. Needed for conversion.
    Returns:
        final_string (string): a text paragraph loaded into the Tkinter text widgets, containing
        the prepared and final form of the information
    """
    new_list = []
    for inner_list in list:
        #convert streak back to a string with appropriate formatting
        inner_list[int_element] = str(inner_list[int_element])
        new_list.append(" - ".join(inner_list))
    final_string = "\n".join(new_list)
    return final_string


def error_popup(text: str):
    """
    Makes an error pop-up window appear on screen.

    Args:
        text (string): the text displayed on the inside of the window (telling the user what kind of error it was.)
    """
    error = tk.Toplevel()
    error.geometry("300x100")

    error_text = tk.Label(error, text=text)
    error_text.grid(column=1, row=0)

    ok_button = tk.Button(error, text="Ok", command=lambda: error.destroy())
    ok_button.grid(column=1, row=1)


def run_clock(root, clock):
    """
    Runs the clock. Function is designed to be called automatically every 1000 milliseconds.

    Args:
        root (Tkinter root object): the root window of the GUI.
        clock (Tkinter text widget object): the text widget inside of which the clock is contained.
    """
    clock.delete("1.0", tk.END)
    clock.insert("1.0", str(datetime.datetime.now())[0:19])
    root.after(1000, run_clock(root, clock))


def diff_of_cm(day_a: datetime.datetime, day_b: datetime.datetime) -> int:
    """
            Returns integer difference in calendar months between two dates.
            Takes into account year difference, so that for example 09.07.2023 is not considered to be 1 month
            away from the 09.07.2024, which would happen if we were just calculating the flat calendar month.

            Args:
                day_a (datetime.datetime)
                day_b (datetime.datetime)
            Returns:
                difference (int)
            """

    diff = dateutil.relativedelta.relativedelta(day_a.replace(day=1), day_b.replace(day=1))

    return int((diff.years * 12) + diff.months)


def diff_of_cw(day_a: datetime.datetime, day_b: datetime.datetime) -> int:
    """
        Returns integer difference in calendar weeks between two dates.
        Takes into account year difference, so that for example 09.08.2023 is not considered to be 1 calendar week
        away from the 16.08.2024, which would happen if we were just calculating the flat CW.

        Args:
            day_a (datetime.datetime)
            day_b (datetime.datetime)
        Returns:
            difference (int)
        """

    monday_a = (day_a - datetime.timedelta(days=day_a.weekday()))
    monday_b = (day_b - datetime.timedelta(days=day_b.weekday()))

    return int((monday_a - monday_b).days / 7)