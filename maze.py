import sys
from random import shuffle, randrange


def make_maze(w = 15, h = 20):
    vis = [[0] * w + [1] for _ in range(h)] + [[1] * (w + 1)]
    ver = [["|  "] * w + ['|'] for _ in range(h)] + [[]]
    hor = [["+--"] * w + ['+'] for _ in range(h + 1)]

    def walk(x, y):
        vis[y][x] = 1

        d = [(x - 1, y), (x, y + 1), (x + 1, y), (x, y - 1)]
        shuffle(d)
        for (xx, yy) in d:
            if vis[yy][xx]: continue
            if xx == x: hor[max(y, yy)][x] = "+  "
            if yy == y: ver[y][max(x, xx)] = "   "
            walk(xx, yy)

    walk(randrange(w), randrange(h))

    s = ""
    for (a, b) in zip(hor, ver):
        s += ''.join(a + ['\n'] + b + ['\n'])
    return s


def read_maze(maze):
    """Reads a maze string and produces a 2d array of walls"""
    walls = []
    for indx, line in enumerate(iter(maze.splitlines())):
        if indx % 2 == 0:  # even means horizontal, ie skip first char
            jmp = 1
        else:
            jmp = 0

        lnwalls = []
        for char in line:
            if jmp == 0:
                jmp = 2
                if char in ("-", "|"):
                    lnwalls.append(1)
                else:
                    lnwalls.append(0)
            else:
                jmp -= 1
        walls.append(lnwalls)

    return walls


def draw_maze(maze_arr):
    out = ""
    for indx, line in enumerate(maze_arr):
        if indx % 2 == 0:
            out += "+"
            hor = True
        else:
            hor = False
        for wall in line:
            if wall == 1:
                if hor:
                    out += "--+"
                else:
                    out += "|  "
            else:
                if hor:
                    out += "  +"
                else:
                    out += "   "
        if not hor:
            out = out[:-2]
        out += "\n"

    return out


if __name__ == '__main__':
    sys.setrecursionlimit(10000)
    maze = make_maze(21, 15)
    arr = read_maze(maze)
    maze2 = draw_maze(arr)
    print(maze)
    print(arr)
    print(maze2)
    print(len(maze2))
