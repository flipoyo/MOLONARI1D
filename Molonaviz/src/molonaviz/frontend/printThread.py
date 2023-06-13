
from PyQt5.QtCore import QObject, pyqtSignal
from queue import Queue #Used only for type hints


class InterceptOutput:
    """
    The goal of this class is to intercept sys.stdout and put in in a queue: instead of displaying a message in the terminal, it will be put in a queue.
    """
    def __init__(self, queue : Queue):
        self.queue = queue

    def write(self, text : str):
        """
        Method called when trying to print something. This is an overloaded function.
        """
        self.queue.put(text)

    def flush(self):
        """
        This function is necessary so no error occurs: however, it can be empty. See this Stack Overflow (https://stackoverflow.com/questions/20525587/python-logging-in-multiprocessing-attributeerror-logger-object-has-no-attrib) for more information.
        """
        pass

class Receiver(QObject):
    """
    A QObject meant to run in its own QThread that waits for data to be pushed in its queue. When it has something in the queue, send it to the Main Thread by emitting a custom signal.
    """
    printMessage = pyqtSignal(str)

    def __init__(self, queue : Queue):
        QObject.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            text = self.queue.get()
            self.printMessage.emit(text)
