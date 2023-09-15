#!/usr/bin/env python3
# Exe erzeugen mit pyinstaller --onefile --noconsole Fokus_check.pyw
# import time
import pyautogui
# from collections import defaultdict
import pygame
# from PIL import Image
import threading
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QMainWindow, QFrame, QSpacerItem, QSizePolicy, QHBoxLayout, QSlider
from PyQt5.QtCore import Qt
from PyQt5 import QtGui


class environment:
    def __init__(self):
        self.running = True
        self.gewarnt = False
        self.threads = []
        self.event_check_fokus = threading.Event()
    
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
        self.warnschwelle = 33
        self.intervall = 10
        self.mp3_fokuswarnung = 'Fokuswarnung.mp3'
        self.volume_fokuswarnung = 100

    def set_debug(self,debug):
        self.debug = debug

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
                    elif line.startswith('warnschwelle ='):
                        self.warnschwelle = int(line.split('=')[1].split('#')[0].strip())
                    elif line.startswith('intervall ='):
                        self.intervall = int(line.split('=')[1].split('#')[0].strip())
                    elif line.startswith('mp3_fokuswarung ='):
                        self.mp3_fokuswarnung = line.split('=')[1].split('#')[0].strip()
                    elif line.startswith('volume_fokuswarnung'):
                        self.volume_fokuswarnung = int(line.split('=')[1].split('#')[0].strip())

        except FileNotFoundError:
            print("Die Datei wurde nicht gefunden.")
        except PermissionError:
            print("Du hast keine Berechtigung, die Datei zu lesen.")
        except Exception as e:
            print("Ein unbekannter Fehler ist aufgetreten:", str(e))

    def write_configfile(self,config_name,value):
        print("debug schreibe file")
        found = False
        content= []
        if config_name == 'debug':
            value = bool(value)
        try:
            with open(self.config_file, 'r') as file:
                for line in file:
                    if line.startswith(config_name):
                        found = True
                        comment = line.split('#', 1)[-1].strip()
                        new_line = f'{config_name} = {value} # {comment}\n'
                        content.append(new_line)
                    else:
                        line = line.rstrip('\n') # remove newline
                        line += '\n' # add newline
                        content.append(line)
                if found == False:
                    new_line = f'{config_name} = {value} # \n'
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


def count_pixels(config):
    # Erfasse den Bildschirmbereich
    # screenshot = pyautogui.screenshot(region=(config.x1, config.y1, config.x2 - config.x1, config.y2 - config.y1))
    screenshot = get_screenshot(config.x1, config.y1, config.x2, config.y2)
    # Initialisiere den Zähler für Pixel
    fokus_voll_pixel_count = 0
    fokus_leer_pixel_count = 0
    # if config.debug == True:
    #     color_counts = defaultdict(int)

    # Durchlaufe die Pixel im erfassten Bereich
    for x in range(config.x2 - config.x1):
        for y in range(config.y2 - config.y1):
            pixel_color = screenshot.getpixel((x, y))
            if config.debug == True:
                print(f"Pixel {x} {y} Farb:{pixel_color}")
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
    if config.debug == True:
        print(f"Fokus sichtbar: {fokus_sichtbar:.0f}%")
        # env.update_debug_label(f"Fokus sichtbar: {fokus_sichtbar:.0f}%")
    return fokus_sichtbar

"""
Code Snippings für Debugging
        # Gib die Anzahl der verschiedenen Farben aus
        # if debug == True:
        #     for color, count in color_counts.items():
        #         print(f"Farbe {color}: {count} Pixel")
        # Screenshot anzeigen
        # if config.debug == True:
        #     screenshot.show()


"""

def sound_play(sound):
    sound.play()

def get_screenshot(x1,y1,x2,y2):
    screenshot = pyautogui.screenshot(region=(x1, y1, x2 - x1, y2 - y1))
    return screenshot

def check_fokus(env,config):
    fokus_voll,fokus_leer = count_pixels(config)
    fokus_sichtbar = get_fokus_sichtbar(env,config,fokus_leer,fokus_voll)
    if fokus_sichtbar > 70:
            prozent_voll = fokus_voll / (fokus_voll + fokus_leer) * 100
            if prozent_voll < config.warnschwelle:
                print("Fokuswarnung")
                if env.gewarnt == False:
                    env.set_gewarnt(True)
                    sound_play(env.mp3_Fokuswarnung)
            else:
                if env.gewarnt == True:
                    env.set_gewarnt(False)
            if config.debug == True:
                print(f"Fokus Pixel Voll: {fokus_voll}")
                print(f"Fokus Pixel Leer: {fokus_leer}")
            print(f"Prozentualer Fokus: {prozent_voll:.0f}%")
    else:
        print("Fokus nicht sichtbar")

def fokus_check(env,config):

    while env.running == True:
        check_fokus(env,config)
        env.event_check_fokus.wait(config.intervall)
        env.event_check_fokus.clear()

def gui_sound_test(env):
    sound_play(env.mp3_Fokuswarnung)


class MainWindow(QMainWindow):
    def __init__(self,env,config):
        super().__init__()
        self.config_color_background = '#C2C2C2'
        self.config_color_font = 'black'
        self.config_frame_width = 560
        self.config_frame_height = 278 # 
        self.config_widget_width = 540
        self.config_widget_height = 60
        self.config_widget_border_radius = 10
        self.config_label_width = 270
        self.config_label_height = 40
        self.config_slider_width = 200
        self.config_slider_height = 40
        self.config_slider_groove_color_background = 'white'
        self.config_slider_handle_color_background = '#3399ff'
        self.config_slider_add_page_color_background = 'white'
        self.config_slider_sub_page_color_background = '#3399ff'

        self.config_button_width = 50
        self.config_value_text_width = 40
        self.config_value_text_height = 30
        

        self.initUI(env,config)

    def create_config_frame(self):
        config_frame = QFrame(self)
        config_frame.setFrameShape(QFrame.StyledPanel)
        config_frame.setFixedSize(self.config_frame_width , self.config_frame_height) 
        config_frame.setStyleSheet('background-color: yellow')
        return config_frame
    
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
    
    def create_style_sheet(self,groove_height,handle_margin,groove_color_background,handle_color_background,sub_page_color_background,add_page_color_background):
        style_sheet = f'QSlider::groove:horizontal   {{ border: 1px solid black; background: {groove_color_background}  ;border-radius: 4px; height: {groove_height}px; margin: 0px 0; }} \
                        QSlider::handle:horizontal   {{ border: 1px solid black; background: {handle_color_background}  ;border-radius: 4px; width: 10px; margin: {handle_margin}px 0; }} \
                        QSlider::sub-page:horizontal {{ border: 1px solid black; background: {sub_page_color_background};border-radius: 4px; }} \
                        QSlider::add-page:horizontal {{ border: 1px solid black; background: {add_page_color_background};border-radius: 4px; }} \
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
        slider.setStyleSheet(self.create_style_sheet(groove_height,handle_margin,self.config_slider_groove_color_background,self.config_slider_handle_color_background,self.config_slider_sub_page_color_background,self.config_slider_add_page_color_background))
        slider.setRange(min, max)
        slider.setValue(value)
        return slider


    def show_config_volume_fokuswarnung(self,env,config):
        widget = QWidget()
        widget.setFixedWidth(self.config_widget_width)
        widget.setFixedHeight(self.config_widget_height)
        widget.setStyleSheet(f'background-color: {self.config_color_background} ; border-radius: {self.config_widget_border_radius}px; border: 0px solid black')

        layout = QHBoxLayout()

        label = QLabel('Warnlautstärke')
        label.setFixedWidth(self.config_label_width-self.config_button_width-5-1) # -5 wegen padding -1 wegen weiß noch nicht warum
        label.setFixedHeight(self.config_label_height)
        label.setStyleSheet(f'color: {self.config_color_font}; font-size: 14px; border: 0px solid black; padding: 5px')
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
        max_radius = self.get_max_radius(label_volume.sizeHint().width() , label_volume.sizeHint().height())
        label_volume.setStyleSheet(f'background-color: white ; color: black; font-size: 14px; border: 1px solid black; padding: 5px; border-radius: {max_radius}px')
        layout.addWidget(label_volume)

        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        widget.setLayout(layout)
        return widget

    def show_config_warnschwelle(self,env,config):
        widget = QWidget()
        widget.setFixedWidth(self.config_widget_width)
        widget.setFixedHeight(self.config_widget_height)
        widget.setStyleSheet(f'background-color: {self.config_color_background} ; border-radius: {self.config_widget_border_radius}px; border: 0px solid black')

        layout = QHBoxLayout()

        label = QLabel('Warnschwelle')
        label.setFixedWidth(self.config_label_width) 
        label.setFixedHeight(self.config_label_height)
        label.setStyleSheet(f'color: {self.config_color_font}; font-size: 14px; border: 0px solid black; padding: 5px')
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
        max_radius = self.get_max_radius(label_volume.sizeHint().width() , label_volume.sizeHint().height())
        label_volume.setStyleSheet(f'background-color: white ; color: black; font-size: 14px; border: 1px solid black; padding: 5px; border-radius: {max_radius}px')
        layout.addWidget(label_volume)

        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        widget.setLayout(layout)
        return widget

    def slider_use_keyboard(self,env,config,config_name,event_key,slider,diff_value=0):
        value = slider.value() + diff_value

        height = slider.height()
        groove_height, handle_margin = self.calculate_slider_componets_size(height)
        slider.setStyleSheet(self.create_style_sheet(groove_height,handle_margin,'pink','yellow','pink','pink'))

        if event_key in ['action_trigger',16777220,16777221]:
            slider.setStyleSheet(self.create_style_sheet(groove_height,handle_margin,self.config_slider_groove_color_background,self.config_slider_handle_color_background,self.config_slider_sub_page_color_background,self.config_slider_add_page_color_background))
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
        widget.setStyleSheet(f'background-color: {self.config_color_background} ; border-radius: {self.config_widget_border_radius}px; border: 0px solid black')

        layout = QHBoxLayout()

        label = QLabel('Prüfintervall in Sekunden')
        label.setFixedWidth(self.config_label_width) 
        label.setFixedHeight(self.config_label_height)
        label.setStyleSheet(f'color: {self.config_color_font}; font-size: 14px; border: 0px solid black; padding: 5px')
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
        max_radius = self.get_max_radius(label_volume.sizeHint().width() , label_volume.sizeHint().height())
        label_volume.setStyleSheet(f'background-color: white ; color: black; font-size: 14px; border: 1px solid black; padding: 5px; border-radius: {max_radius}px')
        layout.addWidget(label_volume)

        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        widget.setLayout(layout)
        return widget

    def show_config_debug(self,env,config):
        widget = QWidget()
        widget.setFixedWidth(self.config_widget_width)
        widget.setFixedHeight(self.config_widget_height)
        widget.setStyleSheet(f'background-color: {self.config_color_background} ; border-radius: {self.config_widget_border_radius}px; border: 0px solid black')

        layout = QHBoxLayout()

        label = QLabel('Debug')
        label.setFixedWidth(self.config_label_width) 
        label.setFixedHeight(self.config_label_height)
        label.setStyleSheet(f'color: {self.config_color_font}; font-size: 14px; border: 0px solid black; padding: 5px')
        layout.addWidget(label)
      

        slider = self.create_slider(self.config_slider_width,self.config_slider_height,0,1,config.debug)
        slider.setPageStep(1)
        slider.valueChanged.connect(lambda: (config.set_debug(slider.value()), label_volume.setText(str(slider.value()))))
        slider.sliderReleased.connect(lambda: (config.write_configfile('debug', slider.value())))
        slider.keyReleaseEvent= lambda event: (self.slider_use_keyboard(env,config,'debug',event.key(),slider) ) 
        slider.actionTriggered.connect(lambda event: self.slider_action_triggered(env,config,'debug',event,slider))
        layout.addWidget(slider)
        
        label_volume = QLabel(str(slider.value()))
        label_volume.setFixedWidth(self.config_value_text_width)
        label_volume.setFixedHeight(self.config_value_text_height)
        label_volume.setAlignment(Qt.AlignCenter)
        max_radius = self.get_max_radius(label_volume.sizeHint().width() , label_volume.sizeHint().height())
        label_volume.setStyleSheet(f'background-color: white ; color: black; font-size: 14px; border: 1px solid black; padding: 5px; border-radius: {max_radius}px')
        layout.addWidget(label_volume)

        layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        widget.setLayout(layout)
        return widget
    
    def fill_config_frame(self,env,config,config_frame):
        # Erstelle Widget, Buttons und Regler
        widget_volume_fokuswarnung = self.show_config_volume_fokuswarnung(env,config)
        widget_warnschwelle = self.show_config_warnschwelle(env,config)
        widget_intervall = self.show_config_intervall(env,config)
        widget_debug = self.show_config_debug(env,config)

        config_layout = QVBoxLayout()
        config_layout.addWidget(widget_volume_fokuswarnung)
        config_layout.addWidget(widget_warnschwelle)
        config_layout.addWidget(widget_intervall)
        config_layout.addWidget(widget_debug)
        config_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
        config_frame.setLayout(config_layout)
    
    def fill_debug_frame(self,env,config,debug_frame):
        # QLabel für Debug-Meldungen erstellen und dem Debug-Frame hinzufügen
        debug_label = QLabel(debug_frame)
        debug_label.setGeometry(10, 10, 400, 100)  # Setze die Größe und Position des Labels
        debug_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)  # Text links oben ausrichten
        debug_label.setWordWrap(True)  # Zeilenumbruch aktivieren, falls der Text zu lang ist
        env.set_debug_label(debug_label)
        return debug_label


    def initUI(self,env,config):
        self.setWindowTitle('Fokus Check')
        self.setGeometry(100, 100, 800, 400)

        # Frames erstellen
        config_frame = self.create_config_frame()
        # button_frame = self.create_button_frame()
        # debug_frame = self.create_debug_frame()

        # Frames befüllen 
        self.fill_config_frame(env,config,config_frame)
        # self.fill_debug_frame(env,config,debug_frame)


        # Layouts erstellen
        left_layout = QVBoxLayout()
        left_layout.addWidget(config_frame,1)
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
    main_window.setFixedSize(580, 300)
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
