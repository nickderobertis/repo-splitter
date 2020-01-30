import queue
import sys
import threading
from dataclasses import dataclass
from traceback import TracebackException
from typing import Callable, Optional, Any

from repo_splitter.gui.config import sg
from repo_splitter.gui.error import error_window


@dataclass
class Result:
    value: Optional[Any] = None
    exception: Optional[TracebackException] = None

    @property
    def empty(self) -> bool:
        return self.value is None and self.exception is None


def run_put_result_in_queue(func: Callable, gui_queue: queue.Queue, *args, **kwargs):
    """
    A worker thread that communicates with the GUI through a queue
    This thread can block for as long as it wants and the GUI will not be affected
    :param func: Function to run
    :param gui_queue: (queue.Queue) Queue to communicate back to GUI that task is completed
    :return:
    """
    try:
        value = func(*args, **kwargs)
        result = Result(value=value)
        gui_queue.put(result)  # put a message into queue for GUI
    except Exception as e:
        te = TracebackException.from_exception(e)
        result = Result(exception=te)
        gui_queue.put(result)
        raise e


def loading_gui(func: Callable, message: str, *args, **kwargs):
    """

    :param func: Function to run while loading
    :param message: Message to display while loading
    :param args: args to pass to func
    :param func_kwargs: kwargs to pass to func
    """

    gui_queue = queue.Queue()  # queue used to communicate between the gui and the threads

    layout = [[sg.Text(message)],
              [sg.Button('Cancel')] ]

    window = sg.Window('Loading...', layout)

    # --------------------- EVENT LOOP ---------------------
    started_process = False
    result = Result()
    while True:
        event, values = window.Read(timeout=100)       # wait for up to 100 ms for a GUI event
        if event is None or event == 'Cancel':
            break
        if not started_process:
            threading.Thread(
                target=run_put_result_in_queue,
                args=(func, gui_queue, *args),
                kwargs=kwargs,
                daemon=True
            ).start()
            started_process = True
        # --------------- Check for incoming messages from threads  ---------------
        try:
            result = gui_queue.get_nowait()
        except queue.Empty:             # get_nowait() will get exception when Queue is empty
            result = Result()              # break from the loop if no more messages are queued up

        # if result received from queue, display the result in the Window
        if not result.empty:
            break

    # if user exits the window, then close the window and exit the GUI func
    window.Close()

    if result.empty:
        # User must have canceled as no result was ever returned
        exit(0)

    if result.exception is not None:
        # Got an exception. Show it to the user.
        error_window(result.exception)
        exit(1)

    return result.value




if __name__ == '__main__':
    import time

    num_secs = 5

    def sleep_with_fail(fail: bool = False):
        if fail:
            raise ValueError('yo boy')

        time.sleep(num_secs)

    res = loading_gui(
        sleep_with_fail,
        f'Sleeping for {num_secs}',
        True
    )

    print(f'result: {res}')
