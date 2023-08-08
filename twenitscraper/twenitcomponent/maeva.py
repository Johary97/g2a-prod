from tkinter import *
from tkinter import filedialog, messagebox
from tkinter.ttk import Combobox, Notebook, Style, Progressbar, LabelFrame
from twenitlib.seleniummaeva import MaevaScraping
import threading
import os


class MaevaInstance(Frame):

    def __init__(self, root, parent, container, filename, urls, path, index):
        super().__init__(parent)
        self['bg'] = "#152525"
        self['width'] = 400
        self['height'] = 220
        self['highlightbackground'] = "#999"
        self['highlightthickness'] = 1
        self.root = root
        self.index = index
        self.parent = parent
        self.container = container
        self.filename = filename
        self.urls = urls
        self.path = path

        self.instance = MaevaScraping(urls=urls, dest_name=filename, dest_folder=path)

        self.filepath = self.instance.full_path
        self.percentage = int((self.instance.get_last_index()[0]+1)*100/self.instance.total)

        self.progress_percentage = StringVar(self)
        self.progress_state = StringVar(self)
        self.saved_data = IntVar(self)

        self.progress_percentage.set(f'{self.percentage}%')
        self.progress_state.set(f'{self.instance.get_last_index()[0]+1}/{self.instance.total}')
        self.saved_data.set(0)

        path_label = Label(self, text="Nom de l'instance:", font=("Verdana", 10), fg="#DDD", bg="#152525")
        path_label.place(x='10', y='26')

        path_value = Label(self, text=self.filename, font=("Verdana", 10, "bold"), fg="#EFEFFF", bg="#152525")
        path_value.place(x='140', y='26')

        progress_label = Label(self, text="Progression:", font=("Verdana", 10), fg="#DDD", bg="#152525")
        progress_label.place(x='10', y='59')

        progress_value = Label(self, textvariable=self.progress_state, font=("Verdana", 10, "bold"), fg="#DDD", bg="#152525")
        progress_value.place(x='140', y='59')

        progress_label = Label(self, text="Enregistré(s):", font=("Verdana", 10), fg="#DDD", bg="#152525")
        progress_label.place(x='10', y='92')

        progress_value = Label(self, textvariable=self.saved_data, font=("Verdana", 10, "bold"), fg="#DDD", bg="#152525")
        progress_value.place(x='140', y='92')

        self.progressbar = Progressbar(
            self,
            orient='horizontal',
            mode='determinate',
            length=320
        )

        self.progressbar.place(x='10', y='128')

        progress_percentage = Label(self, textvariable=self.progress_percentage, font=("Verdana", 10, "bold"), fg="#DDD", bg="#152525")
        progress_percentage.place(x='336', y='128')

        remove_button_frame = Frame(self, highlightbackground='#DDD', highlightthickness=2)
        remove_button_frame.place(x='10', y='168', width=100)

        open_button_frame = Frame(self, highlightbackground='#DDD', highlightthickness=2)
        open_button_frame.place(x='145', y='168', width=100)

        start_button_frame = Frame(self, highlightbackground='#DDD', highlightthickness=2)
        start_button_frame.place(x='280', y='168', width=100)

        self.remove_button = Button(remove_button_frame, text="Supprimer", bg="#cf2121", fg="#DDD", font=("Verdana", 10), width=40, command=self.remove_scraping)
        self.remove_button.pack()

        open_bouton = Button(open_button_frame, text="Ouvrir", bg="#244", fg="#DDD", font=("Verdana", 10), width=40, command=self.open_result)
        open_bouton.pack()

        self.start_button = Button(start_button_frame, text="Démarrer", bg="#23ac63", fg="#DDD", font=("Verdana", 10), width=40, command=self.start_scraping)
        self.start_button.pack()

    def start_scraping(self):
        self.start_button['text'] = "Arreter"
        self.start_button['command'] = self.stop_scraping
        self.remove_button['state'] = 'disabled'

        t = threading.Thread(target=self.scraping_worker)
        t.start()

        # Commencer à vérifier périodiquement si le process est terminé.
        self.schedule_check(t)
        return

    def stop_scraping(self):
        self.start_button['text'] = "Démarrer"
        self.start_button['command'] = self.start_scraping

        self.instance.stop()
        self.remove_button['state'] = 'normal'
        return

    def remove_scraping(self):
        self.container.remove_instance(self.index)

    def open_result(self):
        os.system(f'start {self.instance.result_folder}')

    def scraping_worker(self):
        self.instance.start()

    def schedule_check(self, t):
        self.root.after(1000, self.check_if_done, t)

    def check_if_done(self, t):

        # Afficher un message si le process s'arrête
        if not t.is_alive():
            messagebox.showinfo("Information", "Scaping arrêté !")
        else:
            # Actualiser l'interface
            indexes = self.instance.get_last_index()
            self.progress_state.set(f'{indexes[0]+1}/{self.instance.total}')
            self.percentage = (indexes[0]+1)*100/self.instance.total
            self.progressbar['value'] = self.percentage
            self.progress_percentage.set(f'{float("{:.2f}".format(self.percentage))} %')
            self.saved_data.set(indexes[1])

            # Revérifier après une seconde
            self.schedule_check(t)
    
    def set_index(self, index):
        self.index = index


class MaevaContainer(Frame):
    def __init__(self, root, parent):
        super().__init__(parent, bg="#071215", width=900, height=700)

        # Propriétés
        self.root = root
        self.current_list = []
        self.urls_source = StringVar(self)
        self.data_dest = StringVar(self)
        self.data_filename = StringVar(self)

        # Widgets
        self.instances = Frame(self, bg="#071215", width=450, height=600)
        self.instances.pack_propagate(0)
        self.instances.place(x='450', y='0')

        instances_title = Label(self.instances, text="Scraping en cours", font=("Verdana", 11, "bold"), fg="#DDE", bg="#071215", anchor="w")
        instances_title.grid(row=0, column=0, padx= 20, pady= [20, 0], sticky="w")

        self.new_instance = Frame(self, bg="#071215", width=450, height=600)
        self.new_instance.place(x='0', y='0')

        self.instance_frame_content = Frame(self.new_instance, bg="#071215", width=450, height=500)
        self.instance_frame_content.place(x='0', y='10')

        self.instance_frame_content_title = Label(self.instance_frame_content, text="Nouvelle instance", font=("Verdana", 11, "bold"), fg="#DDE", bg="#071215")
        self.instance_frame_content_title.place(x='20', y='10')

        filename_label = Label(self.instance_frame_content, text="Nom du nouveau fichier:", font=("Verdana", 10), fg="#DDD", bg="#071215")
        filename_label.place(x='20', y='48')

        filename_urls_entree = Entry(self.instance_frame_content, textvariable=self.data_filename, font=("Verdana", 10))
        filename_urls_entree.place(x='20', y='80', width=400, height=32)

        source_label = Label(self.instance_frame_content, text="Fichiers contenant les urls:", font=("Verdana", 10), fg="#DDD", bg="#071215")
        source_label.place(x='20', y='128')

        source_urls_entree = Entry(self.instance_frame_content, textvariable=self.urls_source, font=("Verdana", 10))
        source_urls_entree.place(x='20', y='160', width=400, height=32)

        source_urls_button_frame = Frame(self.instance_frame_content, highlightbackground='white', highlightthickness=1)
        source_urls_button_frame.place(x='348', y='161')

        urls_source_bouton = Button(source_urls_button_frame, text="Parcourir", bg="#071215", fg="#DDD", command=self.browse_urls_source_files, font=("Verdana", 10))
        urls_source_bouton.pack()

        data_dest_label = Label(self.instance_frame_content, text="Enregistrer sous:", font=("Verdana", 10), fg="#DDD", bg="#071215")
        data_dest_label.place(x='20', y='210')

        data_dest_entree = Entry(self.instance_frame_content, textvariable=self.data_dest, font=("Verdana", 10))
        data_dest_entree.place(x='20', y='240', width=400, height=32)

        data_dest_button_frame = Frame(self.instance_frame_content, highlightbackground='white', highlightthickness=1)
        data_dest_button_frame.place(x='348', y='241')

        data_dest_bouton = Button(data_dest_button_frame, text="Parcourir", bg="#071215", fg="#DDD", command=self.browse_dest_folder, font=("Verdana", 10))
        data_dest_bouton.pack()

        add_scrap_button_frame = Frame(self.instance_frame_content, highlightbackground='#DDD', highlightthickness=2)
        add_scrap_button_frame.place(x='262', y='300', width=160)

        add_scrap_bouton = Button(add_scrap_button_frame, text="Ajouter", bg="#244", fg="#DDD", font=("Verdana", 10), width=40, command=self.add_instance)
        add_scrap_bouton.pack()

    def browse_urls_source_files(self):
        filename = filedialog.askopenfilename(initialdir = "/",
                                            title = "Selectionner les fichiers",
                                            filetypes = (("Excel files", "*.xlsx*"), ("CSV files", "*.csv*"),
                                                        ("all files", "*.*")))
        self.urls_source.set(filename)

    def browse_dest_folder(self):
        filename = filedialog.askdirectory()
        self.data_dest.set(filename)

    def add_instance(self):
        if len(self.current_list) < 2:
            m = MaevaInstance(root=self.root, parent=self.instances, container=self, filename=self.data_filename.get(), urls=self.urls_source.get(), path=self.data_dest.get(), index=len(self.current_list))
            m.grid(row=len(self.current_list)+1, column=0, padx= [30, 25], pady= 20)
            self.current_list.append(m)
        else:
            messagebox.showinfo("Information", "La liste est pleine !!!")

    def refresh(self):
        for instance in self.instances.winfo_children():
            if isinstance(instance, MaevaInstance):
                instance.stop_scraping()
                instance.destroy()
        
        for instance in self.current_list:
            m = MaevaInstance(root=self.root, parent=self.instances, container=self, filename=instance.filename, urls=instance.urls, path=instance.path, index=instance.index)
            m.grid(row=instance.index+1, column=0, padx= [30, 25], pady= 20)

    def remove_instance(self, index):
        messagebox.showinfo("Information", f"Vous voulez vraiment supprimer l'instance {index + 1} ?")
        self.current_list.pop(index)
        if len(self.current_list):
            for i in range(0, len(self.current_list)):
                self.current_list[i].set_index(i)

        self.refresh()
