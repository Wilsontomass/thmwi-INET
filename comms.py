"""
The comms module contains functions that allow receiving based on
the wilson protokoll.

Authors: Tomass Wilson
"""
import logging


class Msg():
    def __init__(self, msg_type, msg, msg_2 = None):
        self.msg_type = msg_type
        self.msg = msg
        self.msg_2 = msg_2

    def send(self, sckt):
        """
        Send the message. Will block until message sent

        args:
            sckt: The socket to send on
        """
        msg = self.msg
        logging.debug('%s: sending "%s"', sckt.getsockname(), msg)
        _send_message(sckt, self.msg_type)
        if self.msg_type in (b'j', b'M', b'd'):  # utf-8 message
            msg = msg.encode("utf-8")
            _send_message(sckt, len(msg).to_bytes(1, byteorder='big'))
        elif self.msg_type in (b'm', b'a'):  # Two part message
            msg = msg.encode("utf-8")
            _send_message(sckt, len(msg).to_bytes(1, byteorder='big'))
            _send_message(sckt, msg)
            msg = str(self.msg_2).encode("ascii")
        elif self.msg_type == b'n':
            msg = msg.encode("utf-8")
            _send_message(sckt, len(msg).to_bytes(1, byteorder='big'))
            _send_message(sckt, msg)
            msg = self.msg_2  # preencoded coordinates
        elif self.msg_type == b'k':
            msg = msg  # preencoded coordinates
        else:  # simple ascii message
            msg = msg.encode("ascii")
        _send_message(sckt, msg)


def receive(sckt):
    """
    Recieve a request/message from another party

    args:
        sckt: The socket on which to receive

    returns:
        msg_type: The type of the message
        msg: The message in the form of a string.
    """
    # get type
    msg_type = _receive_type(sckt)
    not_blck = sckt.gettimeout() == 0
    sckt.setblocking(1)

    if msg_type in (b'j', b'M', b'd'):  # Read a utf-8 message
        msg_bytes = _receive_type(sckt)  # names can be up to 255 bytes long
        msg_bytes = int.from_bytes(msg_bytes, byteorder='big')
        msg = _receive_message(sckt, msg_bytes).decode("utf-8")

    elif msg_type == b's':  # Move/action request, status msg
        msg = _receive_message(sckt, 1).decode("ascii")

    elif msg_type in (b'm', b'a'):  # receive named action/move
        msg_bytes = _receive_type(sckt)
        msg_bytes = int.from_bytes(msg_bytes, byteorder='big')
        name = _receive_message(sckt, msg_bytes).decode("utf-8")
        msg = _receive_message(sckt, 1).decode("ascii")
        msg = [name, msg]  # two part message

    elif msg_type == b'n':  # new player message
        msg_bytes = _receive_type(sckt)
        msg_bytes = int.from_bytes(msg_bytes, byteorder='big')
        name = _receive_message(sckt, msg_bytes).decode("utf-8")
        y = int.from_bytes(_receive_message(sckt, 1), byteorder='big')
        x = int.from_bytes(_receive_message(sckt, 1), byteorder='big')
        msg = [name, y, x]  # three part message

    elif msg_type == b'k':
        y = int.from_bytes(_receive_message(sckt, 1), byteorder='big')
        x = int.from_bytes(_receive_message(sckt, 1), byteorder='big')
        msg = [y, x]  # two part message

    elif msg_type == b'w':  # Maze message
        msg = _receive_message(sckt, 2014).decode("ascii")

    if not_blck:
        sckt.setblocking(0)

    return (msg_type, msg)


def _receive_type(sckt):
    msg_type = sckt.recv(1)
    if msg_type == b'':
        raise ConnectionResetError("socket connection broken")
    return msg_type


def _receive_message(sckt, msglen):
    """Receive a message of msglen bytes"""
    chunks = []
    bytes_recd = 0
    while bytes_recd < msglen:
        chunk = sckt.recv(min(msglen - bytes_recd, 2048))
        if chunk == b'':
            raise ConnectionResetError("socket connection broken")
        chunks.append(chunk)
        bytes_recd = bytes_recd + len(chunk)
    return b''.join(chunks)


def _send_message(sckt, msg):
    """repeat sending till all message sent"""
    total_sent = 0
    while total_sent < len(msg):
        sent = sckt.send(msg[total_sent:])
        if sent == 0:
            raise ConnectionResetError("socket connection broken")
        total_sent = total_sent + sent
