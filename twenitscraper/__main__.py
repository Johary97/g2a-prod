from tkinter import *
from tkinter import filedialog, messagebox
from tkinter.ttk import Combobox, Notebook, Style, Progressbar, LabelFrame
from twenitlib.twenitweb import clean_result, generate_sitemap
from twenitlib.seleniummaeva import MaevaScraping
from twenitcomponent.maeva import MaevaInstance, MaevaContainer
from twenitcomponent.booking import BookingContainer
from twenitcomponent.web import NormalizationFrame, SitemapFrame
from tkcalendar import Calendar
from datetime import datetime, timedelta
import threading


### Fenetre principale ###

fenetre = Tk()
fenetre.geometry('900x700')
fenetre.title('TwenIT - Scraper')
fenetre['bg'] = 'black'
fenetre.resizable(height=False, width=False)

title = Label(fenetre, text="TwenIT - Scraper Interface", font=("Verdana", 16, "bold"), fg="white", bg="black")
title.place(x='280', y='30')

style = Style()
style.theme_create( "dark_th", parent="alt", settings={
        "TNotebook": {"configure": {"tabmargins": [0, 0, 0, 0], "background": "black" } },
        "TNotebook.Tab": {
            "configure": {"background": "black", "foreground": "white", "font": ('URW Gothic L', '11', 'bold'), "padding": [10, 10, 10, 10] },
            "map":       {"background": [("selected", "#011013")],
                          "expand": [("selected", [0, 0, 0, 0])] } } } )

style.theme_use("dark_th")

notebook = Notebook(fenetre)
notebook.pack(pady=(90, 0), expand = 1, fill ="both")

webframe = Frame(notebook, bg="#071215", width=900, height=700)
webframe.pack()

selenium_frame = MaevaContainer(fenetre, notebook)
selenium_frame.pack()

selenium_booking = BookingContainer(fenetre, notebook)
selenium_booking.pack()

notebook.add(webframe, text="web-scraper")
notebook.add(selenium_frame, text="MAEVA selenium")
notebook.add(selenium_booking, text="Booking selenium")

### Frame 1: Générer les sitemaps ### 

sitemap_frame = SitemapFrame(fenetre, webframe)
sitemap_frame.place(x='0', y='0')

### Frame 2: Normalisation resultats ###

normalization_frame = NormalizationFrame(fenetre, webframe)
normalization_frame.place(x='600', y='0')

fenetre.mainloop()