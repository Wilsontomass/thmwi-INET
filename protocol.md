# Wilson protocol description

Clients connect to the server by opening a socket, and for the entire time that
the client is connected all data flows along one socket.

When a message is sent, it is always preceded by a single ascii encoded
byte specifying the type of the message, followed by data that conforms
to that types data protocol.

## Type descriptions
Each type is listed with the ascii interpretation of the leading byte.

### Client messages
Messages made from the client to the server.

1. Message type: "M", a message, where the second byte is unsigned 8bit int of
the message length, followed by that many bytes encoded in utf-8. Signifies an
outgoing chat message

2. Join type: "j", a join request sent to the server, which is identical to
the Message type, but where the last data is the name of the new player

3. Move type: "m", a move request, where the second byte is unsigned 8bit int of
the message length, followed by that many bytes encoded in utf-8 representing
the moving players name. The final byte is an ascii character, of either
0, 1, 2, or 3, signifying a cardinal direction the client would like to move
in, NESW respectively

### Server messages
Messages made to the client from the server.

1. Welcome type: "w", a return status message, after a successful join
request. The next 8514 bytes contain an ascii encoded string of the map
according to the server.

1. Message type: "M", a message, where the second byte is unsigned 8bit int of
the message length, followed by that many bytes encoded in utf-8. Signifies an
incoming chat message

2. Move type: "m", a move request, where the second byte is unsigned 8bit int of
the message length, followed by that many bytes encoded in utf-8 representing
the moving players name. The final byte is an ascii character, of either
0, 1, 2, or 3, signifying a cardinal direction the player will move
in, NESW respectively.

3. New player type: "n", A new player, where the second byte is unsigned 8bit int of
the message length, followed by that many bytes encoded in utf-8 representing
the new players name. The final two bytes are unsigned 8 bit ints, representing
the y and x coordinates of the new player respectively

4. Delete player type: "d", A player has left, delete them. The second byte is
unsigned 8bit int of the message length, followed by that many bytes encoded
in utf-8 representing the deleted players name.

4. New key type: "k", A new key, where the next two bytes are unsigned 8 bit ints,
representing the y and x coordinates of the new key respectively. This same
command is used to delete keys (once they are taken)

5. Status type: "s", varies based on previous message.
below is a list of status messages, all sent as single byte ascii characters
   1. "T": name taken, after join request
   2. "I": illegal move, after move request
   3. "W": Win. You have won (after move request)
