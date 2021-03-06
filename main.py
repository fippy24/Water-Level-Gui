import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates

import tkinter as tk
from PIL import ImageGrab

import time
import os
import glob
import sys
import numpy as np
from datetime import datetime

from threading import Thread
import code_from_yue as Yue

# Run data creator
thread = Thread(target=Yue.code, args=[])
thread.daemon = True
thread.start()
time.sleep(2)

# Gets the number of tanks
figs = []
for tank in glob.glob("tank[0-9].csv"):
    figs.append(Figure(figsize=(8, 3), dpi=100))

# Set up the non-volatile memory
data = []
try:
    file = open('values.txt', 'r')
    data = file.readlines()
    file.close()
except OSError:
    pass

if len(data) != len(figs) * 3 + 2:
    try:
        os.remove('values.txt')
    except OSError:
        pass
    i = 0
    for f in figs:
        i += 1
        data.append("Tank " + str(i) + "\n")
        data.append(str(.26) + "\n")
        data.append(str(.025) + "\n")
    data.append("COM3\n")
    data.append(str(9600) + "\n")
    file = open('values.txt', 'w')
    file.writelines(data)
    file.close()

# the central function to the graph page
def update(f):
    i = 0

    for f in figs: #for each tank added at the start of the program
        f.clear()
        a = f.add_subplot(1, 2, 1)

        def str2date(x): return datetime.strptime(
            x.decode("utf-8"), '%Y-%m-%d %H:%M:%S')
        fileName = "tank" + str(i + 1) + ".csv"

        # if the tanks have been cleared
        if len(glob.glob("tank[0-9].csv")) <= 0:
            day3Data = [['2016-01-01 00:00:00', 0, 0]]
        else:
            try:
                day3Data = np.genfromtxt(
                    fileName, dtype="datetime64[us], i4, i4", names=True, delimiter=',', comments='#', converters={0: str2date})
                day3Data = sorted(day3Data, key=lambda row: np.datetime64(
                    row[0]).astype(datetime))
            except (TypeError, OSError):
                day3Data = [['2016-01-01 00:00:00', 0, 0]]

        # Set up the half day data
        temp2 = [np.datetime64(row[0]).astype(datetime) for row in day3Data]
        recent = temp2.index(max(temp2)) + 1
        if (len(day3Data) > 24):
            try:
                halfDayData = day3Data[recent - 24:recent]
            except IndexError:
                halfDayData = day3Data[0:recent].append(
                    day3Data[-1 * (24 - recent):])
        else:
            halfDayData = day3Data

        xfmt = mdates.DateFormatter('%d %H:%M')
        conv = float(data[i * 3 + 1])

        # Update the half day
        temp = [np.datetime64(row[0]).astype(datetime) for row in halfDayData]
        a.plot_date(temp, [row[2] * conv for row in halfDayData],
                    color='g', label='Half Day', ls='solid')
        a.tick_params(axis='x', which='major', labelsize=7)
        ticks = a.get_xticks()
        n = len(ticks) // 5 + 1
        a.set_xticks(ticks[::n])
        a.set_xticklabels(a.xaxis.get_majorticklabels(), rotation=15)
        a.xaxis.set_major_formatter(xfmt)
        a.set_title('Half Day')
        a.set_ylim(ymin=0)

        # Update the three day graph
        a2 = f.add_subplot(1, 2, 2)
        temp2 = [np.datetime64(row[0]).astype(datetime) for row in day3Data]
        a2.plot_date(temp2, [row[2] * conv for row in day3Data],
                     color='g', label='Three Days', ls='solid')
        a2.tick_params(axis='x', which='major', labelsize=7)
        ticks2 = a2.get_xticks()
        n2 = len(ticks2) // 5 + 1
        a2.set_xticks(ticks2[::n2])
        a2.set_xticklabels(a2.xaxis.get_majorticklabels(), rotation=15)
        a2.xaxis.set_major_formatter(xfmt)
        a2.set_title('Three Days')
        a2.set_ylim(ymin=0)

        f.canvas.draw()

        main.frames[GraphPage].values[len(data) + i * 2].set("Current Water Level: " + format(
            day3Data[recent - 1][2] * float(data[i * 3 + 1]), '.2f'))
        main.frames[GraphPage].values[len(data) + i * 2 + 1].set("Current Battery Level: " + format(
            day3Data[recent - 1][1] * float(data[i * 3 + 2]), '.2f') + "%")

        i += 1

    # Creates the Image to be put up on a website
    x = main.winfo_rootx()
    y = main.winfo_rooty()
    x1 = x + main.winfo_width()
    y1 = y + main.winfo_height()
    ImageGrab.grab().crop((x, y, x1, y1)).save("./image.png")

    main.after(1000, update, figs)

# Creates all the frames and sets up the window
class mainP(tk.Tk):

    def __init__(self, *args, **kwargs):

        tk.Tk.__init__(self, *args, **kwargs)

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in (StartPage, GraphPage, SettingsPage, InfoPage):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(StartPage)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

# The first page you see
class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(
            self, text="Water Level\nMonitoring System", font=("Helvetica", 64))
        label.pack(pady=10, padx=10)

        button = tk.Button(self, text="Graphs", font=("Helvetica", 32),
                           command=lambda: controller.show_frame(GraphPage))
        button.pack()
        button2 = tk.Button(self, text="Settings", font=("Helvetica", 32),
                            command=lambda: controller.show_frame(SettingsPage))
        button2.pack()
        button3 = tk.Button(self, text="Information", font=("Helvetica", 32),
                            command=lambda: controller.show_frame(InfoPage))
        button3.pack()

# Displays the relevant information
class InfoPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Information", font=("Helvetica", 32))
        label.pack()

        tk.Label(self, text="Description", font=("Helvetica", 24)).pack()
        tk.Label(self, text="This is a program designed to keep track of the water level and \n \
battery level from a serial port input. It then displays this \n \
information on a GUI and a website.\n",font=("Helvetica", 12)).pack()
                            
        tk.Label(self, text="How to Use", font=("Helvetica", 24)).pack()
        tk.Label(self, text="Simply run this GUI then if the data gets corrupted, clear it from\n\
the settings page and possibly restart the gui.\n",font=("Helvetica", 12)).pack()


        tk.Label(self, text="How it works", font=("Helvetica", 24)).pack()
        tk.Label(self, text="The program will read in bytes from serial port, and split it into\n\
7 pieces, take the third fourth piece and multiply by a factor to get\n\
the water level and battery level, the fifth piece will be the indicator\n\
of tank number. Write all information above into CSV files named by \n\
each tank. The GUI will read in those CSV files and display a chart of\n\
water level against time, and output those file to a png file. Finally\n\
run an Apache server and display the png file online.\n",font=("Helvetica", 12)).pack()

        tk.Label(self, text="Creators", font=("Helvetica", 24)).pack()
        tk.Label(self, text="Connor O'Leary\nDavid Hamilton\nYue Gong\n\n",
                 font=("Helvetica", 12)).pack()

        button1 = tk.Button(self, text="Back to Home",
                            command=lambda: controller.show_frame(StartPage))
        button1.pack()

# Provides the options to change the port, Baud, and the ability to clear the tank data
class SettingsPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Settings", font=("Helvetica", 32))
        label.grid(row=0, column=0, columnspan=3)

        tk.Label(self, text="Serial Port Number", font=(
            "Helvetica", 20)).grid(padx=10, row=1)
        self.e1 = tk.Entry(self)
        self.e1.grid(padx=10, row=1, column=2)

        tk.Label(self, text="Baud Rate", font=(
            "Helvetica", 20)).grid(padx=10, row=2)
        self.e2 = tk.Entry(self)
        self.e2.grid(padx=10, row=2, column=2)

        button = tk.Button(self, text="Enter",
                           command=lambda: self.getValues())
        button.grid(column=2)

        tk.Button(self, text="Clear All Tank Data",  height=2, width=14,
                  command=lambda: clear_tanks()).grid(columnspan=3)

        tk.Button(self, text="Back to Home",  height=2, width=14,
                  command=lambda: controller.show_frame(StartPage)).grid(columnspan=3)

    def getValues(self):
        if (self.e1.get() != ""):
            data[3 * len(figs)] = self.e1.get() + "\n"
            self.e1.delete(0, tk.END)
            with open('values.txt', 'w') as file:
                file.writelines(data)
        if (self.e2.get() != ""):
            data[3 * len(figs) + 1] = self.e2.get() + "\n"
            self.e2.delete(0, tk.END)
            with open('values.txt', 'w') as file:
                file.writelines(data)

# Removes all of the tank data and the counter.txt file
def clear_tanks():
    for f in glob.glob("*.csv"):
        os.remove(f)
    for f in glob.glob("counter.txt"):  # if there is one, remove it
        os.remove("counter.txt")

class GraphPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        # TODO: Possible Scroll Bar for more than two tanks
        # canvas=tk.Canvas(self)
        # frame=tk.Frame(canvas)
        # myscrollbar=tk.Scrollbar(self,orient="vertical",command=canvas.yview)
        # canvas.configure(yscrollcommand=myscrollbar.set)

        # myscrollbar.grid(column=6, row=0, rowspan=len(figs)*5+2, sticky='ns')
        # canvas.grid()
        # canvas.create_window((0,0),window=frame,anchor='nw')
        # frame.bind("<Configure>",myfunction)

        label = tk.Label(self, text="Graph Page", font=("Helvetica", 32))
        label.grid(columnspan=2, pady=10, padx=10)
        i = 0

        # List of string variables
        self.values = []
        for dat in data:
            val = tk.StringVar()
            val.set(dat.replace('\n', ''))
            self.values.append(val)

        # Create the layout for displaying the tanks
        for f in figs:
            content = tk.StringVar()
            tk.Button(self, text=self.values[i * 3].get(), textvariable=self.values[i * 3], height=1, width=10, borderwidth=1, font=("Helvetica", 20),
                      command=lambda i=i: self.tank_rename(i)).grid(row=i * 6 + 1, column=0, columnspan=2, padx=10)

            # Current info
            val1 = tk.StringVar()
            lab = tk.Label(self, textvariable=val1, font=("Helvetica", 16))
            self.values.append(val1)
            lab.grid(row=i * 6 + 2, column=0, columnspan=2, padx=10)
            val2 = tk.StringVar()
            lab = tk.Label(self, textvariable=val2, font=("Helvetica", 16))
            self.values.append(val2)
            lab.grid(row=i * 6 + 3, column=0, columnspan=2, padx=10)

            # Conversion factors
            tk.Label(self, text="Conversion Factors", font=("Helvetica", 12)).grid(
                row=i * 6 + 4, column=0, columnspan=2, padx=10)
            tk.Label(self, text="Water:", font=("Helvetica", 12)).grid(
                row=i * 6 + 5, column=0, padx=1)
            tk.Button(self, textvariable=self.values[i * 3 + 1],
                      height=1, width=4, borderwidth=1, font=("Helvetica", 12),
                      command=lambda i=i: self.conv_water(i)).grid(row=i * 6 + 5, column=1, padx=10)
            tk.Label(self, text="Battery:", font=("Helvetica", 12)).grid(
                row=i * 6 + 6, column=0, padx=1)
            tk.Button(self, textvariable=self.values[i * 3 + 2],
                      height=1, width=4, borderwidth=1, font=("Helvetica", 12),
                      command=lambda i=i: self.conv_battery(i)).grid(row=i * 6 + 6, column=1, padx=10)

            canvas = FigureCanvasTkAgg(f, self)
            canvas.show()
            canvas._tkcanvas.grid(row=i * 6 + 1, column=2, rowspan=6)

            i += 1

        button1 = tk.Button(self, text="Back to Home", height=2, width=14,
                            command=lambda: controller.show_frame(StartPage))
        button1.grid(columnspan=3)

    # Opens a new window if the user wants to rename the tank
    def tank_rename(self, num):
        t = tk.Toplevel()
        tk.Label(t, text="Enter Tank " + str(num + 1) +
                 "'s name").pack(side="top", fill="both", expand=True, padx=10, pady=5)
        e = tk.Entry(t)
        e.pack(padx=10)
        button = tk.Button(t, text="Enter",
                           command=lambda: self.get_values(t, e.get(), 0, num)).pack()

    # Opens a new window if the user wants to change the water conversion factor
    def conv_water(self, num):
        t = tk.Toplevel()
        tk.Label(t, text="Enter Tank " + str(num + 1) + "'s water conversion").pack(
            side="top", fill="both", expand=True, padx=10, pady=5)
        e = tk.Entry(t)
        e.pack(padx=10)
        button = tk.Button(t, text="Enter",
                           command=lambda: self.get_values(t, e.get(), 1, num)).pack()

    # Opens a new window if the user wants to change the battery conversion factor
    def conv_battery(self, num):
        t = tk.Toplevel()
        tk.Label(t, text="Enter Tank " + str(num + 1) + "'s battery conversion").pack(
            side="top", fill="both", expand=True, padx=10, pady=5)
        e = tk.Entry(t)
        e.pack(padx=10)
        button = tk.Button(t, text="Enter",
                           command=lambda: self.get_values(t, e.get(), 2, num)).pack()

    # Take the changed values and write them to values.txt
    def get_values(self, t, string, context, num):
        data[3 * num + context] = string + "\n"
        self.values[3 * num + context].set(string)
        os.remove('values.txt')
        with open('values.txt', 'w') as file:
            file.writelines(data)

        t.destroy()

main = mainP()
main.after(1, update, figs)
main.mainloop()