import socket
import logging
import threading
import sys
import queue
from screen import Screen
from comms import receive, Msg

logging.basicConfig(level=logging.WARNING)


class Client():
    def __init__(self):
        self.screen = Screen(self, self)
        self.server_address = ('81.229.8.57', 26000)

        # Create a TCP/IP socket
        self.sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        logging.debug('connecting to %s port %s', self.server_address[0],
                      self.server_address[1])
        self.sckt.connect(self.server_address)

        self.name = self.welcome()
        maze = self.join()
        self.screen.start_game(maze)

        self.screen.chat.set_prompt(self.name + "> ")

        self.bucket = queue.Queue()

        self.stop_threads = False
        stop = lambda : self.stop_threads

        chatter = Chatterer(self.bucket, self.name, self.screen,
                            self.sckt, stop)
        # chatter.run()

        input_listener = Inputter(self.bucket, self.name,
                                  self.screen, self.sckt, stop)
        input_listener.start()

        listener = Listener(self.bucket, self.name, self.screen,
                            self.sckt, stop)
        listener.start()

        self.screen.refresh()
        self.threads = [input_listener, listener]
        self.mainloop()

    def welcome(self):
        """display a welcome splash screen"""
        name = self.screen.welcome()
        self.screen.clear()
        return name

    def join(self):
        """Send a join request to the server, and recieve the maze"""
        msg = Msg(b'j', self.name)
        msg.send(self.sckt)
        msg_type, msg = receive(self.sckt)
        if msg_type == b'w':
            return msg
        if (msg_type == b's') and (msg == "T"):
            self.name = self.welcome()
            return self.join()  # Try again. TODO: add new name prompt
        self.screen.print_debug("failed to join, no maze received\nInstead"
                                " received type " + str(msg_type)
                                + " with data " + str(msg))
        return None  # Connection refused, assume name taken

    def mainloop(self):
        exc = None
        win = False
        while not win:
            try:
                exc = self.bucket.get(block=False)
            except queue.Empty:
                pass

            for thread in self.threads:
                thread.join(0.1)
                if thread.is_alive():
                    continue
                win = True
                break
            if exc is not None:
                break

        if exc is not None:
            self.screen.print_exc(exc)
        elif win:
            self.stop_threads = True
            self.screen.win()


class Client_thread(threading.Thread):
    def __init__(self, bucket, name, screen, sckt, stop):
        threading.Thread.__init__(self)
        self.bucket = bucket
        self.name = name
        self.screen = screen
        self.sckt = sckt
        self.stop = stop
        self.setDaemon(True)

    def run(self):
        try:
            self.mainloop()
        except Exception:
            self.bucket.put(sys.exc_info())

    def mainloop(self):
        """The looped thread action"""


class Chatterer(Client_thread):
    def __init__(self, bucket, name, screen, sckt, stop):
        Client_thread.__init__(self, bucket, name, screen, sckt, stop)

    def mainloop(self):
        """wait for input on the chat window, and send message"""
        while True:
            msg = self.name + "> " + self.screen.chat.getinp()
            msg = Msg(b'M', msg)
            # Send messages on socket
            msg.send(self.sckt)
            if self.stop():
                break


class Listener(Client_thread):
    def __init__(self, bucket, name, screen, sckt, stop):
        Client_thread.__init__(self, bucket, name, screen, sckt, stop)

    def mainloop(self):
        """Listen for incoming commands from the server"""
        while True:
            try:
                msg_type, data = receive(self.sckt)
            except ConnectionResetError:  # Server closed
                logging.info('closing %s after reading no data',
                             self.sckt.getpeername())
                self.sckt.close()
                break
            logging.debug('%s: received "%s"', self.sckt.getsockname(), data)
            if msg_type == b'M':
                self.screen.chat.print_line(data)
            elif msg_type == b'n':  # new player joined
                self.screen.game.game.add_player(data[0], data[1], data[2])
                self.screen.refresh()
            elif msg_type == b'm':  # move a player
                self.screen.game.game.move(data[0], int(data[1]))
                self.screen.refresh()
            elif msg_type == b'd':  # delete a player
                self.screen.game.game.delete_player(data)
                self.screen.refresh()
            elif msg_type == b'k':
                self.screen.game.game.toggle_key(data[0], data[1])
                self.screen.refresh()
            elif msg_type == b's':
                if data == "I":  # illegal move
                    pass
                if data == "W":
                    break
            if self.stop():
                break

class Inputter(Client_thread):
    def __init__(self, bucket, name, screen, sckt, stop):
        Client_thread.__init__(self, bucket, name, screen, sckt, stop)

    def mainloop(self):
        while True:
            direction = self.screen.getdir()
            if direction is None:
                continue
            self.move_req(direction)
            if self.stop():
                break

    def move_req(self, direction):
        msg = Msg(b'm', self.name, direction)
        msg.send(self.sckt)


if __name__ == "__main__":
    sys.setrecursionlimit(10000)
    client = Client()
