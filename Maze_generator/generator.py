#!/usr/bin/env python3
"""Interactive maze generator.

Generates perfect mazes on a configurable grid. Click cells to place the start
and end points, adjust grid size and wall thickness, then export to PNG or SVG.

Requires a Python build with tkinter. On macOS with Homebrew Python:
    brew install python-tk
or just run it with the system Python: /usr/bin/python3 generator.py
"""

import random
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Wall bit flags, indexed by direction.
N, S, E, W = 1, 2, 4, 8
OPPOSITE = {N: S, S: N, E: W, W: E}
# direction -> (dcol, drow)
DELTA = {N: (0, -1), S: (0, 1), E: (1, 0), W: (-1, 0)}

MIN_SIZE, MAX_SIZE = 2, 100
MIN_CELL, MAX_CELL = 4, 80


def margin_pad(thickness):
    """Breathing room around the maze, scaled to the wall thickness."""
    return thickness + 10


class Maze:
    """A grid of cells, each storing which of its four walls stand."""

    def __init__(self, cols, rows):
        self.cols = cols
        self.rows = rows
        # Every cell starts fully walled in.
        self.cells = [[N | S | E | W] * cols for _ in range(rows)]

    def carve(self, seed=None):
        """Carve a perfect maze with randomised depth-first search.

        Iterative rather than recursive so large grids can't blow the stack.
        """
        rng = random.Random(seed)
        self.cells = [[N | S | E | W] * self.cols for _ in range(self.rows)]
        visited = [[False] * self.cols for _ in range(self.rows)]

        start = (rng.randrange(self.cols), rng.randrange(self.rows))
        visited[start[1]][start[0]] = True
        stack = [start]

        while stack:
            cx, cy = stack[-1]
            neighbours = []
            for direction, (dx, dy) in DELTA.items():
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows and not visited[ny][nx]:
                    neighbours.append((direction, nx, ny))

            if not neighbours:
                stack.pop()
                continue

            direction, nx, ny = rng.choice(neighbours)
            self.cells[cy][cx] &= ~direction
            self.cells[ny][nx] &= ~OPPOSITE[direction]
            visited[ny][nx] = True
            stack.append((nx, ny))

    def solve(self, start, end):
        """Breadth-first search for the unique path between two cells."""
        if start == end:
            return [start]

        prev = {start: None}
        queue = [start]
        while queue:
            current = queue.pop(0)
            if current == end:
                break
            cx, cy = current
            for direction, (dx, dy) in DELTA.items():
                if self.cells[cy][cx] & direction:
                    continue  # wall in the way
                nxt = (cx + dx, cy + dy)
                if nxt not in prev:
                    prev[nxt] = current
                    queue.append(nxt)

        if end not in prev:
            return []

        path = []
        node = end
        while node is not None:
            path.append(node)
            node = prev[node]
        path.reverse()
        return path

    def wall_segments(self):
        """Yield (col, row, direction) for every wall that stands.

        Interior walls are shared by two cells, so only the north and west
        sides are reported except along the bottom and right borders.
        """
        for y in range(self.rows):
            for x in range(self.cols):
                cell = self.cells[y][x]
                if cell & N:
                    yield x, y, N
                if cell & W:
                    yield x, y, W
                if y == self.rows - 1 and cell & S:
                    yield x, y, S
                if x == self.cols - 1 and cell & E:
                    yield x, y, E


class MazeApp:
    BG = "#1e1f26"
    WALL = "#e8e8ef"
    START = "#3ddc84"
    END = "#ff5a5f"
    PATH = "#4da3ff"

    def __init__(self, root):
        self.root = root
        root.title("Maze Generator")
        root.configure(bg=self.BG)
        root.minsize(760, 560)

        self.maze = Maze(20, 20)
        self.start = (0, 0)
        self.end = (19, 19)
        self.path = []
        self.place_mode = tk.StringVar(value="start")
        self.show_path = tk.BooleanVar(value=False)
        self.cell_px = 24  # recomputed on every draw to fit the canvas

        self._build_controls()
        self._build_canvas()
        self._sync_size_controls()
        self.regenerate()

    # ---------- UI construction ----------

    def _build_controls(self):
        bar = ttk.Frame(self.root, padding=(12, 10, 12, 4))
        bar.pack(side=tk.TOP, fill=tk.X)

        # Grid group: the maze's size measured in cells.
        grid_box = ttk.LabelFrame(bar, text="Grid (cells)", padding=(8, 4, 8, 6))
        grid_box.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(grid_box, text="Columns").grid(row=0, column=0, sticky="w")
        self.cols_var = tk.IntVar(value=self.maze.cols)
        ttk.Spinbox(grid_box, from_=MIN_SIZE, to=MAX_SIZE, width=5,
                    textvariable=self.cols_var,
                    command=self.on_size_change).grid(row=0, column=1, padx=(4, 12))

        ttk.Label(grid_box, text="Rows").grid(row=0, column=2, sticky="w")
        self.rows_var = tk.IntVar(value=self.maze.rows)
        ttk.Spinbox(grid_box, from_=MIN_SIZE, to=MAX_SIZE, width=5,
                    textvariable=self.rows_var,
                    command=self.on_size_change).grid(row=0, column=3, padx=(4, 0))

        # Size group: the drawn size in pixels.
        size_box = ttk.LabelFrame(bar, text="Size (pixels)", padding=(8, 4, 8, 6))
        size_box.pack(side=tk.LEFT, padx=(0, 10))

        self.fit_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(size_box, text="Fit to window", variable=self.fit_var,
                        command=self.on_fit_toggle).grid(row=0, column=0,
                                                         padx=(0, 12))

        ttk.Label(size_box, text="Cell").grid(row=0, column=1, sticky="w")
        self.cell_var = tk.IntVar(value=24)
        self.cell_spin = ttk.Spinbox(size_box, from_=MIN_CELL, to=MAX_CELL,
                                     width=5, textvariable=self.cell_var,
                                     command=self.on_cell_change)
        self.cell_spin.grid(row=0, column=2, padx=(4, 12))

        ttk.Label(size_box, text="W x H").grid(row=0, column=3, sticky="w")
        self.dims_label = ttk.Label(size_box, text="", width=13)
        self.dims_label.grid(row=0, column=4, padx=(4, 0))

        # Walls group.
        wall_box = ttk.LabelFrame(bar, text="Walls", padding=(8, 4, 8, 6))
        wall_box.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(wall_box, text="Thickness").grid(row=0, column=0, sticky="w")
        self.thickness_var = tk.IntVar(value=3)
        ttk.Scale(wall_box, from_=1, to=20, orient=tk.HORIZONTAL, length=120,
                  command=self.on_thickness_change).grid(row=0, column=1,
                                                         padx=(6, 4))
        self.thickness_label = ttk.Label(wall_box, text="3 px", width=6)
        self.thickness_label.grid(row=0, column=2)

        ttk.Button(bar, text="Generate",
                   command=self.regenerate).pack(side=tk.LEFT, pady=(12, 0))

        place = ttk.Frame(self.root, padding=(12, 0, 12, 8))
        place.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(place, text="Click a cell to place:").pack(side=tk.LEFT)
        ttk.Radiobutton(place, text="Start", value="start",
                        variable=self.place_mode).pack(side=tk.LEFT, padx=(8, 2))
        ttk.Radiobutton(place, text="End", value="end",
                        variable=self.place_mode).pack(side=tk.LEFT, padx=2)
        ttk.Checkbutton(place, text="Show solution", variable=self.show_path,
                        command=self.draw).pack(side=tk.LEFT, padx=(16, 2))
        ttk.Button(place, text="Export PNG",
                   command=self.export_png).pack(side=tk.RIGHT, padx=3)
        ttk.Button(place, text="Export SVG",
                   command=self.export_svg).pack(side=tk.RIGHT, padx=3)

        self.status = ttk.Label(self.root, text="", padding=(12, 0, 12, 8))
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

    def _build_canvas(self):
        wrap = ttk.Frame(self.root)
        wrap.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=12, pady=(0, 8))

        self.canvas = tk.Canvas(wrap, bg=self.BG, highlightthickness=0)
        vbar = ttk.Scrollbar(wrap, orient=tk.VERTICAL,
                             command=self.canvas.yview)
        hbar = ttk.Scrollbar(wrap, orient=tk.HORIZONTAL,
                             command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        vbar.grid(row=0, column=1, sticky="ns")
        hbar.grid(row=1, column=0, sticky="ew")
        wrap.rowconfigure(0, weight=1)
        wrap.columnconfigure(0, weight=1)

        self.canvas.bind("<Configure>", lambda _e: self.draw())
        self.canvas.bind("<Button-1>", self.on_click)

    # ---------- geometry ----------

    def _layout(self):
        """Cell size and top-left origin that centre the maze in the canvas.

        In fit mode the cell size is derived from the canvas; otherwise the
        cell size set in the controls is used verbatim, so the maze keeps its
        chosen pixel dimensions and the canvas scrolls if it overflows.
        """
        cw = max(self.canvas.winfo_width(), 1)
        ch = max(self.canvas.winfo_height(), 1)
        margin = self.thickness_var.get() + 10

        if self.fit_var.get():
            cell = min((cw - 2 * margin) / self.maze.cols,
                       (ch - 2 * margin) / self.maze.rows)
            cell = max(cell, 2)
        else:
            cell = self._clamped(self.cell_var, MIN_CELL, MAX_CELL)

        # Centre in the canvas, but never start inside the margin.
        ox = max(margin, (cw - cell * self.maze.cols) / 2)
        oy = max(margin, (ch - cell * self.maze.rows) / 2)
        return cell, ox, oy

    def maze_pixel_size(self, cell=None):
        """Drawn width and height of the maze in pixels, walls included."""
        if cell is None:
            cell, _, _ = self._layout()
        thickness = self.thickness_var.get()
        return (round(self.maze.cols * cell + thickness),
                round(self.maze.rows * cell + thickness))

    def _cell_at(self, px, py):
        cell, ox, oy = self._layout()
        # Translate window coordinates into canvas coordinates (scroll-aware).
        px = self.canvas.canvasx(px)
        py = self.canvas.canvasy(py)
        col = int((px - ox) // cell)
        row = int((py - oy) // cell)
        if 0 <= col < self.maze.cols and 0 <= row < self.maze.rows:
            return col, row
        return None

    # ---------- actions ----------

    def _clamped(self, var, low=MIN_SIZE, high=MAX_SIZE):
        try:
            value = int(var.get())
        except (tk.TclError, ValueError):
            value = low
        value = max(low, min(high, value))
        if value != var.get():
            var.set(value)
        return value

    def on_cell_change(self):
        """Cell size edited: leave fit mode so the value actually takes hold."""
        self._clamped(self.cell_var, MIN_CELL, MAX_CELL)
        if self.fit_var.get():
            self.fit_var.set(False)
        self._sync_size_controls()
        self.draw()

    def on_fit_toggle(self):
        if self.fit_var.get():
            self.canvas.configure(scrollregion=())
        else:
            # Adopt the current on-screen cell size as the starting point.
            cell, _, _ = self._layout()
            self.cell_var.set(max(MIN_CELL, min(MAX_CELL, round(cell))))
        self._sync_size_controls()
        self.draw()

    def _sync_size_controls(self):
        """Grey out the cell spinbox in fit mode and refresh the W x H read-out."""
        self.cell_spin.state(("disabled",) if self.fit_var.get() else ("!disabled",))

    def on_size_change(self):
        cols = self._clamped(self.cols_var)
        rows = self._clamped(self.rows_var)
        if (cols, rows) != (self.maze.cols, self.maze.rows):
            self.maze = Maze(cols, rows)
            # Keep the endpoints inside the new grid.
            self.start = (min(self.start[0], cols - 1), min(self.start[1], rows - 1))
            self.end = (min(self.end[0], cols - 1), min(self.end[1], rows - 1))
            self.regenerate()

    def on_thickness_change(self, value):
        self.thickness_var.set(int(float(value)))
        self.thickness_label.config(text=f"{self.thickness_var.get()} px")
        self.draw()

    def regenerate(self):
        cols = self._clamped(self.cols_var)
        rows = self._clamped(self.rows_var)
        if (cols, rows) != (self.maze.cols, self.maze.rows):
            self.maze = Maze(cols, rows)
        self.start = (min(self.start[0], cols - 1), min(self.start[1], rows - 1))
        self.end = (min(self.end[0], cols - 1), min(self.end[1], rows - 1))
        self.maze.carve()
        self.resolve()

    def resolve(self):
        self.path = self.maze.solve(self.start, self.end)
        self.draw()

    def on_click(self, event):
        cell = self._cell_at(event.x, event.y)
        if cell is None:
            return
        if self.place_mode.get() == "start":
            if cell == self.end:
                return
            self.start = cell
        else:
            if cell == self.start:
                return
            self.end = cell
        self.resolve()

    # ---------- drawing ----------

    def draw(self):
        self.canvas.delete("all")
        cell, ox, oy = self._layout()
        self.cell_px = cell
        thickness = self.thickness_var.get()

        width_px, height_px = self.maze_pixel_size(cell)
        self.dims_label.config(text=f"{width_px} x {height_px}")
        # Let the canvas scroll to whatever the maze actually occupies.
        self.canvas.configure(scrollregion=(
            0, 0, ox + cell * self.maze.cols + margin_pad(thickness),
            oy + cell * self.maze.rows + margin_pad(thickness)))

        self._fill_cell(self.start, cell, ox, oy, self.START)
        self._fill_cell(self.end, cell, ox, oy, self.END)

        if self.show_path.get() and len(self.path) > 1:
            points = []
            for cx, cy in self.path:
                points.append(ox + (cx + 0.5) * cell)
                points.append(oy + (cy + 0.5) * cell)
            self.canvas.create_line(*points, fill=self.PATH,
                                    width=max(1, cell * 0.22),
                                    capstyle=tk.ROUND, joinstyle=tk.ROUND)

        for x, y, direction in self.maze.wall_segments():
            x0, y0, x1, y1 = self._wall_coords(x, y, direction, cell, ox, oy)
            self.canvas.create_line(x0, y0, x1, y1, fill=self.WALL,
                                    width=thickness, capstyle=tk.ROUND)

        reachable = "solved" if self.path else "no path"
        mode = "fit" if self.fit_var.get() else f"{round(cell)} px/cell"
        self.status.config(
            text=f"{self.maze.cols} x {self.maze.rows} cells  |  "
                 f"{width_px} x {height_px} px ({mode})  |  "
                 f"start {self.start}  end {self.end}  |  "
                 f"{len(self.path)} cells ({reachable})")

    def _fill_cell(self, cell_rc, cell, ox, oy, colour):
        cx, cy = cell_rc
        pad = cell * 0.14
        self.canvas.create_rectangle(
            ox + cx * cell + pad, oy + cy * cell + pad,
            ox + (cx + 1) * cell - pad, oy + (cy + 1) * cell - pad,
            fill=colour, outline="")

    @staticmethod
    def _wall_coords(x, y, direction, cell, ox, oy):
        left, top = ox + x * cell, oy + y * cell
        right, bottom = left + cell, top + cell
        if direction == N:
            return left, top, right, top
        if direction == S:
            return left, bottom, right, bottom
        if direction == W:
            return left, top, left, bottom
        return right, top, right, bottom

    # ---------- export ----------

    def export_cell_size(self):
        """Cell size used for exports: the chosen one, or 24 px in fit mode."""
        if self.fit_var.get():
            return 24
        return self._clamped(self.cell_var, MIN_CELL, MAX_CELL)

    def export_svg(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".svg", filetypes=[("SVG image", "*.svg")],
            initialfile="maze.svg")
        if not path:
            return

        cell = self.export_cell_size()
        thickness = self.thickness_var.get()
        pad = thickness
        width = self.maze.cols * cell + 2 * pad
        height = self.maze.rows * cell + 2 * pad

        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}">',
            f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        ]

        for cell_rc, colour in ((self.start, self.START), (self.end, self.END)):
            cx, cy = cell_rc
            parts.append(
                f'<rect x="{pad + cx * cell + 3}" y="{pad + cy * cell + 3}" '
                f'width="{cell - 6}" height="{cell - 6}" fill="{colour}"/>')

        if self.show_path.get() and len(self.path) > 1:
            pts = " ".join(f"{pad + (cx + 0.5) * cell},{pad + (cy + 0.5) * cell}"
                           for cx, cy in self.path)
            parts.append(
                f'<polyline points="{pts}" fill="none" stroke="{self.PATH}" '
                f'stroke-width="{max(1, cell * 0.2):.1f}" stroke-linecap="round" '
                f'stroke-linejoin="round"/>')

        parts.append(f'<g stroke="#111111" stroke-width="{thickness}" '
                     f'stroke-linecap="round">')
        for x, y, direction in self.maze.wall_segments():
            x0, y0, x1, y1 = self._wall_coords(x, y, direction, cell, pad, pad)
            parts.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y1}"/>')
        parts.append("</g></svg>")

        with open(path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(parts))
        self.status.config(text=f"Saved {path}")

    def export_png(self):
        """PNG export goes through Pillow; SVG is the dependency-free option."""
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            messagebox.showinfo(
                "Pillow required",
                "PNG export needs Pillow (pip install pillow).\n"
                "Use Export SVG for a dependency-free vector file.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".png", filetypes=[("PNG image", "*.png")],
            initialfile="maze.png")
        if not path:
            return

        cell = self.export_cell_size()
        thickness = self.thickness_var.get()
        pad = thickness
        width = self.maze.cols * cell + 2 * pad
        height = self.maze.rows * cell + 2 * pad

        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)

        for cell_rc, colour in ((self.start, self.START), (self.end, self.END)):
            cx, cy = cell_rc
            draw.rectangle(
                [pad + cx * cell + 3, pad + cy * cell + 3,
                 pad + (cx + 1) * cell - 3, pad + (cy + 1) * cell - 3],
                fill=colour)

        if self.show_path.get() and len(self.path) > 1:
            pts = [(pad + (cx + 0.5) * cell, pad + (cy + 0.5) * cell)
                   for cx, cy in self.path]
            draw.line(pts, fill=self.PATH, width=max(1, int(cell * 0.2)),
                      joint="curve")

        for x, y, direction in self.maze.wall_segments():
            x0, y0, x1, y1 = self._wall_coords(x, y, direction, cell, pad, pad)
            draw.line([x0, y0, x1, y1], fill="black", width=thickness)

        image.save(path)
        self.status.config(text=f"Saved {path}")


def main():
    root = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except tk.TclError:
        pass
    MazeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
