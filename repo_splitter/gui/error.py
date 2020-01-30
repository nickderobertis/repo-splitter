from traceback import TracebackException

from repo_splitter.gui.config import sg


def error_window(exc: TracebackException):
    message = ''.join(exc.format())

    layout = [
        [sg.Text(message)],
        [sg.Button('Ok')]
    ]

    window = sg.Window('Error', layout)

    # --------------------- EVENT LOOP ---------------------
    while True:
        event, values = window.Read(timeout=100)  # wait for up to 100 ms for a GUI event
        if event is None or event == 'Ok':
            break

    # if user exits the window, then close the window and exit the GUI func
    window.Close()
