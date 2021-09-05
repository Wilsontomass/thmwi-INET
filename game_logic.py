import random
import maze
import numpy as np
import logging
from copy import deepcopy


class Game():
    def __init__(self):
        self.players = {}
        self.keys = []
        self.rows = 15
        self.cols = 21
        self.num_keys = 20
        self.keys_spawned = False
        self.board = None

    def genboard(self):
        """generate a game board"""
        maze_str = maze.make_maze(self.cols, self.rows)
        board = maze.read_maze(maze_str)
        self.board = board

    def loadboard(self, strinp):
        self.board = maze.read_maze(strinp)

    def new_player(self, name):
        """generate a new player position"""
        y = 0
        x = 0
        if len(self.players) == 0:  # first player
            y = random.randrange(self.rows)
            x = random.randrange(self.cols)
        else:
            y, x = self.get_common_furthest()
        self.add_player(name, y, x)
        logging.debug("new player %s added with coordinates y: %d x: %d",
                      name, x, y)
        return (y, x)

    def add_player(self, name, y, x):
        """add a player from existing coordinates"""
        self.players[name] = player(name, (y, x))

    def delete_player(self, name):
        del self.players[name]

    def find_furthest(self, y, x):
        vis = [[0] * self.cols + [1] for _ in range(self.rows)] + [[1] * (self.cols + 1)]

        def walk(y, x):
            vis[y][x] = 1
            bestSolution = {"start": (y, x), "end": (y, x), "distance": 0}
            d = [(y, x - 1), (y + 1, x), (y, x + 1), (y - 1, x)]
            random.shuffle(d)
            for (yy, xx) in d:
                if vis[yy][xx]:
                    continue

                newbest = walk(yy, xx)
                if newbest["distance"] > bestSolution["distance"]:
                    bestSolution["distance"] = newbest["distance"] + 1
                    bestSolution["end"] = newbest["end"]
            return bestSolution

        return walk(y, x)

    def get_common_furthest(self):
        """Get a point that is quite far from players and keys"""
        dist_grid = np.ones((self.rows, self.cols))
        for player_name in self.players:
            y, x = self.players[player_name].pos
            grid = self.distance_grid(y, x)
            dist_grid = dist_grid * grid

        for key in self.keys:
            y, x = key.pos
            grid = self.distance_grid(y, x)
            dist_grid = dist_grid * grid

        result = np.where(dist_grid == np.amax(dist_grid))
        listOfCordinates = list(zip(result[0], result[1]))
        y, x = random.choice(listOfCordinates)  # get rand occurance
        # convert from numpy types
        y = y.item()
        x = x.item()

        return (y, x)

    def distance_grid(self, y, x):
        """return a 2d numpy array containing distance from (y, x)"""
        grid = np.zeros((self.rows, self.cols))
        vis = [[0] * self.cols + [1] for _ in range(self.rows)] + [[1] * (self.cols + 1)]

        def walk(y, x, dist):
            vis[y][x] = 1
            grid[y][x] = dist
            d = [(y, x - 1), (y + 1, x), (y, x + 1), (y - 1, x)]
            random.shuffle(d)
            for (yy, xx) in d:
                if vis[yy][xx]:
                    continue
                walk(yy, xx, dist+1)

        walk(y, x, 0)
        return grid

    def move(self, name, direction):
        """Attempt to move a player in a direction, returns True if
        legal move, else false"""
        plyr = self.players[name]
        newy, newx = deepcopy(plyr.pos)
        chky = 0
        chkx = 0
        if direction == 0:
            newy -= 1
        elif direction == 1:
            newx += 1
            chky = 1
            chkx = 1
        elif direction == 2:
            newy += 1
            chky = 2
        elif direction == 3:
            newx -= 1
            chky = 1

        # Move player
        y, x = plyr.pos
        wally = y * 2
        if self.board[wally + chky][x + chkx] == 0:  # check no wall
            for check_player in self.players.values():
                if check_player.pos == (newy, newx):
                    return False
            plyr.pos = (newy, newx)
            return True

        return False  # illegal move

    def spawn_keys(self):
        if not self.keys_spawned:
            for _ in range(self.num_keys):
                y, x = self.get_common_furthest()
                self.keys.append(Key((y, x)))
            self.keys_spawned = True
            return True
        return False

    def toggle_key(self, y, x):
        """Toggle a key, returns False if key was deleted, True if new key
        added"""
        for key in self.keys:
            keyy, keyx = key.pos
            if (keyy == y) and (keyx == x):
                self.keys.remove(key)  # Delete key
                return False
        self.keys.append(Key((y, x)))  # Create new key
        return True

    def check_key(self, name):
        """check if player name is standing on a key, if so remove the key
        and return the keys position, else return None"""
        y, x = self.players[name].pos
        for key in self.keys:
            keyy, keyx = key.pos
            if (keyy == y) and (keyx == x):
                self.keys.remove(key)  # Delete key
                return (keyy, keyx)
        return None

    def is_win(self):
        """Returns true if the game has been won, else false"""
        if self.keys_spawned and (len(self.keys) == 0):
            return True
        return False

    def interact(self, name, action):
        pass

    def mazestr(self):
        """A function that creates a string of the maze"""
        try:
            maze_string = maze.draw_maze(self.board)
        except TypeError as e:
            print(self.board)
            raise e
        return maze_string


class player():
    def __init__(self, name, pos):
        self.name = name
        self.pos = pos
        self.health = 100
        self.items = []

    def hit(self, dmg):
        self.health -= dmg

    def pick(self, item):
        self.items.append(item)

    def has_item(self, item):
        for it in self.items:
            if it == item:
                return True
        return False


class Key():
    def __init__(self, pos):
        self.pos = pos
