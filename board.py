class Board:
    def __init__(self, board_img, center, coords):
        self.image = board_img
        self.cells = ['-' for _ in range(9)]
        self.center = center  # (x, y) pozycja środka planszy
        self.xmin, self.w, self.ymin, self.h = coords
        self.xmax = self.xmin + self.w
        self.ymax = self.ymin + self.h

    def __str__(self):
        return f"""
        \r---------
        \r| {self.cells[0]} {self.cells[1]} {self.cells[2]} |
        \r| {self.cells[3]} {self.cells[4]} {self.cells[5]} |
        \r| {self.cells[6]} {self.cells[7]} {self.cells[8]} |
        \r---------"""

    def symbol_wins(self, symbol):
        # sprawdzanie czy `symbol` występuje na wszystkich polach `c` danej linii
        # zaczynając od 3 wierszy, potem 3 kolumn i kończąc na przekątnych
        symbol_winning = [all(c == symbol for c in self.cells[:3]),
                          all(c == symbol for c in self.cells[3:6]),
                          all(c == symbol for c in self.cells[6:]),
                          all(c == symbol for c in (self.cells[i] for i in [0, 3, 6])),
                          all(c == symbol for c in (self.cells[i] for i in [1, 4, 7])),
                          all(c == symbol for c in (self.cells[i] for i in [2, 5, 8])),
                          all(c == symbol for c in (self.cells[i] for i in [0, 4, 8])),
                          all(c == symbol for c in (self.cells[i] for i in [2, 4, 6]))]
        return any(symbol_winning)

    def check_outcome(self):
        # sprawdzanie stanu rozgrywki na podstawie wykrytych symboli
        for symbol in ['x', 'o']:
            if self.symbol_wins(symbol):
                print(f"{symbol.upper()} wins!")
                return
        if any(c == '-' for c in self.cells):
            print("Game is not over.")
        else:
            print("It's a draw.")
        return

    def contains_cont(self, sym_x, sym_y, k=1):
        # sprawdzanie czy zadany środek konturu znajduje się w obrębie planszy
        k /= 2
        x, y = self.center
        return (int(x-k*self.w) <= sym_x <= int(x+k*self.w)) and (int(y-k*self.h) <= sym_y <= int(y+k*self.h))

    def update_cells(self, sym_x, sym_y, symbol):
        cell_id = 0
        heights = [int(self.ymin+self.h//3), int(self.ymin+self.h*2//3), self.ymax]
        widths = [int(self.xmin+self.w//3), int(self.xmin+self.w*2//3), self.xmax]
        for i, h in enumerate(heights):
            if sym_y < h:
                cell_id += 3*i
                break
        for j, w in enumerate(widths):
            if sym_x < w:
                cell_id += j
                break
        self.cells[cell_id] = symbol

    def update_middle(self, symbol):
        self.cells[4] = symbol

