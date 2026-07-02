import tkinter as tk
import webbrowser
from enum import Enum, auto
from tkinter import messagebox, ttk
from typing import Optional


def callback(url):
    """Открывает ссылку в браузере по умолчанию."""
    webbrowser.open_new(url)


class ChessGame:
    @staticmethod
    def play() -> None:
        """Создаёт окно приложения и запускает главный цикл tkinter."""
        app = ChessGame.App()
        try:
            app.mainloop()
        except KeyboardInterrupt:
            pass
        finally:
            exit()

    @staticmethod
    def opponent(color: "ChessGame.Color") -> "ChessGame.Color":
        """Возвращает цвет соперника для переданного цвета."""
        return ChessGame.Color.BLACK if color == ChessGame.Color.WHITE else ChessGame.Color.WHITE

    @staticmethod
    def correct_coords(row: int, col: int) -> bool:
        """Проверяет, что координаты (row, col) находятся в пределах доски 8x8."""
        return 0 <= row < 8 and 0 <= col < 8

    class Color(Enum):
        WHITE = auto()
        BLACK = auto()

    class Figure:
        """Базовый класс фигуры. Хранит цвет и односимвольное обозначение."""

        def __init__(self, color: "ChessGame.Color", _char: str = '') -> None:
            self.color = color
            self._char = _char

        def get_color(self) -> "ChessGame.Color":
            return self.color

        def char(self) -> str:
            return self._char

        def can_move(self, board: "ChessGame.Board", row: int, col: int, row1: int, col1: int) -> bool:
            """Базовая проверка хода: координаты валидны, ход не "на месте",
            и на целевой клетке нет фигуры того же цвета."""
            if not ChessGame.correct_coords(row, col) or not ChessGame.correct_coords(row1, col1):
                return False

            if row == row1 and col == col1:
                return False

            piece1 = board.get_piece(row1, col1)
            if piece1 and piece1.get_color() == self.color:
                return False

            return True

        def can_attack(self, board: "ChessGame.Board", row: int, col: int, row1: int, col1: int) -> bool:
            """По умолчанию правило взятия совпадает с правилом хода.
            Единственное исключение - пешка (см. Pawn.can_attack), у которой
            бой происходит по диагонали, а не так, как обычный ход."""
            return self.can_move(board, row, col, row1, col1)

    class Board:
        """Состояние доски: расположение фигур, чей сейчас ход, и флаги,
        нужные для проверки права на рокировку (двигались ли король/ладьи)."""

        def __init__(self) -> None:
            self.color = ChessGame.Color.WHITE
            self.field = []
            for row in range(8):
                self.field.append([None] * 8)

            self.field[0] = [
                ChessGame.Rook(ChessGame.Color.WHITE), ChessGame.Knight(ChessGame.Color.WHITE),
                ChessGame.Bishop(ChessGame.Color.WHITE), ChessGame.Queen(ChessGame.Color.WHITE),
                ChessGame.King(ChessGame.Color.WHITE), ChessGame.Bishop(ChessGame.Color.WHITE),
                ChessGame.Knight(ChessGame.Color.WHITE), ChessGame.Rook(ChessGame.Color.WHITE)
            ]
            self.field[1] = [
                ChessGame.Pawn(ChessGame.Color.WHITE), ChessGame.Pawn(ChessGame.Color.WHITE),
                ChessGame.Pawn(ChessGame.Color.WHITE), ChessGame.Pawn(ChessGame.Color.WHITE),
                ChessGame.Pawn(ChessGame.Color.WHITE), ChessGame.Pawn(ChessGame.Color.WHITE),
                ChessGame.Pawn(ChessGame.Color.WHITE), ChessGame.Pawn(ChessGame.Color.WHITE)
            ]
            self.field[6] = [
                ChessGame.Pawn(ChessGame.Color.BLACK), ChessGame.Pawn(ChessGame.Color.BLACK),
                ChessGame.Pawn(ChessGame.Color.BLACK), ChessGame.Pawn(ChessGame.Color.BLACK),
                ChessGame.Pawn(ChessGame.Color.BLACK), ChessGame.Pawn(ChessGame.Color.BLACK),
                ChessGame.Pawn(ChessGame.Color.BLACK), ChessGame.Pawn(ChessGame.Color.BLACK)
            ]
            self.field[7] = [
                ChessGame.Rook(ChessGame.Color.BLACK), ChessGame.Knight(ChessGame.Color.BLACK),
                ChessGame.Bishop(ChessGame.Color.BLACK), ChessGame.Queen(ChessGame.Color.BLACK),
                ChessGame.King(ChessGame.Color.BLACK), ChessGame.Bishop(ChessGame.Color.BLACK),
                ChessGame.Knight(ChessGame.Color.BLACK), ChessGame.Rook(ChessGame.Color.BLACK)
            ]

            self.white_king_moved = False
            self.black_king_moved = False
            self.white_rook0_moved = False
            self.white_rook7_moved = False
            self.black_rook0_moved = False
            self.black_rook7_moved = False

            # Клетка, на которую прямо сейчас возможно взятие на проходе (None, если оно недоступно).
            # Устанавливается только на один ближайший ход после того, как пешка сходила сразу на две клетки,
            # и сбрасывается после любого другого хода.
            self.en_passant_target: Optional[tuple[int, int]] = None

        def __str__(self) -> str:
            """Отрисовка консольного поля."""
            s = '     +----+----+----+----+----+----+----+----+\n'
            for row in range(7, -1, -1):
                s += f'  {row}  | '
                for col in range(8):
                    piece: ChessGame.Figure | None = self.field[row][col]
                    if piece is not None:
                        s += f'{self.cell(row, col)} | '
                    else:
                        s += '   | '
                s += '\n     +----+----+----+----+----+----+----+----+\n'
            s += '        0    1    2    3    4    5    6    7 \n'
            return s

        def print_board(self) -> None:
            print(self)

        def move_and_promote_pawn(self, row: int, col: int, row1: int, col1: int, char: str) -> bool:
            """Ход пешкой с одновременным превращением на последней горизонтали."""
            piece = self.field[row][col]
            if not isinstance(piece, ChessGame.Pawn):
                return False

            if piece.get_color() != self.color:
                return False

            if self.field[row1][col1]:
                if not piece.can_attack(self, row, col, row1, col1):
                    return False

            elif not self.field[row1][col1]:
                if not piece.can_move(self, row, col, row1, col1):
                    return False

            if char == 'Q':
                piece = ChessGame.Queen(piece.get_color())
            elif char == 'R':
                piece = ChessGame.Rook(piece.get_color())
            elif char == 'B':
                piece = ChessGame.Bishop(piece.get_color())
            elif char == 'N':
                piece = ChessGame.Knight(piece.get_color())
            else:
                return False

            self.field[row][col], self.field[row1][col1] = None, piece
            # Превращение пешки никогда не открывает возможность взятия на проходе на следующем ходу - сбрасываем цель.
            self.en_passant_target = None
            self.color = ChessGame.opponent(self.color)
            return True

        def can_castle0(self) -> bool:
            """Рокировка в сторону ладьи "a" (длинная рокировка, столбец 0)."""
            row = 0 if self.color == ChessGame.Color.WHITE else 7

            king = self.get_piece(row, 4)
            rook = self.get_piece(row, 0)

            if (not isinstance(king, ChessGame.King) or king.get_color() != self.color
                    or not isinstance(rook, ChessGame.Rook) or rook.get_color() != self.color):
                return False

            if self.color == ChessGame.Color.WHITE:
                if self.white_king_moved or self.white_rook0_moved:
                    return False

            else:
                if self.black_king_moved or self.black_rook0_moved:
                    return False

            # Между королём и ладьёй не должно быть фигур
            for c in range(1, 4):
                if self.get_piece(row, c):
                    return False

            # Король не должен находиться под шахом, а также проходить
            # или останавливаться на битом поле (клетки 4, 3, 2)
            for c in range(4, 1, -1):
                if self.is_under_attack(row, c, ChessGame.opponent(self.color)):
                    return False
            return True

        def castling0(self) -> bool:
            if not self.can_castle0():
                return False

            row = 0 if self.color == ChessGame.Color.WHITE else 7
            king = self.get_piece(row, 4)
            rook = self.get_piece(row, 0)

            self.field[row][4], self.field[row][2] = None, king
            self.field[row][0], self.field[row][3] = None, rook
            self.en_passant_target = None  # рокировка не пешечный рывок

            if self.color == ChessGame.Color.WHITE:
                self.white_king_moved = True
                self.white_rook0_moved = True
            else:
                self.black_king_moved = True
                self.black_rook0_moved = True

            self.color = ChessGame.opponent(self.color)
            return True

        def can_castle7(self) -> bool:
            """Рокировка в сторону ладьи "h" (короткая рокировка, столбец 7)."""
            row = 0 if self.color == ChessGame.Color.WHITE else 7

            king = self.get_piece(row, 4)
            rook = self.get_piece(row, 7)

            if (not isinstance(king, ChessGame.King) or king.get_color() != self.color
                    or not isinstance(rook, ChessGame.Rook) or rook.get_color() != self.color):
                return False

            if self.color == ChessGame.Color.WHITE:
                if self.white_king_moved or self.white_rook7_moved:
                    return False

            else:
                if self.black_king_moved or self.black_rook7_moved:
                    return False

            for c in range(5, 7):
                if self.get_piece(row, c):
                    return False

            for c in range(4, 7):
                if self.is_under_attack(row, c, ChessGame.opponent(self.color)):
                    return False
            return True

        def castling7(self) -> bool:
            if not self.can_castle7():
                return False

            row = 0 if self.color == ChessGame.Color.WHITE else 7
            king = self.get_piece(row, 4)
            rook = self.get_piece(row, 7)

            self.field[row][4], self.field[row][6] = None, king
            self.field[row][7], self.field[row][5] = None, rook
            self.en_passant_target = None  # рокировка не пешечный рывок

            if self.color == ChessGame.Color.WHITE:
                self.white_king_moved = True
                self.white_rook7_moved = True
            else:
                self.black_king_moved = True
                self.black_rook7_moved = True

            self.color = ChessGame.opponent(self.color)
            return True

        def is_under_attack(self, row: int, col: int, color: "ChessGame.Color") -> bool:
            """Проверяет, атакована ли клетка (row, col) хотя бы одной фигурой цвета color."""
            from itertools import product

            for row1, col1 in product(range(8), range(8)):
                piece: None | ChessGame.Figure = self.field[row1][col1]
                if piece and piece.get_color() == color and piece.can_attack(self, row1, col1, row, col):
                    return True
            return False

        def current_player_color(self) -> "ChessGame.Color":
            return self.color

        def cell(self, row: int, col: int) -> str:
            """Текстовое представление клетки для отладочного вывода доски в консоль."""
            piece: None | ChessGame.Figure = self.field[row][col]
            if piece is None:
                return '  '
            color = piece.get_color()
            c = 'w' if color == ChessGame.Color.WHITE else 'b'
            return c + piece.char()

        def get_piece(self, row: int, col: int) -> Optional["ChessGame.Figure"]:
            if ChessGame.correct_coords(row, col):
                return self.field[row][col]
            return None

        def move_piece(self, row: int, col: int, row1: int, col1: int) -> bool:
            """Обычный ход фигурой (без рокировки и без превращения пешки - для этих случаев есть отдельные методы)."""
            if not ChessGame.correct_coords(row, col) or not ChessGame.correct_coords(row1, col1):
                return False

            if row == row1 and col == col1:
                return False

            piece: None | ChessGame.Figure = self.field[row][col]
            if piece is None:
                return False

            if piece.get_color() != self.color:
                return False

            other_piece: None | ChessGame.Figure = self.field[row1][col1]

            # Взятие на проходе: пешка идёт по диагонали на пустую клетку,
            # которая прямо сейчас является целью en_passant_target.
            is_en_passant = (
                    other_piece is None
                    and isinstance(piece, ChessGame.Pawn)
                    and (row1, col1) == self.en_passant_target
                    and piece.attacks_square(row, col, row1, col1)
            )

            if other_piece is None:
                if not piece.can_move(self, row, col, row1, col1):
                    return False

            elif other_piece.get_color() == ChessGame.opponent(piece.get_color()):
                if not piece.can_attack(self, row, col, row1, col1):
                    return False
            else:
                return False

            # Запоминаем, что король/ладья сдвинулись - это лишает права на соответствующую рокировку до конца партии
            if isinstance(piece, ChessGame.Rook):
                if piece.get_color() == ChessGame.Color.WHITE:
                    if col == 0 and row == 0:
                        self.white_rook0_moved = True
                    elif col == 7 and row == 0:
                        self.white_rook7_moved = True
                else:
                    if col == 0 and row == 7:
                        self.black_rook0_moved = True
                    elif col == 7 and row == 7:
                        self.black_rook7_moved = True

            elif isinstance(piece, ChessGame.King):
                if piece.get_color() == ChessGame.Color.BLACK:
                    self.black_king_moved = True
                else:
                    self.white_king_moved = True

            if is_en_passant:
                # Взятая пешка стоит не на клетке назначения, а рядом: на той же горизонтали,
                # что и атакующая пешка, в столбце клетки назначения.
                self.field[row][col1] = None

                # Пешечный рывок на 2 клетки открывает взятие на проходе ровно на один следующий ход;
                # любой другой ход эту возможность закрывает.
            if isinstance(piece, ChessGame.Pawn) and abs(row1 - row) == 2:
                self.en_passant_target = ((row + row1) // 2, col)
            else:
                self.en_passant_target = None

            self.field[row][col], self.field[row1][col1] = None, piece
            self.color = ChessGame.opponent(self.color)
            return True

    class Rook(Figure):
        def __init__(self, color: "ChessGame.Color") -> None:
            super().__init__(color, 'R')

        def can_move(self, board: "ChessGame.Board", row: int, col: int, row1: int, col1: int) -> bool:
            """Ладья ходит по прямой (по вертикали или горизонтали), путь должен быть свободен."""
            if not super().can_move(board, row, col, row1, col1):
                return False

            if row != row1 and col != col1:
                return False

            if col1 == col:
                step = 1 if (row1 > row) else -1
                for r in range(row + step, row1, step):
                    if board.get_piece(r, col) is not None:
                        return False

            else:
                step = 1 if (col1 > col) else -1
                for c in range(col + step, col1, step):
                    if board.get_piece(row, c) is not None:
                        return False

            return True

    class Pawn(Figure):
        def __init__(self, color: "ChessGame.Color") -> None:
            super().__init__(color, 'P')

        def can_move(self, board: "ChessGame.Board", row: int, col: int, row1: int, col1: int) -> bool:
            """Пешка ходит только вперёд по своему столбцу: на 1 клетку всегда,
            и на 2 клетки - только с начальной позиции, и только если целевая
            клетка (и промежуточная при ходе на 2) свободны."""
            if not super().can_move(board, row, col, row1, col1):
                return False

            if col != col1:
                return False

            direction = 1 if self.color == ChessGame.Color.WHITE else -1
            start_row = 1 if self.color == ChessGame.Color.WHITE else 6

            if row + direction == row1:
                if not board.get_piece(row1, col1):
                    return True

            if row == start_row and row + 2 * direction == row1 and not board.field[row + direction][col]:
                return True

            return False

        def can_attack(self, board: "ChessGame.Board", row: int, col: int, row1: int, col1: int) -> bool:
            """Пешка бьёт по диагонали на одну клетку вперёд, и только если там
            действительно стоит фигура соперника (взятия "на проходе" не реализовано)."""
            if not ChessGame.correct_coords(row1, col1):
                return False

            piece1: None | ChessGame.Figure = board.field[row1][col1]
            if not piece1 or piece1.get_color() == self.color:
                return False

            direction = 1 if self.color == ChessGame.Color.WHITE else -1
            return row + direction == row1 and (col + 1 == col1 or col - 1 == col1)

        def attacks_square(self, row: int, col: int, row1: int, col1: int) -> bool:
            """Тот же диагональный паттерн, что и в can_attack, но БЕЗ проверки,
            что на клетке (row1, col1) кто-то стоит. Нужно для взятия на
            проходе: клетка назначения там всегда пустая, взятие происходит
            не по правилу can_attack, а по отдельной логике в move_piece."""
            if not ChessGame.correct_coords(row1, col1):
                return False
            direction = 1 if self.color == ChessGame.Color.WHITE else -1
            return row + direction == row1 and (col + 1 == col1 or col - 1 == col1)

    class Knight(Figure):
        def __init__(self, color: "ChessGame.Color") -> None:
            super().__init__(color, 'N')

        def can_move(self, board: "ChessGame.Board", row: int, col: int, row1: int, col1: int) -> bool:
            """Конь ходит буквой "Г": 2 клетки в одном направлении и 1 в перпендикулярном.
            Фигуры на пути не мешают (конь "перепрыгивает")."""
            if not super().can_move(board, row, col, row1, col1):
                return False

            return (abs(row1 - row) == 2 and abs(col1 - col) == 1) or (abs(row1 - row) == 1 and abs(col1 - col) == 2)

    class King(Figure):
        def __init__(self, color: "ChessGame.Color") -> None:
            super().__init__(color, 'K')

        def can_move(self, board: "ChessGame.Board", row: int, col: int, row1: int, col1: int) -> bool:
            """Король ходит на одну клетку в любом направлении (рокировка обрабатывается отдельно)."""
            if not super().can_move(board, row, col, row1, col1):
                return False

            return max(abs(row - row1), abs(col - col1)) == 1

    class Queen(Figure):
        def __init__(self, color: "ChessGame.Color") -> None:
            super().__init__(color, 'Q')

        def can_move(self, board: "ChessGame.Board", row: int, col: int, row1: int, col1: int) -> bool:
            """Ферзь сочетает ходы ладьи и слона: прямая или диагональ, путь свободен."""
            if not super().can_move(board, row, col, row1, col1):
                return False

            if (row != row1 and col != col1) and (abs(row - row1) != abs(col - col1)):
                return False

            if col == col1 or row == row1:
                if col == col1:
                    step = 1 if (row1 > row) else -1
                    for r in range(row + step, row1, step):
                        if board.get_piece(r, col):
                            return False

                if row == row1:
                    step = 1 if (col1 > col) else -1
                    for c in range(col + step, col1, step):
                        if board.get_piece(row, c):
                            return False

                return True

            elif abs(row - row1) == abs(col - col1):
                step = 1 if (row1 > row) else -1
                step1 = 1 if (col1 > col) else -1
                for r, c in zip(range(row + step, row1, step), range(col + step1, col1, step1)):
                    if board.get_piece(r, c):
                        return False
                return True

            return False

    class Bishop(Figure):
        def __init__(self, color: "ChessGame.Color") -> None:
            super().__init__(color, 'B')

        def can_move(self, board: "ChessGame.Board", row: int, col: int, row1: int, col1: int) -> bool:
            """Слон ходит по диагонали на любое число клеток, путь должен быть свободен."""
            if not super().can_move(board, row, col, row1, col1):
                return False

            if abs(row - row1) != abs(col - col1):
                return False

            step = 1 if (row1 > row) else -1
            step1 = 1 if (col1 > col) else -1
            for r, c in zip(range(row + step, row1, step), range(col + step1, col1, step1)):
                if board.get_piece(r, c):
                    return False

            return True

    class App(tk.Tk):
        """Главное окно приложения: содержит меню, экран настроек и игровое поле,
        реализованные как три наложенных друг на друга фрейма (place + lift)."""

        def __init__(self) -> None:
            super().__init__()
            self.title('Chess Game')
            self.minsize(520, 600)
            self.resizable(False, False)
            self.configure(bg='#000000')

            style = ttk.Style(self)
            style.theme_use('clam')
            style.configure('TButton',
                            font=('Segoe UI', 20, 'bold'),
                            padding=6,
                            background='#2d3436',
                            foreground='#dfe6e9',
                            borderwidth=0)
            style.map('TButton',
                      background=[('active', '#00cec9'), ('!active', '#2d3436')],
                      foreground=[('active', '#121212'), ('!active', '#dfe6e9')])
            style.configure('Hover.TButton',
                            font=('Segoe UI', 24, 'bold'),
                            background='#00cec9',
                            foreground='#121212')
            style.configure('TLabel',
                            background='#000000',
                            foreground='#00c8ff',
                            font=('Segoe UI', 20))
            style.configure('TFrame',
                            background='#000000')

            self.color_var = None
            self.color_menu = None
            self.canvas = None
            self.status_label = None

            self.board = None
            self.selected = None
            self.possible_moves = []
            self.capture_moves = set()
            self.castling_moves = set()
            self.promotion_pending = None
            self.square_size = 64
            self.colors = ['#b58863', '#debc8a']
            self.pieces_unicode = {
                'wP': '\u2659', 'wR': '\u2656', 'wN': '\u2658', 'wB': '\u2657', 'wQ': '\u2655', 'wK': '\u2654',
                'bP': '\u265F', 'bR': '\u265C', 'bN': '\u265E', 'bB': '\u265D', 'bQ': '\u265B', 'bK': '\u265A',
            }

            self.menu_frame = ttk.Frame(self, style='TFrame')
            self.settings_frame = ttk.Frame(self, style='TFrame')
            self.game_frame = ttk.Frame(self, style='TFrame')
            self.rules_frame = ttk.Frame(self, style='TFrame')

            self.menu_frame.place(relwidth=1, relheight=1)
            self.settings_frame.place(relwidth=1, relheight=1)
            self.game_frame.place(relwidth=1, relheight=1)
            self.rules_frame.place(relwidth=1, relheight=1)

            self.create_menu()
            self.create_settings()
            self.create_game()
            self.create_rules()

            self.show_menu()

        def create_menu(self) -> None:
            """Строит виджеты главного меню."""
            for widget in self.menu_frame.winfo_children():
                widget.destroy()

            self.menu_frame['padding'] = 20

            title = ttk.Label(self.menu_frame, text='Chess Game', font=('Segoe UI', 36, 'bold'),
                              foreground='#00c8ff', background='#000000')
            title.pack(pady=(60, 40))

            start_btn = ttk.Button(self.menu_frame, text='Start Game', command=self.start_game)
            start_btn.pack(pady=12, ipadx=10, ipady=6)

            settings_btn = ttk.Button(self.menu_frame, text='Settings', command=self.show_settings)
            settings_btn.pack(pady=12, ipadx=10, ipady=6)

            rules_btn = ttk.Button(self.menu_frame, text='Rules', command=self.show_rules)
            rules_btn.pack(pady=12, ipadx=10, ipady=6)

            exit_btn = ttk.Button(self.menu_frame, text='Exit', command=self.quit)
            exit_btn.pack(pady=12, ipadx=10, ipady=6)

            for btn in [start_btn, settings_btn, rules_btn, exit_btn]:
                btn.bind('<Enter>', lambda e, b=btn: b.configure(style='Hover.TButton'))
                btn.bind('<Leave>', lambda e, b=btn: b.configure(style='TButton'))

        def show_menu(self) -> None:
            """Показывает экран главного меню поверх остальных фреймов."""
            self.minsize(520, 600)
            self.menu_frame.lift()

        def create_settings(self) -> None:
            """Строит виджеты экрана настроек (выбор цветовой темы доски)."""
            for widget in self.settings_frame.winfo_children():
                widget.destroy()

            self.settings_frame['padding'] = 20

            title = ttk.Label(self.settings_frame, text='Settings', font=('Segoe UI', 30, 'bold'),
                              foreground='#00c8ff', background='#000000')
            title.pack(pady=(40, 30))

            self.color_var = tk.StringVar(value='Classic')

            color_label = ttk.Label(self.settings_frame, text='Тема Цвета Доски:', font=('Segoe UI', 20),
                                    foreground='#00c8ff', background='#000000')
            color_label.pack(pady=(10, 5))

            option_menu_frame = ttk.Frame(self.settings_frame, style='TFrame')
            option_menu_frame.pack(pady=(0, 20))

            self.color_menu = ttk.Combobox(option_menu_frame, textvariable=self.color_var, state='readonly',
                                           values=['Classic', 'Blue', 'Green', 'Gray'], font=('Segoe UI', 16))
            self.color_menu.pack()

            save_btn = ttk.Button(self.settings_frame, text='Save and Return', command=self.save_settings)
            save_btn.pack(pady=10, ipadx=10, ipady=6)

            back_btn = ttk.Button(self.settings_frame, text='Back to Menu', command=self.show_menu)
            back_btn.pack(pady=10, ipadx=10, ipady=6)

            for btn in [save_btn, back_btn]:
                btn.bind('<Enter>', lambda e, b=btn: b.configure(style='Hover.TButton'))
                btn.bind('<Leave>', lambda e, b=btn: b.configure(style='TButton'))

        def show_settings(self) -> None:
            self.minsize(520, 450)
            self.settings_frame.lift()

        def save_settings(self) -> None:
            """Применяет выбранную цветовую тему доски и возвращает в главное меню."""
            theme = self.color_var.get()

            if theme == 'Classic':
                self.colors = ['#b58863', '#debc8a']
            elif theme == 'Blue':
                self.colors = ['#5499c7', '#a9cce3']
            elif theme == 'Green':
                self.colors = ['#1e7342', '#a0dbb9']
            elif theme == 'Gray':
                self.colors = ['#5d5e5e', '#919b9c']

            messagebox.showinfo('Settings', 'Настройки сохранены!')
            self.show_menu()

        def create_game(self) -> None:
            """Строит виджеты игрового экрана: холст доски, статус хода, кнопки управления."""
            self.minsize(550, 700)
            for widget in self.game_frame.winfo_children():
                widget.destroy()

            self.canvas = tk.Canvas(self.game_frame, width=8 * self.square_size, height=8 * self.square_size,
                                    bg='#0a1f2f', highlightthickness=0)
            self.canvas.pack(pady=10)

            self.status_label = ttk.Label(self.game_frame, font=('Segoe UI', 16), foreground='#00c8ff',
                                          background='#000000')
            self.status_label.pack(pady=5)

            btn_frame = ttk.Frame(self.game_frame, style='TFrame')
            btn_frame.pack(pady=10)

            reset_btn = ttk.Button(btn_frame, text='Reset Game', command=self.reset_game)
            reset_btn.pack(side=tk.LEFT, padx=10, ipadx=10, ipady=6)

            menu_btn = ttk.Button(btn_frame, text='Main Menu', command=self.back_to_menu)
            menu_btn.pack(side=tk.LEFT, padx=10, ipadx=10, ipady=6)

            self.canvas.bind('<Button-1>', self.on_click)

        def create_rules(self) -> None:
            """Создаёт окно с кратким изложением правил и ссылкой на полный текст."""
            for widget in self.rules_frame.winfo_children():
                widget.destroy()

            self.rules_frame['padding'] = 20

            title = ttk.Label(self.rules_frame, text='Rules', font=('Segoe UI', 30, 'bold'),
                              foreground='#00c8ff', background='#000000')
            title.pack(pady=(40, 30))

            self.color_var = tk.StringVar(value='Classic')

            url = ("https://docs.yandex.ru/docs/view?tm=1782925588&tld=ru&lang=ru&name=LawsOfChess2023Russian.pdf"
                   "&text=ghfdbkf%20buhs%20d%20if%5Bvfns&url=https%3A%2F%2Fhandbook.fide.com%2Ffiles"
                   "%2Fhandbook%2FLawsOfChess2023Russian.pdf&lr=1091&mime=pdf&l10n=ru"
                   "&sign=ffa4d547a03ae37941b9492d6300cbbe&keyno=0&nosw=1&serpParams=tm%3D1782925588%26tld%3Dru%26lang"
                   "%3Dru%26name%3DLawsOfChess2023Russian.pdf%26text%3Dghfdbkf%2Bbuhs%2Bd%2Bif%255Bvfns%26url"
                   "%3Dhttps%253A%2F%2Fhandbook.fide.com%2Ffiles%2Fhandbook%2FLawsOfChess2023Russian.pdf%26lr"
                   "%3D1091%26mime%3Dpdf%26l10n%3Dru%26sign%3Dffa4d547a03ae37941b9492d6300cbbe%26keyno%3D0%26nosw%3D1")

            rules_text = (
                "1. Игра ведётся на доске 8×8.\n"
                "2. Белые ходят первыми, затем игроки чередуются.\n"
                "3. Каждая фигура ходит по-разному:\n"
                "   • Пешка — на 1 или 2 клетки вперёд первым ходом, бьёт по диагонали.\n"
                "   • Ладья — на любое число клеток по вертикали/горизонтали.\n"
                "   • Конь — ходит буквой «Г».\n"
                "   • Слон — на любое число клеток по диагонали.\n"
                "   • Ферзь — по вертикали, горизонтали и диагонали.\n"
                "   • Король — на одну клетку в любом направлении.\n"
                "4. Пешка превращается в другую фигуру, дойдя до последней горизонтали.\n"
                "5. Игра заканчивается матом, патом или сдачей."
            )

            lbl_rules = ttk.Label(self.rules_frame, text=rules_text, style='Rules.TLabel',
                                  wraplength=440, anchor='w', justify='left', font=('Segoe UI', 11))
            lbl_rules.pack(padx=24, pady=(0, 14), fill='x')

            # Кликабельная ссылка.
            lbl_link = tk.Label(self.rules_frame, text='Подробнее о правилах (FIDE PDF)', fg='#00c8ff', bg='#0a1f2f',
                                cursor='hand2', font=('Segoe UI', 11, 'underline'))
            lbl_link.pack(pady=(0, 16))
            lbl_link.bind('<Enter>', lambda e: lbl_link.configure(fg='#00cec9'))
            lbl_link.bind('<Leave>', lambda e: lbl_link.configure(fg='#00c8ff'))
            lbl_link.bind('<Button-1>', lambda _: callback(url))

            back_btn = ttk.Button(self.rules_frame, text='Back to Menu', command=self.show_menu)
            back_btn.pack(pady=10, ipadx=10, ipady=6)
            back_btn.bind('<Enter>', lambda e, b=back_btn: b.configure(style='Hover.TButton'))
            back_btn.bind('<Leave>', lambda e, b=back_btn: b.configure(style='TButton'))

        def show_rules(self) -> None:
            self.minsize(550, 600)
            self.rules_frame.lift()

        def show_game(self) -> None:
            self.minsize(550, 700)
            self.game_frame.lift()
            self.reset_game()

        def back_to_menu(self) -> None:
            if messagebox.askyesno('Quit Game', 'Вы уверены, что хотите выйти из игры?'):
                self.show_menu()

        def start_game(self) -> None:
            self.show_game()

        def reset_game(self) -> None:
            """Создаёт новую доску и сбрасывает состояние выделения/подсветки."""
            self.board = ChessGame.Board()
            print(self.board, end='\n')
            self.selected = None
            self.possible_moves = []
            self.capture_moves = set()
            self.castling_moves = set()
            self.promotion_pending = None
            self.draw_board()
            self.update_status()

        def draw_board(self) -> None:
            """Полностью перерисовывает доску: клетки, подсветку выделения/ходов,
            фигуры и рамку вокруг короля под шахом."""
            self.canvas.delete('all')
            from itertools import product
            for row, col in product(range(8), repeat=2):
                x1 = col * self.square_size
                y1 = (7 - row) * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size
                color = self.colors[(row + col) % 2]
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color)

                if self.selected == (row, col):
                    self.canvas.create_rectangle(x1, y1, x2, y2, outline='#00c8ff', width=3)

                if (row, col) in self.possible_moves:
                    if (row, col) in self.capture_moves:
                        self.canvas.create_oval(x1 + 15, y1 + 15, x2 - 15, y2 - 15, fill='#f20a0a')

                    elif (row, col) in self.castling_moves:
                        self.canvas.create_oval(x1 + 20, y1 + 20, x2 - 20, y2 - 20, fill='#1442cc')

                    else:
                        self.canvas.create_oval(x1 + 20, y1 + 20, x2 - 20, y2 - 20, fill='#0cf556')

                piece = self.board.get_piece(row, col)
                if piece:
                    # Все фигуры наследуются от Figure и всегда имеют метод char(),
                    # поэтому ключ строится напрямую, без запасного варианта 'wP'
                    key = ('w' if piece.get_color() == ChessGame.Color.WHITE else 'b') + piece.char()
                    piece_unicode = self.pieces_unicode.get(key, '')
                    self.canvas.create_text(x1 + self.square_size / 2, y1 + self.square_size / 2,
                                            text=piece_unicode, font=('Segoe UI Symbol', 40))

                    if (isinstance(piece, ChessGame.King) and
                            self.board.is_under_attack(row, col, ChessGame.opponent(piece.get_color()))):
                        self.canvas.create_rectangle(x1, y1, x2, y2, outline='#ff3864', width=3)

        def on_click(self, event) -> None:
            """Обрабатывает клик по доске: выбор фигуры, снятие выделения или ход."""
            if self.promotion_pending:
                return

            col = event.x // self.square_size
            row = 7 - (event.y // self.square_size)
            if not ChessGame.correct_coords(row, col):
                return

            piece = self.board.get_piece(row, col)
            if self.selected:
                if (row, col) in self.possible_moves:
                    self.try_move(self.selected[0], self.selected[1], row, col)

                elif piece and piece.get_color() == self.board.current_player_color():
                    self.select_piece(row, col)

                else:
                    self.selected = None
                    self.possible_moves = []
                    self.capture_moves = set()
                    self.castling_moves = set()

            elif piece and piece.get_color() == self.board.current_player_color():
                self.select_piece(row, col)
            self.draw_board()

        def select_piece(self, row: int, col: int) -> None:
            """Выделяет фигуру на (row, col) и пересчитывает доступные ей ходы,
            взятия и рокировки."""
            self.selected = (row, col)
            self.possible_moves = self.get_valid_moves(row, col)
            self.capture_moves = self.get_capture_moves(row, col)
            self.castling_moves = self.get_castling_targets(row, col)

        def get_valid_moves(self, row: int, col: int) -> list[tuple[int, int]]:
            """Возвращает список клеток, куда фигура с (row, col) может легально
            сходить - то есть ход в принципе разрешён правилами фигуры и после
            него собственный король не остаётся под шахом."""
            moves = []
            piece = self.board.get_piece(row, col)
            if not piece:
                return moves

            from itertools import product
            for r, c in product(range(8), repeat=2):
                if r == row and c == col:
                    continue

                if isinstance(piece, ChessGame.Pawn):
                    if (not self.board.field[r][c] and piece.can_move(self.board, row, col, r, c)
                            and self.is_move_safe(row, col, r, c)):
                        moves.append((r, c))
                    elif piece.can_attack(self.board, row, col, r, c) and self.is_move_safe(row, col, r, c):
                        moves.append((r, c))
                    elif ((r, c) == self.board.en_passant_target
                          and piece.attacks_square(row, col, r, c)
                          and self.is_move_safe(row, col, r, c)):
                        # Взятие на проходе: клетка назначения пуста.
                        moves.append((r, c))

                else:
                    if (not self.board.field[r][c] and piece.can_move(self.board, row, col, r, c)
                            and self.is_move_safe(row, col, r, c)):
                        moves.append((r, c))

                    elif piece.can_attack(self.board, row, col, r, c) and self.is_move_safe(row, col, r, c):
                        moves.append((r, c))

            # Рокировочные клетки тоже добавляем в общий список ходов - это нужно,
            # чтобы check_game_over корректно определял мат/пат.
            if isinstance(piece, ChessGame.King) and piece.get_color() == self.board.current_player_color():
                if self.board.can_castle0() and self.is_move_safe(row, col, row, 2):
                    moves.append((row, 2))

                if self.board.can_castle7() and self.is_move_safe(row, col, row, 6):
                    moves.append((row, 6))

            return moves

        def get_castling_targets(self, row: int, col: int) -> set[tuple[int, int]]:
            """Возвращает клетки, доступные фигуре на (row, col) именно через
            рокировку - используется только для подсветки на доске."""
            targets = set()
            piece = self.board.get_piece(row, col)
            if not isinstance(piece, ChessGame.King) or piece.get_color() != self.board.current_player_color():
                return targets

            if self.board.can_castle0() and self.is_move_safe(row, col, row, 2):
                targets.add((row, 2))
            if self.board.can_castle7() and self.is_move_safe(row, col, row, 6):
                targets.add((row, 6))
            return targets

        def get_capture_moves(self, row: int, col: int) -> set[tuple[int, int]]:
            """Из всех легальных ходов фигуры выбирает те, что являются взятием
            (на целевой клетке стоит фигура соперника)."""
            captures = set()
            piece = self.board.get_piece(row, col)

            if not piece:
                return captures

            for r, c in self.get_valid_moves(row, col):
                target_piece = self.board.get_piece(r, c)
                if target_piece and target_piece.get_color() != piece.get_color():
                    captures.add((r, c))
                elif isinstance(piece, ChessGame.Pawn) and (r, c) == self.board.en_passant_target:
                    # Клетка взятия на проходе пуста (взятая пешка стоит
                    # рядом), но для игрока это тоже взятие - подсвечиваем
                    # его так же, как обычные захваты.
                    captures.add((r, c))

            return captures

        def is_move_safe(self, row: int, col: int, row1: int, col1: int) -> bool:
            """Проверяет, не окажется ли собственный король под шахом после
            гипотетического хода. Для этого ход "проигрывается" на копии доски."""
            from copy import deepcopy
            temp_board = deepcopy(self.board)
            piece = temp_board.get_piece(row, col)

            if piece is None:
                return False

            # Если это взятие на проходе, на реальной доске исчезнет ещё и
            # пешка-жертва, стоящая рядом с целью, а не на ней самой.
            if (isinstance(piece, ChessGame.Pawn) and temp_board.field[row1][col1] is None
                    and (row1, col1) == temp_board.en_passant_target):
                temp_board.field[row][col1] = None

            temp_board.field[row1][col1] = piece
            temp_board.field[row][col] = None
            king_pos = None
            for r in range(8):
                for c in range(8):
                    p = temp_board.get_piece(r, c)
                    if isinstance(p, ChessGame.King) and p.get_color() == piece.get_color():
                        king_pos = (r, c)
                        break

                if king_pos:
                    break

            if king_pos is None:
                return False

            if temp_board.is_under_attack(king_pos[0], king_pos[1], ChessGame.opponent(piece.get_color())):
                return False

            return True

        def try_move(self, row, col, row1, col1) -> None:
            """Пытается выполнить выбранный ход: рокировку, превращение пешки
            или обычный ход - в зависимости от того, что выбрал игрок."""
            piece = self.board.get_piece(row, col)

            if not piece:
                return

            if isinstance(piece, ChessGame.King):
                if col == 4 and col1 == 2 and row == row1:
                    if self.board.castling0():
                        self.selected = None
                        self.possible_moves = []
                        self.capture_moves = set()
                        self.castling_moves = set()
                        self.update_status()
                        print(self.board, end='\n')
                        self.draw_board()
                        self.check_game_over()
                        return

                if col == 4 and col1 == 6 and row == row1:
                    if self.board.castling7():
                        self.selected = None
                        self.possible_moves = []
                        self.capture_moves = set()
                        self.castling_moves = set()
                        self.update_status()
                        print(self.board, end='\n')
                        self.draw_board()
                        self.check_game_over()
                        return

            if isinstance(piece, ChessGame.Pawn):
                promotion_row = 7 if piece.get_color() == ChessGame.Color.WHITE else 0
                if row1 == promotion_row:
                    self.promotion_pending = (row, col, row1, col1)
                    self.ask_promotion()
                    print(self.board, end='\n')
                    return

            moved = self.board.move_piece(row, col, row1, col1)
            if moved:
                self.selected = None
                self.possible_moves = []
                self.capture_moves = set()
                self.castling_moves = set()
                self.update_status()
                print(self.board, end='\n')
                self.draw_board()
                self.check_game_over()

        def ask_promotion(self) -> None:
            """Открывает модальное окно выбора фигуры для превращения пешки."""

            def promote(char):
                row, col, row1, col1 = self.promotion_pending
                success = self.board.move_and_promote_pawn(row, col, row1, col1, char)
                if success:
                    self.promotion_pending = None
                    self.update_status()
                    self.draw_board()
                    promotion_window.destroy()
                    self.check_game_over()

                else:
                    messagebox.showerror('Error', 'Неверный выбор.')

            promotion_window = tk.Toplevel(self)
            promotion_window.title('Pawn Promotion')
            promotion_window.minsize(400, 350)
            promotion_window.resizable(False, False)
            promotion_window.configure(bg='#0a1f2f')
            promotion_window.grab_set()
            promotion_window.transient(self)

            label = ttk.Label(promotion_window, text='Превратить пешку в:', font=('Segoe UI', 20),
                              foreground='#00c8ff', background='#0a1f2f')
            label.pack(pady=10)

            buttons_frame = ttk.Frame(promotion_window, style='TFrame')
            buttons_frame.pack(pady=5)

            for fig, name, r, c in [('Q', 'Ферзь', 1, 1), ('R', 'Ладья', 1, 2), ('B', 'Слон', 2, 1),
                                    ('N', 'Конь', 2, 2)]:
                btn = ttk.Button(buttons_frame, text=name, width=8,
                                 command=lambda x=fig: promote(x))
                btn.grid(row=r, column=c, padx=5, pady=10)

            promotion_window.wait_window()

        def update_status(self) -> None:
            """Обновляет подпись под доской: чей сейчас ход."""
            color = self.board.current_player_color()
            self.status_label.config(text=f"{'White' if color == ChessGame.Color.WHITE else 'Black'}'s turn")

        def check_game_over(self) -> None:
            """Проверяет окончание партии после каждого хода: потеря короля
            (защитный случай), мат, пат или обычный шах."""
            color = self.board.current_player_color()
            king_pos = None
            for r in range(8):
                for c in range(8):
                    p = self.board.get_piece(r, c)
                    if isinstance(p, ChessGame.King) and p.get_color() == color:
                        king_pos = (r, c)
                        break

                if king_pos:
                    break

            if king_pos is None:
                winner = 'Белые' if ChessGame.opponent(color) == ChessGame.Color.WHITE else 'Черные'
                messagebox.showinfo('Game Over', f'{winner} победили! Король попал в плен.')
                self.reset_game()
                return

            in_check = self.board.is_under_attack(king_pos[0], king_pos[1], ChessGame.opponent(color))

            has_moves = False
            for r in range(8):
                for c in range(8):
                    p = self.board.get_piece(r, c)
                    if p and p.get_color() == color:
                        moves = self.get_valid_moves(r, c)

                        if moves:
                            has_moves = True
                            break

                if has_moves:
                    break

            if in_check and not has_moves:
                winner = 'Белые' if ChessGame.opponent(color) == ChessGame.Color.WHITE else 'Черные'
                messagebox.showinfo('Checkmate', f'Шах и мат! {winner} победили!')
                self.reset_game()

            elif not in_check and not has_moves:
                messagebox.showinfo('Stalemate', 'Тупик! Игра закончилась вничью.')
                self.reset_game()

            elif in_check:
                side = 'Белые' if color == ChessGame.Color.WHITE else 'Черные'
                self.status_label.config(text=f'{side} под шахом!')

            else:
                self.update_status()


# Точка входа.
if __name__ == '__main__':
    ChessGame.play()
