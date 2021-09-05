"""
The server module owns and runs a server for comunicating between clients

Authors: Tomass Wilson
"""
import socket
import select
import logging
import queue
import sys
from game_logic import Game
from comms import receive, Msg


class Server():
    """An object that runs a server"""

    def __init__(self):
        self.sckt = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sckt.setblocking(0)
        self.port = 26000
        address = ('', self.port)
        self.sckt.bind(address)
        logging.info('starting up on %s port %s',
                     self.sckt.getsockname(), self.port)

        self.inputs = [self.sckt]
        self.clients_to_send = []

        self.client_queues = {}
        self.client_names = {}
        self.game = Game()
        self.game.genboard()
        self.win = False

    def listen(self):
        """Read status of all open sockets"""
        self.sckt.listen(5)
        while self.inputs:
            readable, writable, exceptional = \
                select.select(self.inputs, self.clients_to_send, self.inputs)

            self.read(readable)
            self.write(writable)
            self.handle_exceptional(exceptional)
            if self.win and (len(self.clients_to_send) == 0):
                break

    def read(self, readable):
        """Read all incoming messages"""
        for sckt in readable:
            if sckt is self.sckt:
                (csocket, address) = self.sckt.accept()
                logging.info('new connection from %s', address)
                csocket.setblocking(0)
                self.inputs.append(csocket)
                self.client_queues[csocket] = queue.Queue()
            else:
                try:
                    msg_type, data = receive(sckt)
                except ConnectionResetError:  # Player left
                    logging.info('closing %s after reading no data',
                                 sckt.getpeername())

                    name = self.client_names[sckt]
                    self.game.delete_player(name)
                    msg = Msg(b'd', name)
                    self.send_all(msg)

                    if sckt in self.clients_to_send:
                        self.clients_to_send.remove(sckt)
                    self.inputs.remove(sckt)
                    del self.client_queues[sckt]
                    del self.client_names[sckt]
                    sckt.close()
                    continue

                if msg_type == b'j':
                    self.add_player(sckt, data)

                elif msg_type == b'm':
                    self.move(sckt, int(data[1]))  # send only move direction

                elif msg_type == b'a':
                    logging.info('received interact request '
                                 'from %s', sckt.getpeername())
                    if self.game.interact(self.client_names[sckt], data):
                        None

                elif msg_type == b'M':  # Broadcast message to all players
                    logging.info('received message from '
                                 '"%s", broadcasting', sckt.getpeername())
                    msg = Msg(b'M', data)
                    self.send_all(msg, sckt)

    def add_player(self, sckt, name):
        """send a player join request to all clients"""
        logging.info('received join request with name '
                     '"%s" from %s', name, sckt.getpeername())

        if name not in self.client_names.values():
            self.client_names[sckt] = name
            msg = Msg(b'w', self.game.mazestr())
            self.client_queues[sckt].put(msg)
            pos = self.game.new_player(name)
            y, x = pos
            pos = y.to_bytes(1, byteorder='big') + x.to_bytes(1, byteorder='big')

            msg = Msg(b'n', name, pos)
            self.send_all(msg, sckt)
            self.send_players_and_keys(sckt)

        else:
            msg = Msg(b's', "T")  # name taken
            self.client_queues[sckt].put(msg)

        if sckt not in self.clients_to_send:
            self.clients_to_send.append(sckt)

        if len(self.game.players) == 2:
            upd = self.game.spawn_keys()
            if upd:
                self.send_keys()

    def move(self, sckt, direction):
        logging.info('received move request '
                     'from %s', sckt.getpeername())
        if self.game.move(self.client_names[sckt], direction):
            msg = Msg(b'm', self.client_names[sckt], direction)
            self.send_all(msg)
            key_rem = self.game.check_key(self.client_names[sckt])
            if key_rem is not None:
                y, x = key_rem
                pos = y.to_bytes(1, byteorder='big') + x.to_bytes(1, byteorder='big')
                msg = Msg(b'k', pos)
                self.send_all(msg)
                if self.game.is_win():
                    self.send_win()
        else:
            msg = Msg(b's', "I")
            self.client_queues[sckt].put(msg)
            if sckt not in self.clients_to_send:
                self.clients_to_send.append(sckt)

    def send_all(self, msg, excl=None):
        """send a message to every client, excluding excl socket"""
        for key in self.client_queues:
            if (excl is not None) and (key == excl):
                continue
            self.client_queues[key].put(msg)
            if key not in self.clients_to_send:
                self.clients_to_send.append(key)

    def send_players_and_keys(self, sckt):
        """send all players and keys on board to a single client"""
        for player_name in self.game.players:
            player = self.game.players[player_name]
            y, x = player.pos
            pos = y.to_bytes(1, byteorder='big') + x.to_bytes(1, byteorder='big')
            msg = Msg(b'n', player_name, pos)
            self.client_queues[sckt].put(msg)
        for key in self.game.keys:
            y, x = key.pos
            pos = y.to_bytes(1, byteorder='big') + x.to_bytes(1, byteorder='big')
            msg = Msg(b'k', pos)
            self.client_queues[sckt].put(msg)

    def send_keys(self):
        """send newly spawned keys to all players"""
        for key in self.game.keys:
            y, x = key.pos
            pos = y.to_bytes(1, byteorder='big') + x.to_bytes(1, byteorder='big')
            msg = Msg(b'k', pos)
            self.send_all(msg)

    def send_win(self):
        msg = Msg(b's', "W")
        self.send_all(msg)
        is_done_sending = False

        self.win = True

    def write(self, writable):
        """write to all sockets that have queued messages"""
        for sckt in writable:
            try:
                next_msg = self.client_queues[sckt].get_nowait()
            except queue.Empty:
                # No messages waiting so stop checking for writability.
                self.clients_to_send.remove(sckt)
            else:
                next_msg.send(sckt)

    def handle_exceptional(self, exceptional):
        """Handle "exceptional conditions"""
        for sckt in exceptional:
            logging.warning('handling exceptional condition for %s',
                            sckt.getpeername())
            # Stop listening for input on the connection
            self.inputs.remove(sckt)
            if sckt in self.clients_to_send:
                self.clients_to_send.remove(sckt)
            sckt.close()

            # Remove message queue
            del self.client_queues[sckt]


if __name__ == "__main__":
    sys.setrecursionlimit(10000)
    logging.basicConfig(level=logging.INFO)
    SERVER = Server()
    SERVER.listen()
    print("The players have won!")
