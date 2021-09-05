import curses
import traceback
import sys
from time import sleep
from game_logic import Game


class Screen():
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.screen = curses.initscr()
        self.screen.keypad(True)
        self.init_colour()

        curses.resize_term(33, 96)
        self.game_started = False
        self.chat = None
        self.game = None

    def init_colour(self):
        curses.start_color()
        # Player colour
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_BLUE)
        # Allies Colour
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)
        # Keys Colour
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_YELLOW)

    def refresh(self):
        """Refresh all sub screens and main screen"""
        if self.game_started:
            self.chat.refresh()
            self.game.refresh()
        self.screen.refresh()

    def welcome(self):
        """Draw a welccome splash screen and get user name"""
        self.screen.addstr("Welcome to Tomass' super duper"
                           "cool maze game! The objective\n"
                           "is to collect all the white keys. "
                           "Good luck!\n")
        self.screen.addstr("please enter your name\n")
        self.screen.addstr("> ")
        x, y = self.screen.getyx()
        name = self.screen.getstr(x, y).decode("utf-8")
        self.screen.addstr("Welcome " + name + "!")
        self.refresh()
        sleep(1)
        return name

    def win(self):
        """draw a win Screen"""
        self.clear()
        self.screen.addstr("Well done! You have found all the keys!\n")
        self.screen.addstr("Press any key to exit\n")
        self.screen.getch()
        curses.endwin()
        sys.exit()

    def start_game(self, maze):
        """Initialise the game"""
        self.game_started = True
        self.chat = Chat(self, self.controller, 0, 66)
        self.game = GameScreen(self, self.controller, 0, 0)
        self.game.set_maze(maze)

    def clear(self):
        """Clear the entire screen"""
        self.screen.clear()

    def getdir(self):
        """get a single direction key input"""
        key = self.screen.getch()
        if key == curses.KEY_UP:
            return 0
        if key == curses.KEY_RIGHT:
            return 1
        if key == curses.KEY_DOWN:
            return 2
        if key == curses.KEY_LEFT:
            return 3
        return None

    def print_debug(self, msg):
        curses.endwin()
        print(msg)
        input()
        self.refresh()

    def print_exc(self, exc):
        curses.endwin()
        exc_type, exc_obj, exc_trace = exc
        traceback.print_exception(exc_type, exc_obj, exc_trace, 10)
        sys.exit()


class Chat():
    def __init__(self, parent, controller, x, y):
        self.parent = parent
        self.controller = controller
        self.window = self.parent.screen.derwin(33, 29, x, y)
        self.window.border()
        self.window.move(1, 0)
        self.prompt = None
        self.maxlen = None

    def set_prompt(self, prmpt):
        self.prompt = prmpt
        self.maxlen = 28 - len(prmpt)

    def print_line(self, msg):
        y, _ = self.window.getyx()
        self.window.addstr(y, 1, msg + "\n")
        self.refresh()

    def getinp(self):
        y, x = self.window.getyx()
        msg = self.window.getstr(y, x, self.maxlen).decode("utf-8")
        self.refresh()
        return msg

    def refresh(self):
        y, x = self.window.getyx()
        if self.prompt is not None:
            self.window.addstr(y, 1, self.prompt)
        self.window.border()
        self.window.refresh()


class GameScreen():
    def __init__(self, parent, controller, x, y):
        self.parent = parent
        self.controller = controller
        self.window = self.parent.screen.derwin(33, 65, x, y)
        self.game = Game()

    def refresh(self):
        """Redraw border and refresh screen"""
        self.draw_board()
        self.window.refresh()

    def set_maze(self, string):
        """Take an input string and update the board"""
        self.game.loadboard(string)

    def draw_board(self):
        maze = self.game.mazestr()
        for num, line in enumerate(maze.splitlines()):
            self.window.addstr(num, 0, line)
        for player_name in self.game.players:
            player = self.game.players[player_name]
            y, x = player.pos
            if player_name == self.controller.name:
                self.draw_cell(y, x, player_name[:2], 1)
            else:
                self.draw_cell(y, x, player_name[:2], 2)
        for key in self.game.keys:
            y, x = key.pos
            self.draw_cell(y, x, "ky", 3)

    def draw_cell(self, y, x, msg, pair_num):
        y = (y*2)+1
        x = (x*3)+1
        self.window.addstr(y, x, msg, curses.color_pair(pair_num))
