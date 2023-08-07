from tkinter import *
from tkinter import filedialog, messagebox
from tkinter.ttk import Combobox, Notebook, Style, Progressbar, LabelFrame
from twenitlib.seleniummaeva import MaevaScraping
from twenitlib.seleniumbooking import BookingScraping
import threading
import os
from tkcalendar import Calendar
from datetime import datetime


class BookingInstance(Frame):

    def __init__(self, root, parent, container, filename, freq, start, end, index):
        super().__init__(parent)
        self['bg'] = "#152525"
        self['width'] = 290
        self['height'] = 240
        self['highlightbackground'] = "#999"
        self['highlightthickness'] = 1
        self.root = root
        self.index = index
        self.parent = parent
        self.container = container
        self.filename = f"{filename}/{freq}j"
        self.freq = freq
        self.start = start
        self.end = end
        self.instance = BookingScraping(name=filename, freq=freq, start=start, end=end)

        self.percentage = int((self.instance.get_last_url_index()+1)*100/self.instance.total)

        self.progress_percentage = StringVar(self)
        self.progress_state = StringVar(self)

        self.progress_percentage.set(f'{self.percentage}%')
        self.progress_state.set(f'{self.instance.get_last_url_index()+1}/{self.instance.total}')
        
        self.status_value = StringVar(self)
        self.status_value.set('en attente ...')

        path_label = Label(self, text="Nom de l'instance:", font=("Verdana", 10), fg="#DDD", bg="#152525")
        path_label.place(x='10', y='26')

        path_value = Label(self, text=self.filename, font=("Verdana", 10, "bold"), fg="#EFEFFF", bg="#152525")
        path_value.place(x='10', y='56')

        progress_label = Label(self, text="Progression:", font=("Verdana", 10), fg="#DDD", bg="#152525")
        progress_label.place(x='10', y='92')

        progress_value = Label(self, textvariable=self.progress_state, font=("Verdana", 10, "bold"), fg="#DDD", bg="#152525")
        progress_value.place(x='100', y='92')

        status_label = Label(self, textvariable=self.status_value, font=("Verdana", 8), fg="#EFEFFF", bg="#152525")
        status_label.place(x='160', y='92')

        self.progressbar = Progressbar(
            self,
            orient='horizontal',
            mode='determinate',
            length=268
        )

        self.progressbar.place(x='10', y='128')

        progress_percentage = Label(self, textvariable=self.progress_percentage, font=("Verdana", 10, "bold"), fg="#DDD", bg="#152525")
        progress_percentage.place(x='336', y='128')

        remove_button_frame = Frame(self, highlightbackground='#DDD', highlightthickness=2)
        remove_button_frame.place(x='10', y='168', width=80)

        open_button_frame = Frame(self, highlightbackground='#DDD', highlightthickness=2)
        open_button_frame.place(x='100', y='168', width=80)

        start_button_frame = Frame(self, highlightbackground='#DDD', highlightthickness=2)
        start_button_frame.place(x='200', y='168', width=80)

        self.remove_button = Button(remove_button_frame, text="Supprimer", bg="#cf2121", fg="#DDD", font=("Verdana", 10), width=40, command=self.remove_scraping)
        self.remove_button.pack()

        open_bouton = Button(open_button_frame, text="Ouvrir", bg="#244", fg="#DDD", font=("Verdana", 10), width=40, command=self.open_result)
        open_bouton.pack()

        self.start_button = Button(start_button_frame, text="Démarrer", bg="#23ac63", fg="#DDD", font=("Verdana", 10), width=40, command=self.start_booking_scraping)
        self.start_button.pack()

    def start_booking_scraping(self):
        self.start_button['text'] = "Arreter"
        self.start_button['command'] = self.stop_booking_scraping
        t = threading.Thread(target=self.scraping_booking_worker)
        t.start()
        self.schedule_check(t)
        return

    def stop_booking_scraping(self):
        self.start_button['text'] = "Démarrer"
        self.start_button['command'] = self.start_booking_scraping

        self.instance.stop()
        self.remove_button['state'] = 'normal'

    def remove_scraping(self):
        self.container.remove_instance(self.index)

    def open_result(self):
        os.system(f'start {self.path}')

    def scraping_worker(self):
        self.instance.start()

    def scraping_booking_worker(self):
        self.instance.start()

    def schedule_check(self, t):
        self.root.after(1000, self.check_if_done, t)

    def check_if_done(self, t):

        # Afficher un message si le process s'arrête
        if not t.is_alive() and not self.instance.run:
            messagebox.showinfo("Information", "Scraping arrêté !")
            self.status_value.set(f"terminé")
            
        else:
            # Actualiser l'interface
            self.progress_state.set(f'{self.instance.get_last_url_index()+1}/{self.instance.total}')
            self.percentage = (self.instance.get_last_url_index()+1)*100/self.instance.total
            self.progressbar['value'] = self.percentage
            self.progress_percentage.set(f'{float("{:.2f}".format(self.percentage))} %')
            self.status_value.set(f"{self.instance.msg_status if self.instance else 'en préparation ...'}")

            # Revérifier après une seconde
            self.schedule_check(t)
        
        if not self.instance.run:
            self.start_button['text'] = "Démarrer"
            self.start_button['command'] = self.start_booking_scraping

            # self.instance.stop()
            self.remove_button['state'] = 'normal'
    
    def set_index(self, index):
        self.index = index


class BookingContainer(Frame):
    def __init__(self, root, parent):
        super().__init__(parent, bg="#071215", width=900, height=700)

        # Propriétés
        self.root = root
        self.current_list = []
        self.dest_ids = StringVar(self)
        self.data_dest = StringVar(self)
        self.data_filename = StringVar(self)
        self.frequence = StringVar(self)

        # Widgets
        self.instances = Frame(self, bg="#071215", width=300, height=600)
        self.instances.pack_propagate(0)
        self.instances.place(x='600', y='0')

        instances_title = Label(self.instances, text="Scraping en cours", font=("Verdana", 11, "bold"), fg="#DDE", bg="#071215", anchor="w")
        instances_title.grid(row=0, column=0, padx= 0, pady= [20, 0], sticky="w")

        self.new_instance = Frame(self, bg="#071215", width=600, height=600)
        self.new_instance.place(x='0', y='0')

        self.instance_frame_content = Frame(self.new_instance, bg="#071215", width=600, height=580)
        self.instance_frame_content.place(x='0', y='10')

        self.instance_frame_content_title = Label(self.instance_frame_content, text="Nouvelle instance", font=("Verdana", 11, "bold"), fg="#DDE", bg="#071215")
        self.instance_frame_content_title.place(x='20', y='10')

        filename_label = Label(self.instance_frame_content, text="Nom du nouveau fichier:", font=("Verdana", 10), fg="#DDD", bg="#071215")
        filename_label.place(x='20', y='48')

        filename_urls_entree = Entry(self.instance_frame_content, textvariable=self.data_filename, font=("Verdana", 10))
        filename_urls_entree.place(x='20', y='80', width=420, height=32)

        interval_label = Label(self.instance_frame_content, text="Fréquence:", font=("Verdana", 10), fg="#DDD", bg="#071215")
        interval_label.place(x='450', y='48')

        freq_entree = Combobox(self.instance_frame_content, textvariable=self.frequence, font=("Verdana", 10))
        freq_entree['values'] = ('1', '3', '7')
        freq_entree.place(x='450', y='80', width=110, height=32)

        # source_label = Label(self.instance_frame_content, text="Liste destinations:", font=("Verdana", 10), fg="#DDD", bg="#071215")
        # source_label.place(x='20', y='128')

        # dest_ids_entree = Entry(self.instance_frame_content, textvariable=self.dest_ids, font=("Verdana", 10))
        # dest_ids_entree.place(x='20', y='160', width=254, height=32)

        # dest_ids_button_frame = Frame(self.instance_frame_content, highlightbackground='white', highlightthickness=1)
        # dest_ids_button_frame.place(x='202', y='192')

        # dest_ids_bouton = Button(dest_ids_button_frame, text="Parcourir", bg="#071215", fg="#DDD", command=self.browse_dest_ids_files, font=("Verdana", 10))
        # dest_ids_bouton.pack()

        # data_dest_label = Label(self.instance_frame_content, text="Enregistrer sous:", font=("Verdana", 10), fg="#DDD", bg="#071215")
        # data_dest_label.place(x='300', y='128')

        # data_dest_entree = Entry(self.instance_frame_content, textvariable=self.data_dest, font=("Verdana", 10))
        # data_dest_entree.place(x='300', y='160', width=260, height=32)

        # data_dest_button_frame = Frame(self.instance_frame_content, highlightbackground='white', highlightthickness=1)
        # data_dest_button_frame.place(x='488', y='192')

        # data_dest_bouton = Button(data_dest_button_frame, text="Parcourir", bg="#071215", fg="#DDD", command=self.browse_dest_folder, font=("Verdana", 10))
        # data_dest_bouton.pack()

        date_start_label = Label(self.instance_frame_content, text="Date début:", font=("Verdana", 10), fg="#DDD", bg="#071215")
        date_start_label.place(x='20', y='128')

        date_end_label = Label(self.instance_frame_content, text="Date fin:", font=("Verdana", 10), fg="#DDD", bg="#071215")
        date_end_label.place(x='310', y='128')

        self.cal_1 = Calendar(self.instance_frame_content, select_mode='day', year=datetime.now().year, month=datetime.now().month, day=datetime.now().day, locale="fr_FR", date_pattern='Y-m-d')
        self.cal_1.place(x='20', y='160')

        self.cal_2 = Calendar(self.instance_frame_content, select_mode='day', year=datetime.now().year, month=datetime.now().month, day=datetime.now().day, locale="fr_FR", date_pattern='Y-m-d')
        self.cal_2.place(x='310', y='160')

        add_scrap_button_frame = Frame(self.instance_frame_content, highlightbackground='#DDD', highlightthickness=2)
        add_scrap_button_frame.place(x='400', y='470', width=160)

        add_scrap_bouton = Button(add_scrap_button_frame, text="Ajouter", bg="#244", fg="#DDD", font=("Verdana", 10), width=40, command=self.add_instance)
        add_scrap_bouton.pack()

    def browse_dest_ids_files(self):
        filename = filedialog.askopenfilename(initialdir = "/",
                                            title = "Selectionner les fichiers",
                                            filetypes = (("CSV files", "*.csv*"),
                                                        ("all files", "*.*")))
        self.dest_ids.set(filename)

    def browse_dest_folder(self):
        filename = filedialog.askdirectory()
        self.data_dest.set(filename)

    def add_instance(self):
        if len(self.current_list) < 2:
            b = BookingInstance(root=self.root, parent=self.instances, container=self, filename=self.data_filename.get(),
                start=self.cal_1.get_date(), end=self.cal_2.get_date(), index=len(self.current_list), freq=self.frequence.get())
            b.grid(row=len(self.current_list)+1, column=0, padx= [0, 20], pady= 10)
            self.current_list.append(b)
        else:
            messagebox.showinfo("Information", "La liste est pleine !!!")

    def refresh(self):
        for instance in self.instances.winfo_children():
            if isinstance(instance, BookingInstance):
                instance.stop_booking_scraping()
                instance.destroy()
        
    #     for instance in self.current_list:
    #         instance.index -= 1
    #         # b = BookingInstance(root=self.root, parent=self.instances, container=self, filename=instance.filename, 
    #             # dest_ids=instance.dest_ids, path=instance.path, start=instance.start, end=instance.end, index=instance.index, freq=instance.freq)
    #         instance.grid(row=instance.index+1, column=0, padx= [0, 25], pady= 10)

    def remove_instance(self, index):
        messagebox.showinfo("Information", f"Vous voulez vraiment supprimer les instances?")
        self.current_list.clear()

        self.refresh()
