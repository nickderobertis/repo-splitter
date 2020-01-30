import PySimpleGUI as sg
import webbrowser

layout = [
          [sg.Text('http://www.google.com', click_submits=True, text_color='blue')],
          [sg.Text('This text is clickable with a key', click_submits=True, key='Text Key')],
          [sg.Text('This text is not clickable')],
          [sg.ReadButton('Button that does nothing')]
         ]

form = sg.FlexForm('Demo of clickable Text Elements').Layout(layout)

while True:
    button, values = form.Read()
    if button is None: break
    webbrowser.open(button)
    print(button, values)