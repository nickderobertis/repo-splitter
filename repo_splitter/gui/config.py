# Prefer qt if it is installed, otherwise default to tkinter
try:
    import PySimpleGUIQt as sg
except ImportError:
    import PySimpleGUI as sg
THEME = 'Material1'