import datetime

import sqlite3
import tkinter as tk
from tkinter import ttk

from habit import Habit
import analytics
import utils

# declare database file we'll be using in this module
Habit.db_name = 'habit_db.db'

if __name__ == "__main__":

    Habit.initialize_db()

    # list of all habits as instances of Habit class (this is used by core functionality)
    habit_group = []
    # list of all habit names (string representations) (this is used by Tkinter)
    habit_namelist = []


    def load_habits_from_db():
        """
        (Re)loads the habits from the SQLite3 database into the application logic.

        Operates on two lists:
        habit_group is the list of Habit objects, which is central to the application,
        and habit_namelist is the list of habit names, which is needed by some Tkinter widgets.
        """

        global habit_group
        global habit_namelist

        habit_group = []
        habit_namelist = []

        with sqlite3.connect(Habit.db_name) as conn:
            cur = conn.cursor()
            query_result = cur.execute("SELECT * FROM Habit").fetchall()
        for row in query_result:
            habit_group.append(
                Habit(name=row[0], period=row[1], start_date=row[2])
            )
        for x in habit_group:
            habit_namelist.append(str(x))


    load_habits_from_db()

    # defining the key Tkinter widgets now: Root first, which is split into an upper and a lower frame
    root = tk.Tk()

    # upper frame contains the habit listbox and buttons through which to interact with them
    upper_frame = tk.Frame(root, padx=8, pady=8)
    upper_frame.pack()

    # the listbox is essentially the central widget here; this is where the user accesses the habits to manipulate them
    habit_listbox_stringvar = tk.StringVar(value=habit_namelist)
    habit_listbox = tk.Listbox(upper_frame, listvariable=habit_listbox_stringvar, exportselection=False)
    habit_listbox.grid(column=1, row=1)

    # lower frame contains brief summary of habit that is loaded upon selection, and clock
    lower_frame = tk.Frame(root, padx=8, pady=8)
    lower_frame.pack()

    # summary text widget, shows summary of habit upon selection
    habit_info = tk.Text(lower_frame, padx=8, pady=8, height=7)
    habit_info.grid(column=1, row=0)

    # starting to define listbox functionality and habit manipulation
    current_habit = None


    def on_habit_select(evt):
        """
        Fetches current habit instance every time user selects something on the listbox, updating the current_habit variable.

        Args:
            evt (event object): passed to the function by the listbox bind method.
        """

        global current_habit

        w = evt.widget
        try:
            index = int(w.curselection()[0])
            current_habit = habit_group[habit_listbox.curselection()[0]]
            value = w.get(index)
            reload_info(current_habit)
        except IndexError:
            pass


    # bind method calls on_habit_select function whenever something is selected
    habit_listbox.bind('<<ListboxSelect>>', on_habit_select)
    # to make sure that clicking out does not render any type of exception
    habit_listbox.bind('<FocusOut>', lambda *args: None)


    # called on every habit select, as well as after other actions, in order to reload all the information
    def reload_info(current_habit):
        """
        Reloads the information displayed on the graphical user interface.
        This includes putting together a summary of the selected habit for the lower text box,
        as well as rendering the habit-dependent buttons depending on habit state (if the button can be pressed.)

        Args:
            current_habit(Habit): the current habit provided and updated by the listbox.
        """

        # checks whether or not a habit is selected by listbox (curselection() returns a tuple; if empty, clears text.)
        if not habit_listbox.curselection():
            habit_info.delete('1.0', tk.END)
        # if there is a selected habit, prepares to render summary text depending on attributes:
        else:
            # make sure the habit instance is up to date
            current_habit.parse_data()
            current_habit.load_state()

            # the following section deifnes each line of text in the summary text box
            # name and periodicity of habit to start off with
            line_one = f"Selected habit: {str(current_habit)} {str(current_habit.period).lower()}."

            # dict to hold all the different words depending on streak length (plurality)
            period_nouns = {'Daily': ('day', 'days'),
                            'Weekly': ('week', 'weeks'),
                            'Monthly': ('month', 'months')}
            # singular
            if current_habit.streak == 1:
                i = 0
            # plural
            elif current_habit.streak > 1:
                i = 1

            # length of current streak in units depending periodicity: Current streak: x day(s)/week(s)/month(s)
            if current_habit.streak != 0:
                line_two = f"Current streak: {current_habit.streak} {period_nouns[current_habit.period][i]}"
            else:
                line_two = ""

            # start date, formatted more elegantly
            line_three = f"started on: {current_habit.start_date.strftime("%d %B, %Y")}"

            # if it has been checked or restarted at any point, shows the last date of the action
            if current_habit.last_success is not None:
                line_four = f"last checked on: {current_habit.last_success.strftime("%d %B, %Y")}"
            else:
                line_four = ""

            # if it has ever been broken at any point, shows last date of that as well
            if current_habit.last_fail is not None:
                line_five = f"habit was recently broken on {current_habit.last_fail.strftime("%d %B, %Y")}"
            else:
                line_five = ""

            # renders habit summary into text widget
            habit_info.delete("1.0", tk.END)
            habit_info.insert(index="1.0",
                              chars=f"{line_one}\n"
                                    f"{line_two}\n\n"
                                    f"{line_three}\n\n"
                                    f"{line_four}\n"
                                    f"{line_five}")

        # renders check-off button only if the selected habit is ready
        check_off_habit_button = tk.Button(upper_frame, text="Check off Habit", command=button_check_off)
        check_off_habit_button.grid(column=0, row=0)
        if current_habit.state == 'Ready':
            check_off_habit_button['state'] = 'normal'
        else:
            check_off_habit_button['state'] = 'disabled'

        # restart button, available if the selected habit's last record is not also a restart
        restart_habit_button = tk.Button(upper_frame, text="Restart Habit", command=button_restart_habit)
        restart_habit_button.grid(column=0, row=1)
        if (current_habit is None or
                not current_habit.data or
                current_habit.data[-1][2] == 'Restart'):
            restart_habit_button['state'] = 'disabled'

        # delete button, available at any time so long as a habit is selected
        delete_habit_button = tk.Button(upper_frame, text="Delete Habit", command=button_delete_habit)
        delete_habit_button.grid(column=2, row=1)
        if current_habit is None:
            delete_habit_button['state'] = 'disabled'


    # defining the functions that the buttons will execute:
    def button_check_off():
        """
        Function used by check-off button. Calls the method of the same name on the habit and reloads info.
        """

        current_habit.check_off()
        current_habit.save_to_db()

        load_habits_from_db()
        reload_info(current_habit)


    def button_restart_habit():
        """
        Function used by restart button. Calls the method of the same name on the habit and reloads info.
        """

        current_habit.restart()
        current_habit.save_to_db()

        load_habits_from_db()
        reload_info(current_habit)


    def button_delete_habit():
        """
        Function used by delete button. Calls the method of the same name on the habit and reloads info.
        """

        current_habit.delete_from_db()
        habit_listbox.delete(habit_listbox.curselection()[0])
        habit_listbox.selection_clear(0, 'end')

        load_habits_from_db()
        reload_info(current_habit)


    # makes a new toplevel window whenever the user wants to add a new habit: name and periodicity are collected there
    def add_habit_popup():
        """
        Function called by the "Add Habit" button, renders another part of the UI where user can enter
        the name and periodicity of the habit. Does error handling based on user input.

        Add habit interface consists of three radio buttons where user picks one of the three possible periodicities,
        and an entry bar where the user can enter a name up to 32 charactes in length.
        """

        # rendering toplevel window
        add_interface = tk.Toplevel(upper_frame)
        add_interface.geometry('250x250')

        # Tkinter Stringvar to store the periodicity choice
        # initialized as having value 1 so as to prevent all three being selected at once upon first render
        period_var = tk.StringVar(value=1)

        # radio buttons to select one of three options for periodicity
        daily_button = tk.Radiobutton(add_interface, text='Daily', variable=period_var, value='Daily')
        daily_button.grid(column=0, row=0)
        weekly_button = tk.Radiobutton(add_interface, text='Weekly', variable=period_var, value='Weekly')
        weekly_button.grid(column=0, row=1)
        monthly_button = tk.Radiobutton(add_interface, text='Monthly', variable=period_var, value='Monthly')
        monthly_button.grid(column=0, row=2)

        # Tkinter entry widget to get name
        new_habit_name = tk.Entry(add_interface)
        new_habit_name.grid(column=1, row=0)

        # inserts new habit into database and reloads all habits from it
        # has some error handling as well, expecting invalid user inputs (missing/invalid name, missing periodicity)
        def create_new_habit():
            """
            Commits creation of the new habit, called upon pressing the button of the same name found inside the
            "add habit" interface.

            Makes sure the name is valid (periodicity entry needs no error handling as only the valid choices are available)
            before inserting the new habit into the Habit table of the database.
            """

            if not period_var.get() or not new_habit_name.get() or period_var.get().isspace() or new_habit_name.get().isspace():
                utils.error_popup("Needs name and periodicity!")
            elif new_habit_name.get() in habit_namelist:
                utils.error_popup(
                    f"There already exists a habit named {new_habit_name.get()}!\nPlease choose another name.")
            elif len(new_habit_name.get()) > 32:
                utils.error_popup("Name is too long! Name can be up to 32 characters.")
            else:
                with sqlite3.connect(Habit.db_name) as conn:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO Habit VALUES(?, ?, ?)",
                                (new_habit_name.get(), period_var.get(), datetime.date.today().isoformat()))
                load_habits_from_db()
                habit_listbox_stringvar.set(value=habit_namelist)

        # button to confirm creation of new habit
        create_button = tk.Button(add_interface, command=create_new_habit, text="Create New Habit")
        create_button.grid(column=1, row=1)

        add_interface.mainloop()


    # button in main window that triggers pop-up of "add habit" interface
    new_habit_button = tk.Button(upper_frame, text="Add Habit", command=add_habit_popup)
    new_habit_button.grid(column=2, row=0)

    # clock widget
    current_time = datetime.datetime.now()
    clock = tk.Text(lower_frame, width=20, height=1, padx=8, pady=8)
    clock.grid(column=0, row=0)


    def run_clock():
        """
        Updates clock widget (Tkinter text) every second.
        """

        current_time = datetime.datetime.now()
        clock.delete('1.0', tk.END)
        clock.insert('1.0', str(current_time)[0:19])
        root.after(1000, run_clock)


    run_clock()


    def show_analytics():
        """
        Renders analytics module window and all of its parts.
        Function is called by the button of the same name.
        """

        if not habit_group:
            utils.error_popup("There are no habits for you to analyze!")
        else:

            # rendering toplevel window
            analytics_window = tk.Toplevel()

            # lower side of screen stores:
            #     left side: best habits
            #     right side: worst habits

            analytics_lower_frame = tk.Frame(analytics_window)
            analytics_lower_frame.grid(column=0, row=1)

            best_habits = tk.Text(analytics_lower_frame, width=50)
            best_habits.grid(column=0, row=0)
            best_habits.insert('1.0', "The longest currently-running habits are:\n\n")
            best_habits.insert(tk.END, f"{analytics.ui_parse(analytics.best(habit_group), 'Best')}")

            worst_habits = tk.Text(analytics_lower_frame, width=50)
            worst_habits.grid(column=1, row=0)
            worst_habits.insert('1.0', "The habits you struggled the most with are:\n\n")
            worst_habits.insert(tk.END, f"{analytics.ui_parse(analytics.worst(habit_group), 'Worst')}")

            # upper side of screen stores:
            #    left side: list of all habits based on period
            #    center: combobox to select habit for which detailed record is wanted
            #    right side: detailed record of selected habit

            analytics_upper_frame = tk.Frame(analytics_window)
            analytics_upper_frame.grid(column=0, row=0)

            # load dict of habits by periodicity; keys = periodicity, values = list of all habits with that periodicity
            # ordered descending by streak
            habits_by_periodicity = analytics.group_by_periodicity(habit_group)

            period_based_habits = tk.Text(analytics_upper_frame, width=40)
            period_based_habits.grid(column=0, row=0)
            period_based_habits.insert('1.0',
                                       f"Daily Habits:\n{analytics.ui_parse(habits_by_periodicity['Daily'], 'Period')}\n\n"
                                       f"Weekly Habits:\n{analytics.ui_parse(habits_by_periodicity['Weekly'], 'Period')}\n\n"
                                       f"Monthly Habits:\n{analytics.ui_parse(habits_by_periodicity['Monthly'], 'Period')}\n\n")

            # Tkinter combobox to select habit for which detailed history is to be loaded
            habits_stringvar_combobox = tk.StringVar(value=habit_namelist)
            detail_select = ttk.Combobox(analytics_upper_frame, textvariable=habits_stringvar_combobox)
            detail_select.grid(column=1, row=0)
            detail_select['values'] = habit_group
            detail_select.current(0)

            # renders history text box
            detail_text = tk.Text(analytics_upper_frame)
            detail_text.grid(column=2, row=0)
            detail_text.insert('1.0', "Please select a habit on the left in order to get a detailed record.")

            # (re)loads info into history text box on every selection
            def on_combobox_select(evt):
                combobox_selection = detail_select.get()
                selected_habit = habit_group[detail_select.current()]

                detail_text.delete('1.0', tk.END)
                # loads initial info for habit: name, periodicity, streak, longest historic streak
                detail_text.insert('1.0', f"Habit: \"{selected_habit.name}\" {selected_habit.period.lower()}\n"
                                          f"Current streak: {selected_habit.streak}\n"
                                          f"Longest historic streak: {selected_habit.longest_streak}\n\n"
    
                # loads habit start date; date here is formatted more elegantly again as with the rest of the UI
                                          f"🚀 Started on {selected_habit.start_date.strftime("%d %B, %Y")}\n")

                # loops through data list of the selected habit and generates lines of text
                # row[0] is habit name, row[1] is date, and row[2] is action
                for row in selected_habit.data:
                    match row[2]:
                        case 'Success':
                            action_for_string = "✅ Completed"
                        case 'Failure':
                            action_for_string = "❌ Broken"
                        case 'Restart':
                            action_for_string = "🔄 Restarted"

                    # loads all the Log entries for the user, in order:
                    detail_text.insert(tk.END, chars=f"{action_for_string} on {row[1].strftime("%d %B, %Y")}\n")

            # finally, binds function to combobox selection
            detail_select.bind('<<ComboboxSelected>>', on_combobox_select)


    # triggers analytics module to pop up; see "show analytics" function
    analytics_button = tk.Button(upper_frame, text="Show Analytics", command=show_analytics)
    analytics_button.grid(column=2, row=2)

    root.mainloop()
