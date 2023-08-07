import csv
from pathlib import Path
from tkinter import *
from tkinter import filedialog, messagebox
from tkinter.ttk import Combobox, Notebook, Style, Progressbar, LabelFrame
import pandas as pd
from tkcalendar import Calendar
from datetime import datetime, timedelta
from twenitlib.seleniummaeva import MaevaScraping
from twenitlib.twenitweb import clean_result, generate_sitemap
import threading
import os


class NormalizationFrame(Frame):

    def __init__(self, root, parent):

        super().__init__(parent, bg="#122", width=300, height=600)

        # Propriétés
        self.root = root

        self.source = StringVar(self)
        self.dest = StringVar(self)
        self.extension = StringVar(self)

        # Widgets

        title = Label(self, text="Normaliser les résultats", font=("Verdana", 13, "bold"), fg="white", bg="#122")
        title.place(x='20', y='20')

        source_label = Label(self, text="Fichiers sources:", font=("Verdana", 10), fg="#DDD", bg="#122")
        source_label.place(x='20', y='88')

        source_entree = Entry(self, textvariable=self.source, font=("Verdana", 10))
        source_entree.place(x='20', y='130', width=260, height=32)

        source_button_frame = Frame(self, highlightbackground='white', highlightthickness=1)
        source_button_frame.place(x='207', y='131')

        self.source_bouton = Button(source_button_frame, text="Parcourir", bg="#122", fg="#DDD", command=self.browse_source_files, font=("Verdana", 10))
        self.source_bouton.pack()

        dest_label = Label(self, text="Enregistrer sous:", font=("Verdana", 10), fg="#DDD", bg="#122")
        dest_label.place(x='20', y='180')

        dest_entree = Entry(self, textvariable=self.dest, font=("Verdana", 10))
        dest_entree.place(x='20', y='220', width=260, height=32)

        dest_button_frame = Frame(self, highlightbackground='white', highlightthickness=1)
        dest_button_frame.place(x='207', y='221')

        self.dest_bouton = Button(dest_button_frame, text="Parcourir", bg="#122", fg="#DDD", command=self.browse_dest_folder, font=("Verdana", 10))
        self.dest_bouton.pack()

        ext_label = Label(self, text="Type de sortie:", font=("Verdana", 10), fg="#DDD", bg="#122")
        ext_label.place(x='20', y='270')

        self.ext_entree = Combobox(self, textvariable=self.extension, font=("Verdana", 10))
        self.ext_entree['values'] = ('Document CSV (*.csv)', 'Document Excel (*.xlsx)')
        self.ext_entree.place(x='20', y='310', width=260, height=32)

        start_button_frame = Frame(self, highlightbackground='#DDD', highlightthickness=2)
        start_button_frame.place(x='120', y='430', width=160)
        

        self.start_bouton = Button(start_button_frame, text="Lancer", bg="#244", fg="#DDD", font=("Verdana", 10), width=40, command=self.start_normalization)
        self.start_bouton.pack()

    def browse_source_files(self):
        filename = filedialog.askopenfilenames(initialdir = "/",
                                            title = "Selectionner les fichiers",
                                            filetypes = (("Text files",
                                                            "*.csv*"),
                                                        ("all files",
                                                            "*.*")))
        self.source.set(filename)

    def browse_dest_folder(self):
        filename = filedialog.askdirectory()
        self.dest.set(filename)

    def normalize(self):
        sources = self.source.get()[1:-1].split(', ')
        if len(sources) > 1:
            sources = list(map(lambda x: x[1:-1], sources))
        else:
            sources = list(map(lambda x: x[1:-2], sources))
        
        response = True
        extension = 'csv' if self.ext_entree.current() == 0 else 'xlsx'

        # uncleaned = self.fusionner(sources)
        # cleaned = clean_result(uncleaned, self.dest.get(), extension)

        
        for s in sources:
            response = response and clean_result(s, self.dest.get(), extension)

        if response:
            messagebox.showinfo('Information', "Normalisation terminée !")

    def fusionner(self, filenames):
        tmplist = []

        fieldnames = ['web-scraper-order', 'web-scraper-start-url', 'nom', 'localite', 'prix_init', 'prix_actuel', 'note', 'typo', 'type_de_lit', 'taxes', 'nuite', 'experience_vecu', 'reduction', 'genius']
        for filename in filenames:
            tmplist.append(pd.read_csv(filename, header=None))
            # with open(filename, 'r') as csvfile:
            #     reader = csv.DictReader(csvfile, fieldnames=fieldnames)
            #     for line in reader:
            #         tmplist.append(line)
        all_data = pd.concat(tmplist)
        dest_filename = f'{self.dest.get()}/{Path(filenames[0]).stem}_full.{Path(filenames[0]).suffix}'
        all_data.to_csv(dest_filename, header=fieldnames)
    
        # dest_filename = f'{self.dest.get()}/{Path(filenames[0]).stem}_full.{Path(filenames[0]).suffix}'
        # with open(dest_filename, 'w', newline='') as csvfile:
        #     writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        #     writer.writeheader()

        #     writer.writerows(tmplist)
        
        return dest_filename

    def start_normalization(self):
        t = threading.Thread(target=self.normalize)
        t.start()

        # Commencer à vérifier périodiquement si le process est terminé.
        self.schedule_check(t)

    def schedule_check(self, t):
        self.root.after(1000, self.check_if_done, t)

    def check_if_done(self, t):

        # Afficher un message si le process s'arrête
        if not t.is_alive():
            messagebox.showinfo("Information", "Normalisation terminée !")
        else:
            # Revérifier après une seconde
            self.schedule_check(t)


class SitemapFrame(Frame):

    def __init__(self, root, parent):

        super().__init__(parent, bg="#071215", width=600, height=600)

        # Propriétés
        self.root = root

        self.source_ids = StringVar(self)
        self.dest_dir = StringVar(self)
        self.interval = IntVar(self)
        self.frequence = StringVar(self)

        # Widgets
        title = Label(self, text="Générer les sitemaps", font=("Verdana", 13, "bold"), fg="white", bg="#071215")
        title.place(x='20', y='20')

        source_label = Label(self, text="Ids destinations:", font=("Verdana", 10), fg="#DDD", bg="#071215")
        source_label.place(x='20', y='86')

        source_entree = Entry(self, textvariable=self.source_ids, font=("Verdana", 10))
        source_entree.place(x='200', y='80', width=300, height=32)

        source_button_frame = Frame(self, highlightbackground='white', highlightthickness=2)
        source_button_frame.place(x='440', y='80')

        source_bouton = Button(source_button_frame, text="Parcourir", bg="#071215", fg="#DDD", command=self.browse_source_file, font=("Verdana", 10))
        source_bouton.pack()

        dest_label = Label(self, text="Enregistrer sous:", font=("Verdana", 10), fg="#DDD", bg="#071215")
        dest_label.place(x='20', y='136')

        dest_entree = Entry(self, textvariable=self.dest_dir, font=("Verdana", 10))
        dest_entree.place(x='200', y='130', width=300, height=32)

        dest_button_frame = Frame(self, highlightbackground='white', highlightthickness=2)
        dest_button_frame.place(x='440', y='130')

        dest_bouton = Button(dest_button_frame, text="Parcourir", bg="#071215", fg="#DDD", command=self.browse_dest_folder, font=("Verdana", 10))
        dest_bouton.pack()

        date_start_label = Label(self, text="Date début:", font=("Verdana", 10), fg="#DDD", bg="#071215")
        date_start_label.place(x='20', y='180')

        date_end_label = Label(self, text="Date fin:", font=("Verdana", 10), fg="#DDD", bg="#071215")
        date_end_label.place(x='310', y='180')

        self.cal_1 = Calendar(self, select_mode='day', year=datetime.now().year, month=datetime.now().month, day=datetime.now().day, locale="fr_FR", date_pattern='dd-mm-y')
        self.cal_1.place(x='20', y='220')

        self.cal_2 = Calendar(self, select_mode='day', year=datetime.now().year, month=datetime.now().month, day=datetime.now().day, locale="fr_FR", date_pattern='dd-mm-y')
        self.cal_2.place(x='310', y='220')

        interval_label = Label(self, text="Intervalle / Frequence:", font=("Verdana", 10), fg="#DDD", bg="#071215")
        interval_label.place(x='20', y='434')

        interval_entree = Entry(self, textvariable=self.interval, font=("Verdana", 10))
        interval_entree.place(x='220', y='430', width=70, height=32)
        freq_entree = Combobox(self, textvariable=self.frequence, font=("Verdana", 10))
        freq_entree['values'] = ('1', '3', '7', 'all')
        freq_entree.place(x='295', y='430', width=70, height=32)

        start_button_frame = Frame(self, highlightbackground='#DDD', highlightthickness=2)
        start_button_frame.place(x='400', y='430', width=160)

        start_bouton = Button(start_button_frame, text="Lancer", bg="#244", fg="#DDD", font=("Verdana", 10), width=40, command=self.start_generation)
        start_bouton.pack()

    def browse_source_file(self):
        filename = filedialog.askopenfilename(initialdir = "/",
                                            title = "Selectionner un fichier",
                                            filetypes = (("Text files",
                                                            "*.csv*"),
                                                        ("all files",
                                                            "*.*")))
        self.source_ids.set(filename)

    def browse_dest_folder(self):
        filename = filedialog.askdirectory()
        self.dest_dir.set(filename)

    def get_all_dates(self, date_start, date_end, interval):
        dates = []
        start = datetime.strptime(date_start, '%d-%m-%Y')
        date_end = datetime.strptime(date_end, '%d-%m-%Y')

        while start < date_end and start + timedelta(days=interval) < date_end:
            end = start + timedelta(days=interval)
            dates.append((start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')))
            start = end + timedelta(days=1)
        if start < date_end:
            dates.append((start.strftime('%Y-%m-%d'), date_end.strftime('%Y-%m-%d')))

        return dates

    def start_generation(self):
        dates = self.get_all_dates(self.cal_1.get_date(), self.cal_2.get_date(), self.interval.get())

        for d in dates:
            generate_sitemap(self.dest_dir.get(), 'booking', self.source_ids.get(), d[0], d[1], self.frequence.get())
        
        messagebox.showinfo('Information', "Fichiers créés !")
