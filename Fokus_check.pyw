#!/usr/bin/env python3
# Exe erzeugen mit pyinstaller --onefile --noconsole Fokus_check.pyw
# import time
import pyautogui
# from collections import defaultdict
import pygame
import os
import requests
# from PIL import Image
import threading
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QMainWindow, QFrame, QSpacerItem, QSizePolicy, QHBoxLayout, QSlider, QProgressBar, QComboBox
from PyQt5.QtCore import Qt
from PyQt5 import QtGui
from PyQt5.QtGui import QPixmap, QImage


class environment:
    def __init__(self):
        self.running = True
        self.gewarnt = False
        self.threads = []
        self.event_check_fokus = threading.Event()
        self.screen_fokus = None
        self.statusdisplay_fokus_image = None
        self.statusdisplay_fokus_progressbar = None

    def init_statusdisplay_fokus_image(self):
        self.statusdisplay_fokus_image = QLabel()

    def update_statusdisplay_fokus_image(self):
        if self.screen_fokus is not None:
            qimage = QImage(self.screen_fokus.tobytes(), self.screen_fokus.width, self.screen_fokus.height, self.screen_fokus.width * 3, QImage.Format_RGB888)
            qpixmap = QPixmap.fromImage(qimage)
            self.statusdisplay_fokus_image.setPixmap(qpixmap)

    def set_screen_fokus(self,screen_fokus):
        self.screen_fokus = screen_fokus
        self.update_statusdisplay_fokus_image()

    def init_statusdisplay_fokus_progressbar(self):
        self.statusdisplay_fokus_progressbar = QProgressBar()
        self.statusdisplay_fokus_progressbar.setFixedWidth(210)
        self.statusdisplay_fokus_progressbar.setFixedHeight(30)
        # self.statusdisplay_fokus_progressbar.setStyleSheet(f'QProgressBar::chunk {{}} ; background-color: white; border: 1px solid black; padding: 0px ; color: black; font-size: 14px')
        # self.statusdisplay_fokus_progressbar.setStyleSheet(f'QProgressBar::chunk {{background-color: pink; }}')
        # ??? bar -- border-style: outset; border-width: 2px; border-color: #74c8ff; border-radius: 7px; margin-top: 1em;
        # ??? chunk -- margin: 0px; width: 10px; border-bottom-right-radius: 10px; border-bottom-left-radius: 10px;
        #  fokus 242, 130, 254 = #F282FE
        self.statusdisplay_fokus_progressbar.setRange(0, 100)
        self.statusdisplay_fokus_progressbar.setValue(-1)

    def update_statusdisplay_fokus_progressbar(self, value):
        value = f'{value:.0f}'
        value = int(value)
        if self.statusdisplay_fokus_progressbar is not None:
            self.statusdisplay_fokus_progressbar.setValue(value)

    def set_running(self,running):
        self.running = running

    def set_gewarnt(self,gewarnt):
        self.gewarnt = gewarnt
    
    def set_mp3_Fokuswarnung(self,mp3_Fokuswarnung):
        self.mp3_Fokuswarnung = mp3_Fokuswarnung
    
    def set_debug_label(self,debug_label):
        self.debug_label = debug_label
    
    def update_debug_label(self, message):
        self.debug_label.setText(message)
    
    def add_debug_message(self, message):
        self.debug_label.setText(self.debug_label.text() + '\n' + message)

class myconfig:
    def __init__(self,config_file='fokus.conf'):
        self.config_file = config_file
        self.set_system_variables()
        self.set_user_default()
        self.read_configfile()
        self.check_config()
        self.calculate_variables()

    def set_system_variables(self):
        self.fokus_voll_color = (242, 130, 254)  # Fokus voll
        self.fokus_leer_color_min = (38, 36, 57)  # Fokus leer (min)
        self.fokus_leer_color_max = (44, 44, 62)  # Fokus leer (max)

    def set_user_default(self):
        self.debug = False
        self.debug_level = 0
        self.warnschwelle = 33
        self.intervall = 10
        self.mp3_fokuswarnung = 'Fokuswarnung.mp3'
        self.volume_fokuswarnung = 100
        self.theme = 'light'

    def set_theme(self,theme):
        self.theme = theme

    def set_debug(self,debug):
        self.debug = debug

    def set_debug_level(self,debug_level):
        self.debug_level = debug_level

    def set_warnschwelle(self,warnschwelle):
        self.warnschwelle = warnschwelle

    def set_intervall(self,intervall):
        self.intervall = intervall

    def set_volume_fokuswarnung(self,volume_fokuswarnung):
        self.volume_fokuswarnung = volume_fokuswarnung

    def read_configfile(self):
        try:
            with open(self.config_file, 'r') as file:
                for line in file:
                    if line.startswith('x1, y1 ='):
                        self.x1, self.y1 = map(int, line.split('=')[1].split('#')[0].strip().split(','))
                    elif line.startswith('x2, y2 ='):
                        self.x2, self.y2 = map(int, line.split('=')[1].split('#')[0].strip().split(','))
                    elif line.startswith('debug ='):
                        self.debug = line.split('=')[1].split('#')[0].strip() == 'True'
                    elif line.startswith('debug_level ='):
                        self.debug_level = int(line.split('=')[1].split('#')[0].strip())
                    elif line.startswith('warnschwelle ='):
                        self.warnschwelle = int(line.split('=')[1].split('#')[0].strip())
                    elif line.startswith('intervall ='):
                        self.intervall = int(line.split('=')[1].split('#')[0].strip())
                    elif line.startswith('mp3_fokuswarung ='):
                        self.mp3_fokuswarnung = line.split('=')[1].split('#')[0].strip()
                    elif line.startswith('volume_fokuswarnung'):
                        self.volume_fokuswarnung = int(line.split('=')[1].split('#')[0].strip())
                    elif line.startswith('theme ='):
                        self.theme = line.split('=')[1].split('#')[0].strip().strip("'").strip('"')


        except FileNotFoundError:
            print("Die Datei wurde nicht gefunden.")
        except PermissionError:
            print("Du hast keine Berechtigung, die Datei zu lesen.")
        except Exception as e:
            print("Ein unbekannter Fehler ist aufgetreten:", str(e))

    def write_configfile(self,config_name,value):
        dprint(self,3,"Schreibe Konfigurationsdatei")
        found = False
        format = 'int'
        content= []
        if config_name == 'debug':
            value = bool(value)
            format = 'bool'
        if config_name in ['theme','mp3_fokuswarnung']:
            format = 'string'
        try:
            with open(self.config_file, 'r') as file:
                for line in file:
                    if line.startswith(config_name):
                        found = True
                        comment = line.split('#', 1)[-1].strip()
                        if format in ['int','bool']:
                            new_line = f"{config_name} = {value} # {comment}\n"
                        elif format == 'string':
                            new_line = f"{config_name} = '{value}' # {comment}\n"
                            
                        content.append(new_line)
                    else:
                        line = line.rstrip('\n') # remove newline
                        line += '\n' # add newline
                        content.append(line)
                if found == False:
                    if format in ['int','bool']:
                        new_line = f'{config_name} = {value} # \n'
                    elif format == 'string':
                        new_line = f"{config_name} = '{value}' # \n"
                    content.append(new_line)
            with open(self.config_file, 'w') as file:
                file.writelines(content)
        except FileNotFoundError:
            print("Die Datei wurde nicht gefunden.")
        except PermissionError:
            print("Du hast keine Berechtigung, die Datei zu lesen.")
        except Exception as e:
            print("Ein unbekannter Fehler ist aufgetreten:", str(e))                
                
    def check_config(self):
        if not all(var is not None for var in (self.x1, self.x2, self.y1, self.y2)):
            print(f"Bitte die Ecken des zu überprüfenden Bereichs in der {self.config_file} eintragen.")
            exit()
        if self.x2 < self.x1 or self.y2 < self.y1:
            print(f"Die Ecken des zu überprüfenden Bereichs sind falsch in der {self.config_file} eingetragen.")
            exit()
    
    def calculate_variables(self):
        self.bar_breite = self.x2 - self.x1

def count_pixels(env,config):
    # Erfasse den Bildschirmbereich
    screenshot = get_screenshot(env,'screen_fokus',config.x1, config.y1, config.x2, config.y2)
    # Initialisiere den Zähler für Pixel
    fokus_voll_pixel_count = 0
    fokus_leer_pixel_count = 0
    # if config.debug == True:
    #     color_counts = defaultdict(int)

    # Durchlaufe die Pixel im erfassten Bereich
    for x in range(config.x2 - config.x1):
        for y in range(config.y2 - config.y1):
            pixel_color = screenshot.getpixel((x, y))
            dprint(config,3,f"Pixel {x} {y} Farb:{pixel_color}")
            # color_tupel = tuple(pixel_color)
            # color_counts[color_tupel] += 1

            # Überprüfe, ob die Farbe des Pixels für Voll steht 
            if pixel_color == config.fokus_voll_color:
                fokus_voll_pixel_count += 1
            # Überprüfe, ob die Farbe des Pixels für Leer steht
            if (    config.fokus_leer_color_min[0] <= pixel_color[0] <= config.fokus_leer_color_max[0]) and (
                    config.fokus_leer_color_min[1] <= pixel_color[1] <= config.fokus_leer_color_max[1]) and (
                    config.fokus_leer_color_min[2] <= pixel_color[2] <= config.fokus_leer_color_max[2]):
                fokus_leer_pixel_count += 1

    return fokus_voll_pixel_count, fokus_leer_pixel_count

def get_fokus_sichtbar(env,config,fokus_leer,fokus_voll):
    gesamt_erkannt = fokus_voll + fokus_leer
    fokus_sichtbar = gesamt_erkannt / config.bar_breite * 100
    dprint(config,3,f"Fokus sichtbar: {fokus_sichtbar:.0f}%")
    return fokus_sichtbar

def sound_play(sound):
    sound.play()

def get_screenshot(env,screen_name,x1,y1,x2,y2):
    screenshot = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
    if screen_name == 'screen_fokus' and env.statusdisplay_fokus_image is not None:
        env.set_screen_fokus(screenshot)
    return screenshot

def check_fokus(env,config):
    fokus_voll,fokus_leer = count_pixels(env,config)
    fokus_sichtbar = get_fokus_sichtbar(env,config,fokus_leer,fokus_voll)
    if fokus_sichtbar > 70:
            prozent_voll = fokus_voll / (fokus_voll + fokus_leer) * 100
            if prozent_voll < config.warnschwelle:
                dprint(config,1,"Fokuswarnung")
                if env.gewarnt == False:
                    env.set_gewarnt(True)
                    sound_play(env.mp3_Fokuswarnung)
            else:
                if env.gewarnt == True:
                    env.set_gewarnt(False)
            dprint(config,3,f"Fokus Pixel Voll: {fokus_voll}")
            dprint(config,3,f"Fokus Pixel Leer: {fokus_leer}")
            dprint(config,1,f"Prozentualer Fokus: {prozent_voll:.0f}%")

            env.update_statusdisplay_fokus_progressbar(prozent_voll)
    else:
        dprint(config,1,"Fokus nicht sichtbar")

def fokus_check(env,config):
    while env.running == True:
        check_fokus(env,config)
        env.event_check_fokus.wait(config.intervall)
        env.event_check_fokus.clear()

def gui_sound_test(env):
    sound_play(env.mp3_Fokuswarnung)

def dprint(config,level,message):
    # Debuglevel 
    # 0: keine Ausgabe
    # 1: Ausgabe Common
    # 2: Ausgabe Info
    # 3: Ausgabe Debug
    if level <= config.debug_level:
        print(message)

class MainWindow(QMainWindow):
    def __init__(self,env,config):
        super().__init__()

        self.config_widget_width = 540
        self.config_widget_height = 60
        self.config_widget_border_radius = 10
        count_widgets = 5
        self.config_frame_width = 560
        self.config_frame_height = count_widgets * 60 + 40

        self.config_label_width = 270
        self.config_label_height = 40
        self.config_slider_width = 200
        self.config_slider_height = 40
        self.config_button_width = 50
        self.config_value_text_width = 40
        self.config_value_text_height = 30

        self.statusdisplay_frame_width = 560
        self.statusdisplay_frame_height = 278
        self.statusdisplay_widget_width = 540
        self.statusdisplay_widget_height = 50
        self.statusdisplay_widget_border_radius = 10
        self.statusdisplay_label_width = 270
        self.statusdisplay_label_height = 30

        self.window_width = 580
        self.window_height = 8 + self.config_frame_height + 8 + self.statusdisplay_frame_height + 8

        self.init_theme()
        self.load_theme(env,config)
        self.initUI(env,config)

    def init_theme(self):
        self.theme_color_window_background = 'lightgrey'
        self.theme_color_frame_config_background = 'yellow'
        self.theme_color_config_widget_background = '#C2C2C2'
        self.theme_color_config_label_font = 'black'
        self.theme_color_config_combo_box_background = 'white'
        self.theme_color_config_combo_box_font = 'black'
        self.theme_color_config_combo_box_selection_background = '#3399ff'
        self.theme_color_config_combo_box_selection_font = 'black'

        self.theme_config_slider_border = '1px solid black'
        self.theme_color_config_slider_groove_background = 'white'
        self.theme_color_config_slider_handle_background = '#3399ff'
        self.theme_color_config_slider_add_page_background = 'white'
        self.theme_color_config_slider_sub_page_background = '#3399ff'

        self.theme_color_config_bubble_background = '#ffffff'
        self.theme_color_config_bubble_font = '#000000'
        self.theme_config_bubble_border = '1px solid #C2C2C2'

        self.theme_color_frame_display_background = 'lightgreen'        

        self.theme_color_display_fokusbar_background = '#ffffff'
        self.theme_color_display_fokusbar_font = '#000000'
        self.theme_align_display_fokusbar_text_align = 'center'
        self.theme_color_display_fokusbar_chunk_background = '#F282FE'
        self.theme_display_fokusbar_chunk_border = '1px solid #C2C2C2'
        self.theme_display_fokusbar_chunk_border_radius = '10px'

        self.statusdisplay_color_background = '#C2C2C2' 
        self.statusdisplay_color_font = 'black'

    def load_theme(self,env,config):
        theme_name = config.theme
        theme_dir = 'themes'
        theme_file = os.path.join(theme_dir, theme_name + '.theme')
        default_theme_file = os.path.join(theme_dir, 'light.theme')

        if not os.path.exists(theme_dir):
            os.makedirs(theme_dir)
        
        if not os.path.isfile(default_theme_file):
            github_url = "https://raw.githubusercontent.com/Bluedai/Fokus_check/main/themes/light.theme"
            response = requests.get(github_url)
            if response.status_code == 200:
                with open(default_theme_file, 'wb') as file:
                    file.write(response.content)

        if not os.path.isfile(theme_file):
            theme_file = os.path.join(theme_dir, 'light.theme')
        
        try:
            with open(theme_file, 'r') as file:
                # print(f"Lade Theme: {theme_name} aus {theme_file}")
                for line in file:
                    if line.startswith('window_background ='):
                        self.theme_color_window_background = line.split('=')[1].split("'")[1].strip()
                        # print(f"debug - window_background: {self.theme_color_window_background}")
                    elif line.startswith('frame_config_background ='):
                        self.theme_color_frame_config_background = line.split('=')[1].split("'")[1].strip()
                        # print(f"frame_config_background: {self.theme_color_frame_config_background}")
                    elif line.startswith('frame_display_background ='):
                        self.theme_color_frame_display_background = line.split('=')[1].split("'")[1].strip()
                        # print(f"frame_display_background: {self.theme_color_frame_display_background}")
                    elif line.startswith('widget_background ='):
                        self.theme_color_config_widget_background = line.split('=')[1].split("'")[1].strip()
                        # print(f"widget_background: {self.theme_color_config_widget_background}")
                    elif line.startswith('widget_font ='):
                        self.theme_color_config_label_font = line.split('=')[1].split("'")[1].strip()
                        # print(f"widget_font: {self.theme_color_config_label_font}")
                    elif line.startswith('config_combo_box_background ='):
                        self.theme_color_config_combo_box_background = line.split('=')[1].split("'")[1].strip()
                        # print(f"config_combo_box_background: {self.theme_color_config_combo_box_background}")
                    elif line.startswith('config_combo_box_font ='):
                        self.theme_color_config_combo_box_font = line.split('=')[1].split("'")[1].strip()
                        # print(f"config_combo_box_font: {self.theme_color_config_combo_box_font}")
                    elif line.startswith('config_combo_box_selection_background ='):
                        self.theme_color_config_combo_box_selection_background = line.split('=')[1].split("'")[1].strip()
                        # print(f"config_combo_box_selection_background: {self.theme_color_config_combo_box_selection_background}")
                    elif line.startswith('config_combo_box_selection_font ='):
                        self.theme_color_config_combo_box_selection_font = line.split('=')[1].split("'")[1].strip()
                        # print(f"config_combo_box_selection_font: {self.theme_color_config_combo_box_selection_font}")
                    elif line.startswith('config_slider_border ='):
                        self.theme_config_slider_border = line.split('=')[1].split("'")[1].strip()
                        # print(f"config_slider_border: {self.theme_config_slider_border}")
                    elif line.startswith('config_slider_groove_background ='):
                        self.theme_color_config_slider_groove_background = line.split('=')[1].split("'")[1].strip()
                        # print(f"config_slider_groove_background: {self.theme_color_config_slider_groove_background}")
                    elif line.startswith('config_slider_handle_background ='):
                        self.theme_color_config_slider_handle_background = line.split('=')[1].split("'")[1].strip()
                        # print(f"config_slider_handle_background: {self.theme_color_config_slider_handle_background}")
                    elif line.startswith('config_slider_add_page_background ='):
                        self.theme_color_config_slider_add_page_background = line.split('=')[1].split("'")[1].strip()
                        # print(f"config_slider_add_page_background: {self.theme_color_config_slider_add_page_background}")
                    elif line.startswith('config_slider_sub_page_background ='):
                        self.theme_color_config_slider_sub_page_background = line.split('=')[1].split("'")[1].strip()
                        # print(f"config_slider_sub_page_background: {self.theme_color_config_slider_sub_page_background}")
                    elif line.startswith('display_fokusbar_background ='):
                        self.theme_color_display_fokusbar_background = line.split('=')[1].split("'")[1].strip()
                        # print(f"display_fokusbar_background: {self.theme_color_display_fokusbar_background}")
                    elif line.startswith('display_fokusbar_font ='):
                        self.theme_color_display_fokusbar_font = line.split('=')[1].split("'")[1].strip()
                        # print(f"display_fokusbar_font: {self.theme_color_display_fokusbar_font}")
                    elif line.startswith('display_fokusbar_text_align ='):
                        self.theme_align_display_fokusbar_text_align = line.split('=')[1].split("'")[1].strip()
                        # print(f"display_fokusbar_text_align: {self.theme_align_display_fokusbar_text_align}")
                    elif line.startswith('display_fokusbar_chunk_background ='):
                        self.theme_color_display_fokusbar_chunk_background = line.split('=')[1].split("'")[1].strip()
                        # print(f"display_fokusbar_chunk_background: {self.theme_color_display_fokusbar_chunk_background}")
                    elif line.startswith('display_fokusbar_chunk_border ='):
                        self.theme_display_fokusbar_chunk_border = line.split('=')[1].split("'")[1].strip()
                        # print(f"display_fokusbar_chunk_border: {self.theme_display_fokusbar_chunk_border}")
                    elif line.startswith('display_fokusbar_chunk_border_radius ='):
                        self.theme_display_fokusbar_chunk_border_radius = line.split('=')[1].split("'")[1].strip()
                        # print(f"display_fokusbar_chunk_border_radius: {self.theme_display_fokusbar_chunk_border_radius}")
                    elif line.startswith('config_bubble_background ='):
                        self.theme_color_config_bubble_background = line.split('=')[1].split("'")[1].strip()
                        # print(f"config_bubble_background: {self.theme_color_config_bubble_background}")
                    elif line.startswith('config_bubble_font ='):
                        self.theme_color_config_bubble_font = line.split('=')[1].split("'")[1].strip()
                        # print(f"config_bubble_font: {self.theme_color_config_bubble_font}")
                    elif line.startswith('config_bubble_border ='):
                        self.theme_config_bubble_border = line.split('=')[1].split("'")[1].strip()
                        # print(f"config_bubble_border: {self.theme_config_bubble_border}")

        except FileNotFoundError:
            print(f"Die Datei {themefile} wurde nicht gefunden.")
        except PermissionError:
            print(f"Du hast keine Berechtigung, die Datei {themefile} zu lesen.")
        except Exception as e:
            print("Ein unbekannter Fehler ist aufgetreten:", str(e))

    def gui_repaint_config_widgets(self,env,config):
        widgetcount = 0
        for widget in self.config_frame.children():
            if widget.isWidgetType():
                widgetcount += 1
                self.set_config_widget_stylesheet(widget)
                widget_child_count = 0
                for widget_child in widget.children():
                    # print(f"widget_child: {widget_child.__class__.__name__}")
                    if isinstance(widget_child, QLabel):
                        widget_child_count += 1
                        if widget_child_count == 1:
                            self.set_label_stylesheet(widget_child)
                        elif widget_child_count == 2: 
                            self.set_config_bubble_stylesheet(widget_child)
                    elif isinstance(widget_child, QComboBox):
                        self.set_config_combo_box_stylesheet(widget_child)
                    elif isinstance(widget_child, QSlider):
                        self.set_config_slider_stylesheet(widget_child)

    def gui_repaint_display_widgets(self,env,config):
        widgetcount = 0
        for widget in self.display_frame.children():
            if widget.isWidgetType():
                widgetcount += 1
                self.set_config_widget_stylesheet(widget)
                widget_child_count = 0
                for widget_child in widget.children():
                    # print(f"widget_child: {widget_child.__class__.__name__}")
                    if isinstance(widget_child, QLabel):
                        widget_child_count += 1
                        if widget_child_count == 1:
                            self.set_label_stylesheet(widget_child)
        self.set_display_fokusbar_stylesheet(env)

    def gui_repaint(self,env,config):
        self.set_main_stylesheet() 
        self.set_frame_config_stylesheet()
        self.set_frame_display_stylesheet()
        
        self.gui_repaint_config_widgets(env,config)
        self.gui_repaint_display_widgets(env,config)
        
        self.repaint()

    def create_config_frame(self):
        self.config_frame = QFrame(self)
        self.config_frame.setFrameShape(QFrame.StyledPanel)
        self.config_frame.setFixedSize(self.config_frame_width , self.config_frame_height) 
        self.set_frame_config_stylesheet()

    def create_display_frame(self):
        self.display_frame = QFrame(self)
        self.display_frame.setFrameShape(QFrame.StyledPanel)
        self.display_frame.setFixedSize(self.statusdisplay_frame_width , self.statusdisplay_frame_height)
        self.set_frame_display_stylesheet()

    def create_button_frame(self):
        button_frame = QFrame(self)
        button_frame.setFrameShape(QFrame.StyledPanel)
        button_frame.setStyleSheet('background-color: lightgreen')
        button_frame.setMinimumSize(100, 100)
        button_frame.setMaximumSize(100, 100)
        return button_frame

    def create_debug_frame(self):
        debug_frame = QFrame(self)
        debug_frame.setFrameShape(QFrame.StyledPanel)
        debug_frame.setStyleSheet('background-color: lightblue')
        return debug_frame
    
    def get_max_radius(self,width,height):
        return height//2 if height < width else width//2
    
    def create_slider_style_sheet(self,groove_height,handle_margin,groove_color_background,handle_color_background,sub_page_color_background,add_page_color_background):
        style_sheet = f'QSlider::groove:horizontal   {{ border: {self.theme_config_slider_border}; background: {groove_color_background}  ;border-radius: 4px; height: {groove_height}px; margin: 0px 0; }} \
                        QSlider::handle:horizontal   {{ border: {self.theme_config_slider_border}; background: {handle_color_background}  ;border-radius: 4px; width: 10px; margin: {handle_margin}px 0; }} \
                        QSlider::sub-page:horizontal {{ border: {self.theme_config_slider_border}; background: {sub_page_color_background};border-radius: 4px; }} \
                        QSlider::add-page:horizontal {{ border: {self.theme_config_slider_border}; background: {add_page_color_background};border-radius: 4px; }} \
                        '
        return style_sheet
    
    def calculate_slider_componets_size(self,height):
        groove_height = height//3
        handle_margin = -height//5
        return groove_height,handle_margin
    
    def create_slider(self,width,height,min,max,value):
        slider = QSlider(Qt.Horizontal)
        slider.setFixedWidth(width)
        slider.setFixedHeight(height)
        groove_height, handle_margin = self.calculate_slider_componets_size(height)
        slider.setStyleSheet(self.create_slider_style_sheet(groove_height,handle_margin,self.theme_color_config_slider_groove_background,self.theme_color_config_slider_handle_background,self.theme_color_config_slider_sub_page_background,self.theme_color_config_slider_add_page_background))
        slider.setRange(min, max)
        slider.setValue(value)
        return slider

    def show_config_volume_fokuswarnung(self,env,config):
        widget = QWidget()
        widget.setFixedWidth(self.config_widget_width)
        widget.setFixedHeight(self.config_widget_height)
        self.set_config_widget_stylesheet(widget)

        layout = QHBoxLayout()

        label = QLabel('Warnlautstärke')
        label.setFixedWidth(self.config_label_width-self.config_button_width-5-1) # -5 wegen padding -1 wegen weiß noch nicht warum
        label.setFixedHeight(self.config_label_height)
        self.set_label_stylesheet(label)
        layout.addWidget(label)

        play_button = QPushButton('Test')
        play_button.setFixedWidth(self.config_button_width)
        play_button.setStyleSheet('background-color: lightgrey; border: 1px solid black; padding: 5px ; color: black; font-size: 14px')
        play_button.clicked.connect(lambda: sound_play(env.mp3_Fokuswarnung))
        layout.addWidget(play_button)

        slider = self.create_slider(self.config_slider_width,self.config_slider_height,0,100,config.volume_fokuswarnung)
        slider.valueChanged.connect(lambda volume: (config.set_volume_fokuswarnung(volume), set_volume(env.mp3_Fokuswarnung, volume), label_volume.setText(str(volume))))
        slider.sliderReleased.connect(lambda: config.write_configfile('volume_fokuswarnung', slider.value()))
        slider.keyReleaseEvent= lambda event: (self.slider_use_keyboard(env,config,'volume_fokuswarnung',event.key(),slider) ) 
        slider.actionTriggered.connect(lambda event: self.slider_action_triggered(env,config,'volume_fokuswarnung',event,slider))
        layout.addWidget(slider)
        
        label_volume = QLabel(str(slider.value()))
        label_volume.setFixedWidth(self.config_value_text_width)
        label_volume.setFixedHeight(self.config_value_text_height)
        label_volume.setAlignment(Qt.AlignCenter)
        self.set_config_bubble_stylesheet(label_volume)
        layout.addWidget(label_volume)

        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        widget.setLayout(layout)
        return widget

    def show_config_warnschwelle(self,env,config):
        widget = QWidget()
        widget.setFixedWidth(self.config_widget_width)
        widget.setFixedHeight(self.config_widget_height)
        self.set_config_widget_stylesheet(widget)

        layout = QHBoxLayout()

        label = QLabel('Warnschwelle')
        label.setFixedWidth(self.config_label_width) 
        label.setFixedHeight(self.config_label_height)
        self.set_label_stylesheet(label)
        layout.addWidget(label)
      

        slider = self.create_slider(self.config_slider_width,self.config_slider_height,0,100,config.warnschwelle)
        slider.valueChanged.connect(lambda: (config.set_warnschwelle(slider.value()), label_volume.setText(str(slider.value()))))
        slider.sliderReleased.connect(lambda: config.write_configfile('warnschwelle', slider.value()))
        slider.keyReleaseEvent= lambda event: (self.slider_use_keyboard(env,config,'warnschwelle',event.key(),slider) ) 
        slider.actionTriggered.connect(lambda event: self.slider_action_triggered(env,config,'warnschwelle',event,slider))
        layout.addWidget(slider)
        
        label_volume = QLabel(str(slider.value()))
        label_volume.setFixedWidth(self.config_value_text_width)
        label_volume.setFixedHeight(self.config_value_text_height)
        label_volume.setAlignment(Qt.AlignCenter)
        self.set_config_bubble_stylesheet(label_volume)
        layout.addWidget(label_volume)

        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        widget.setLayout(layout)
        return widget

    def slider_use_keyboard(self,env,config,config_name,event_key,slider,diff_value=0):
        value = slider.value() + diff_value

        height = slider.height()
        groove_height, handle_margin = self.calculate_slider_componets_size(height)
        slider.setStyleSheet(self.create_slider_style_sheet(groove_height,handle_margin,'pink','yellow','pink','pink'))

        if event_key in ['action_trigger',16777220,16777221]:
            slider.setStyleSheet(self.create_slider_style_sheet(groove_height,handle_margin,self.theme_color_config_slider_groove_background,self.theme_color_config_slider_handle_background,self.theme_color_config_slider_sub_page_background,self.theme_color_config_slider_add_page_background))
            env.event_check_fokus.set()
            config.write_configfile(config_name, value)

    def slider_action_triggered(self,env,config,config_name,event,slider):
        # slider.sliderPosition() liefert den Wert, der nach der Änderung eingestellt ist
        # Ist vielleicht besser als zu rechnen
        # print(f"slider.sliderPosition(): {slider.sliderPosition()}")
        if event == 3:
            diff_value = slider.pageStep()
        elif event == 4:
            diff_value = -slider.pageStep()
        if event in [3,4]:
            self.slider_use_keyboard(env,config,config_name,'action_trigger',slider,diff_value)

    def show_config_intervall(self,env,config):
        widget = QWidget()
        widget.setFixedWidth(self.config_widget_width)
        widget.setFixedHeight(self.config_widget_height)
        self.set_config_widget_stylesheet(widget)

        layout = QHBoxLayout()

        label = QLabel('Prüfintervall in Sekunden')
        label.setFixedWidth(self.config_label_width) 
        label.setFixedHeight(self.config_label_height)
        self.set_label_stylesheet(label)
        layout.addWidget(label)
      
        slider = self.create_slider(self.config_slider_width,self.config_slider_height,1,60,config.intervall)
        slider.valueChanged.connect(lambda: (config.set_intervall(slider.value()), label_volume.setText(str(slider.value()))))
        slider.sliderReleased.connect(lambda: (env.event_check_fokus.set(),config.write_configfile('intervall', slider.value())))
        slider.keyReleaseEvent= lambda event: (self.slider_use_keyboard(env,config,'intervall',event.key(),slider) ) 
        slider.actionTriggered.connect(lambda event: self.slider_action_triggered(env,config,'intervall',event,slider))
        
        layout.addWidget(slider)
        
        label_volume = QLabel(str(slider.value()))
        label_volume.setFixedWidth(self.config_value_text_width)
        label_volume.setFixedHeight(self.config_value_text_height)
        label_volume.setAlignment(Qt.AlignCenter)
        self.set_config_bubble_stylesheet(label_volume)
        layout.addWidget(label_volume)

        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        widget.setLayout(layout)
        return widget

    def show_config_debug(self,env,config):
        widget = QWidget()
        widget.setFixedWidth(self.config_widget_width)
        widget.setFixedHeight(self.config_widget_height)
        self.set_config_widget_stylesheet(widget)
        # widget.setStyleSheet(f'background-color: {self.theme_color_config_widget_background} ; border-radius: {self.config_widget_border_radius}px; border: 0px solid black')

        layout = QHBoxLayout()

        label = QLabel('Debug')
        label.setFixedWidth(self.config_label_width) 
        label.setFixedHeight(self.config_label_height)
        self.set_label_stylesheet(label)
        layout.addWidget(label)
      

        slider = self.create_slider(self.config_slider_width,self.config_slider_height,0,3,config.debug_level)
        slider.setPageStep(1)
        slider.valueChanged.connect(lambda: (config.set_debug_level(slider.value()), label_volume.setText(str(slider.value()))))
        slider.sliderReleased.connect(lambda: (config.write_configfile('debug_level', slider.value())))
        slider.keyReleaseEvent= lambda event: (self.slider_use_keyboard(env,config,'debug_level',event.key(),slider) ) 
        slider.actionTriggered.connect(lambda event: self.slider_action_triggered(env,config,'debug_level',event,slider))
        layout.addWidget(slider)
        
        label_volume = QLabel(str(slider.value()))
        label_volume.setFixedWidth(self.config_value_text_width)
        label_volume.setFixedHeight(self.config_value_text_height)
        label_volume.setAlignment(Qt.AlignCenter)
        self.set_config_bubble_stylesheet(label_volume)
        layout.addWidget(label_volume)

        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        widget.setLayout(layout)
        return widget
    def show_config_theme(self,env,config):
        widget = QWidget()
        widget.setFixedWidth(self.config_widget_width)
        widget.setFixedHeight(self.config_widget_height)
        self.set_config_widget_stylesheet(widget)

        layout = QHBoxLayout()

        label = QLabel('Theme')
        label.setFixedWidth(self.config_label_width) 
        label.setFixedHeight(self.config_label_height)
        self.set_label_stylesheet(label)
        layout.addWidget(label)

        combo_box = QComboBox()
        combo_box.setFixedWidth(self.config_slider_width)
        combo_box.setFixedHeight(int(self.config_slider_height*0.7))
        self.set_config_combo_box_stylesheet(combo_box)

        # Liste der Dateinamen ohne Endung
        theme_names = [os.path.splitext(file)[0] for file in os.listdir('themes') if file.endswith('.theme')]

        # Füge die Dateinamen zur ComboBox hinzu
        combo_box.addItems(theme_names)

        combo_box.setCurrentText(config.theme)
        combo_box.currentTextChanged.connect(lambda theme: (config.set_theme(theme),config.write_configfile('theme', theme),self.load_theme(env,config),self.gui_repaint(env,config)))
        layout.addWidget(combo_box)

        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        widget.setLayout(layout)
        return widget
    

    def fill_config_frame(self,env,config):
        config_frame = self.config_frame # noch auf self.config_frame umbauen
        # Erstelle Widget, Buttons und Regler
        widget_theme = self.show_config_theme(env,config)
        widget_volume_fokuswarnung = self.show_config_volume_fokuswarnung(env,config)
        widget_warnschwelle = self.show_config_warnschwelle(env,config)
        widget_intervall = self.show_config_intervall(env,config)
        widget_debug = self.show_config_debug(env,config)

        config_layout = QVBoxLayout()
        config_layout.addWidget(widget_theme)
        config_layout.addWidget(widget_volume_fokuswarnung)
        config_layout.addWidget(widget_warnschwelle)
        config_layout.addWidget(widget_intervall)
        config_layout.addWidget(widget_debug)
        config_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
        config_frame.setLayout(config_layout)
    
    def show_statusdisplay_fokus(self,env,config):
        widget = QWidget()
        widget.setFixedWidth(self.statusdisplay_widget_width)
        widget.setFixedHeight(self.statusdisplay_widget_height)
        self.set_config_widget_stylesheet(widget)

        layout = QHBoxLayout()

        label = QLabel('Fokus')
        label.setFixedWidth(self.statusdisplay_label_width) 
        label.setFixedHeight(self.statusdisplay_label_height)
        self.set_label_stylesheet(label)
        layout.addWidget(label)

        env.init_statusdisplay_fokus_progressbar()
        self.set_display_fokusbar_stylesheet(env)
        layout.addWidget(env.statusdisplay_fokus_progressbar)

        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        widget.setLayout(layout)
        return widget

    def fill_display_frame(self,env,config):
        layout = QVBoxLayout()
        # layout.addWidget(QLabel('Statusdisplay'))

        # Hier das Bild aus env.screen_fokus einfügen


        # debug 
        # debug_image = QLabel()
        # # pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
        # x1,y1 = 170, 80
        # x2,y2 = 450, 140
        # screenshot = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
        # qimage = QImage(screenshot.tobytes(), screenshot.width, screenshot.height, screenshot.width * 3, QImage.Format_RGB888)
        # qpixmap = QPixmap.fromImage(qimage)
        # debug_image.setPixmap(qpixmap)
        # layout.addWidget(debug_image)

        # env.init_statusdisplay_fokus_image()
        # layout.addWidget(env.statusdisplay_fokus_image)

        # env.init_statusdisplay_fokus_progressbar()
        # layout.addWidget(env.statusdisplay_fokus_progressbar)

        fokus_bar = self.show_statusdisplay_fokus(env,config)
        layout.addWidget(fokus_bar)

        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.display_frame.setLayout(layout)
        
    
    def fill_debug_frame(self,env,config,debug_frame):
        # QLabel für Debug-Meldungen erstellen und dem Debug-Frame hinzufügen
        debug_label = QLabel(debug_frame)
        debug_label.setGeometry(10, 10, 400, 100)  # Setze die Größe und Position des Labels
        debug_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)  # Text links oben ausrichten
        debug_label.setWordWrap(True)  # Zeilenumbruch aktivieren, falls der Text zu lang ist
        env.set_debug_label(debug_label)
        return debug_label

    def set_main_stylesheet(self):
        self.setStyleSheet(f"background-color: {self.theme_color_window_background};")

    def set_frame_config_stylesheet(self):
        self.config_frame.setStyleSheet(f'background-color: {self.theme_color_frame_config_background}')

    def set_frame_display_stylesheet(self):
        self.display_frame.setStyleSheet(f'background-color: {self.theme_color_frame_display_background}')
    
    def set_config_widget_stylesheet(self,widget):
        widget.setStyleSheet(f'background-color: {self.theme_color_config_widget_background} ; border-radius: {self.config_widget_border_radius}px; border: 0px solid black')
    
    def set_label_stylesheet(self,label):
        label.setStyleSheet(f'color: {self.theme_color_config_label_font}; font-size: 14px; border: 0px solid black; padding: 5px')

    def set_config_combo_box_stylesheet(self,combo_box):
        combo_box.setStyleSheet(f'background-color: {self.theme_color_config_combo_box_background} ; color: {self.theme_color_config_combo_box_font}; selection-background-color: {self.theme_color_config_combo_box_selection_background} ; selection-color:{self.theme_color_config_combo_box_selection_font} ; font-size: 12px; border: 1px solid {self.theme_color_config_combo_box_font}; padding: 5px; border-radius: 4px')
    
    def set_config_slider_stylesheet(self,slider):
        height = slider.height()
        groove_height, handle_margin = self.calculate_slider_componets_size(height)
        slider.setStyleSheet(self.create_slider_style_sheet(groove_height,handle_margin,self.theme_color_config_slider_groove_background,self.theme_color_config_slider_handle_background,self.theme_color_config_slider_sub_page_background,self.theme_color_config_slider_add_page_background))

    def set_config_bubble_stylesheet(self,bubble):
        max_radius = self.get_max_radius(bubble.sizeHint().width() , bubble.sizeHint().height())
        bubble.setStyleSheet(f'background-color: {self.theme_color_config_bubble_background} ; color: {self.theme_color_config_bubble_font}; font-size: 14px; border: {self.theme_config_bubble_border}; padding: 5px; border-radius: {max_radius}px')

    def set_display_fokusbar_stylesheet(self,env):
        env.statusdisplay_fokus_progressbar.setStyleSheet(f'QProgressBar {{background-color: {self.theme_color_display_fokusbar_background}; color: {self.theme_color_display_fokusbar_font}; text-align: {self.theme_align_display_fokusbar_text_align}; }}\
                                                            QProgressBar::chunk {{background-color: {self.theme_color_display_fokusbar_chunk_background}; border: {self.theme_display_fokusbar_chunk_border}; border-radius: {self.theme_display_fokusbar_chunk_border_radius} }}\
                                                            ')

    def initUI(self,env,config):
        self.setWindowTitle('Fokus Check')
        self.setGeometry(500, 100, 800, 400)
        self.set_main_stylesheet() 

        # Frames erstellen
        self.create_config_frame()
        self.create_display_frame()
        # button_frame = self.create_button_frame()
        # debug_frame = self.create_debug_frame()

        # Frames befüllen 
        self.fill_config_frame(env,config)
        self.fill_display_frame(env,config)
        # self.fill_debug_frame(env,config,debug_frame)


        # Layouts erstellen
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.config_frame,1)
        left_layout.addWidget(self.display_frame,1)
        # left_layout.addWidget(button_frame,1)
        left_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        right_layout = QVBoxLayout()
        # right_layout.addWidget(debug_frame,1)

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)

        # Widget erstellen
        widget = QWidget()
        widget.setLayout(main_layout)

        self.setCentralWidget(widget)

def set_volume(sound, volume):
    vol = int(volume) / 100
    sound.set_volume(vol)

def gui(env,config):
    app = QApplication([])
    main_window = MainWindow(env,config)
    main_window.setFixedSize(main_window.window_width, main_window.window_height)
    main_window.show()
    app.exec_()
    env.set_running(False)
    env.event_check_fokus.set()

def main():
    config = myconfig('fokus.conf')
    env = environment()

    # Pygame für Soundausgaben initialisieren
    pygame.init()
    pygame.mixer.init()
    mp3_Fokuswarnung = pygame.mixer.Sound(config.mp3_fokuswarnung)
    env.set_mp3_Fokuswarnung(mp3_Fokuswarnung)
    set_volume(env.mp3_Fokuswarnung, config.volume_fokuswarnung)

    # Starte den Thread für die Fokusüberprüfung
    thread_fokus_check = threading.Thread(target=fokus_check, args=(env,config,))    
    env.threads.append(thread_fokus_check)
    thread_fokus_check.start()

    # Starte die GUI
    gui(env,config)

    # Warte, bis alle Threads beendet sind
    for thread in env.threads:
        thread.join()


if __name__ == "__main__":
    main()
