from tkinter import *
from tkinter import messagebox
from tkinter.ttk import Button, Style

import matplotlib.pyplot as plt
from pandas import DataFrame
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import sqlite3
import datetime
import requests

app = None
JSON_LINK = 'https://data.wa.gov/api/views/d886-d5q2/rows.json'


def main():
    global app
    try:
        conn = sqlite3.connect('application.db')
        app = App(conn)
        app.run()
    except Exception as e:
        print('A problem appeared when establishing a DB connection!', e)


def get_raw():
    try:
        fetched = requests.get(JSON_LINK)
        return fetched.json()
    except ValueError as e:
        messagebox.showerror('File error', 'The data cannot be loaded!')
        print(e)


def load_data(conn):
    cursor = conn.cursor()
    if not app.scheme_present:
        cursor.execute('''
			CREATE TABLE IF NOT EXISTS cars(
				id TEXT PRIMARY KEY,
				ev_count INT NOT NULL,
				date timestamp);
			''')
        app.scheme_present = True
        conn.commit()
    if app.data_present:
        cursor.close()
        app.status.config(text='Some data is still present - clear the DB!')
        return
    try:
        insert_to_db(cursor, conn, get_values(get_raw()))
        cursor.close()
        app.data_present = True
        app.load_executed = True
        app.status.config(text='Data was loaded into DB successfully')
    except sqlite3.Error as e:
        print(e)


def check_db_empty(cursor):
    cursor.execute('SELECT COUNT(*) FROM cars')
    return int(cursor.fetchone()[0]) == 0


def get_values(json):
    result = []
    for item in json.get('data'):
        result.append((item[1], int(item[-1]),
                       datetime.datetime.strptime(item[-4], '%Y-%m-%dT%H:%M:%S')))
    return result


def insert_to_db(cursor, conn, vals):
    if len(vals) < 1:
        messagebox.showerror(
            'Data error', 'No values were found for adding to the DB')
    cursor.executemany('INSERT INTO cars VALUES(?, ?, ?);', vals)
    conn.commit()


def clear_data(conn):
    try:
        cursor = conn.cursor()
        if check_db_empty(cursor):
            app.status.config(text='DB is empty already!')
            cursor.close()
            return
        cursor.execute('DELETE FROM cars;')
        conn.commit()
        cursor.close()
        app.data_present = False
        app.load_executed = False
        app.status.config(text='DB was cleared successfully')
    except sqlite3.Error as e:
        app.status.config(text='There was a problem clearing the DB!')
        print(e)


def calc_sum(conn):
    if app.scheme_present and app.load_executed:
        cursor = conn.cursor()
        cursor.execute('SELECT SUM(ev_count) FROM cars;')
        res = int(cursor.fetchone()[0])
        cursor.close()
        return res
    else:
        return None


class App(Tk):
    def __init__(self, db_conn):
        super().__init__()
        self.db_conn = db_conn
        self.scheme_present = False
        self.data_present = check_db_empty(self.db_conn.cursor())
        self.load_executed = False

    def run(self):
        self.resizable(width=False, height=False)
        self.title('Data display app')
        self.geometry('{}x{}'.format(500, 550))
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.init_top()
        self.init_center()
        self.init_btm()
        self.protocol('WM_DELETE_WINDOW', self.on_close)
        self.mainloop()

    def on_close(self):
        self.db_conn.close()
        self.destroy()

    def init_top(self):
        self.top = Frame(self, pady=3)
        self.top.grid(row=0, sticky='nsew')
        for x in range(4):
            self.top.grid_columnconfigure(x, weight=1)
        self.layout_top()

    def layout_top(self):
        self.sum_visible = False
        style = Style()
        style.configure('W.TButton', font=('Helvetica', 10, 'bold'),
                        borderwidth='3', background='blue')
        style.map('W.TButton', foreground=[('active', 'green')],
                  background=[('active', 'black')])

        self.set_btn(self.top, 0, 0, 'Load data',
                     lambda: load_data(self.db_conn))
        self.set_btn(self.top, 0, 1, 'Clear database',
                     lambda: clear_data(self.db_conn))
        self.set_btn(self.top, 0, 2, 'Calculate total', self.add_sum)
        self.set_btn(self.top, 0, 3, 'Show graph', self.layout_center)

    def add_sum(self):
        if not self.sum_visible:
            sum_text = self.get_sum()
            if sum_text:
                self.sum_label = Label(self.top, text=sum_text, padx=10, pady=10) \
                    .grid(row=1, column=0, columnspan=4, sticky='w')
                self.status.config(text='Sum calculated successfully')
                self.sum_visible = True
        elif self.sum_label:
            sum_text = self.get_sum()
            if sum_text:
                self.sum_label.config(text=sum_text)
                self.status.config(text='Updated sum!')

    def get_sum(self):
        calculated = calc_sum(self.db_conn)
        if not calculated:
            self.status.config(
                text='A problem occured upon request for a sum!')
            return None
        return f'Calculated sum of vehicles: {calculated}'

    def init_center(self):
        self.plot_area = None
        self.center = Frame(self, padx=3, pady=3)
        self.center.grid(row=1, sticky='nsew')
        self.center.grid_rowconfigure(0, weight=1)
        self.center.grid_columnconfigure(0, weight=1)

    def layout_center(self):
        if not self.plot_area and self.load_executed:
            self.plot_area = self.get_plot(self.center)
            self.plot_area.grid(row=0, column=0, sticky='nsew')
            self.status.config(text='Graph displayed successfully')
        elif self.plot_area:
            self.status.config(text='Graph requested - already visible')
        else:
            self.status.config(text='Data was not yet loaded!')

    def get_plot(self, frame):
        global df2
        figure2 = plt.Figure(figsize=(4, 4), dpi=100)
        ax2 = figure2.add_subplot(111)
        line2 = FigureCanvasTkAgg(figure2, frame)
        df2 = df2[['Month', 'Vehicles amount']].groupby('Month').sum()
        df2.plot(kind='line', legend=True, ax=ax2,
                 color='r', marker='o', fontsize=8)
        ax2.set_title('Electric Vehicles Registered vs. Months')
        line2.draw()
        return line2.get_tk_widget()

    def init_btm(self):
        bottom = Frame(self, bg='lavender', height=40)
        bottom.grid(row=2, sticky='ew')
        bottom.grid_rowconfigure(0, weight=1)
        self.layout_btm(bottom)
        bottom.grid_propagate(0)

    def layout_btm(self, frame):
        Label(frame, text='<Status line>: ', bg='lavender', padx=10) \
            .grid(row=0, column=0)
        self.status = Label(frame, text='', bg='lavender')
        self.status.grid(row=0, column=1)

    def set_btn(self, frame, row, column, text, command):
        btn = Button(frame, text=text, command=command, style='W.TButton')
        btn.grid(row=row, column=column, padx=10, pady=10)
        return btn


data2 = {'Month': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
         'Vehicles amount': [900.8, 1002, 800, 700.2, 600.9, 700, 600.5, 600.2, 500.5, 600.3]
         }
df2 = DataFrame(data2, columns=['Month', 'Vehicles amount'])

if __name__ == '__main__':
    main()
