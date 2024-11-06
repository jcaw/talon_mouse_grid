from collections import namedtuple
import math
from typing import List, Optional
from random import randint

from talon import ui, canvas, screen, app, Module, Context, actions, cron
from talon.ui import Rect, Point2d

user = actions.user


# TODO: Cluster each prefix in an evenly-proportioned rectangle, where possible?
#   What's happening by default, is that each prefix is being layed out in
#   vertical stripes down the screen - less attractive, more distracting, harder
#   to track visually.


# Color of grid
GRID_COLOR = "F003"  # F0F is a nice purple, if I want bold
TEXT_COLOR = "FFFF"
TEXT_BACKGROUND_COLOR = "000A"
DROP_SHADOW_COLOR = "3333"
# Padding (as ratio of text size) for text background box
TEXT_BACKGROUND_PADDING = 0.2
# Should we fake a drop shadow on the grid?
DRAW_DROP_SHADOW = True

CELL_WIDTH = 50
CELL_HEIGHT = 40

MIN_9CELL_WIDTH = 10
MIN_9CELL_HEIGHT = 10

MIN_LABEL_WIDTH = 30
MIN_LABEL_HEIGHT = 20

CELL_FONT_SIZE = 18
# FIXME: better font picking method. This will fail if Fira Code is not installed.
CELL_TYPEFACE = "Fira Code"


# TODO: An order that's easier on the fingers?
#
# TODO: Select these in such a way as we optimise rolls?
#
# Alphabetical
# VALID_KEYS = "abcdefghijklmnopqrstuvwxyz"

# Ordered for optimising strong finger presses (index first, pinky last -
# alternating hands)
VALID_KEYS = "fjruvndkeicmslwoxaqpzghtyb"

# Left hand only
# VALID_KEYS = "frvdecswxaqz123456"

# Remove the numbers and cells will need 4 letters
# VALID_KEYS = "frvdecswxaqz"

# Additional
# VALID_KEYS += "1234567890"
# VALID_KEYS += ",./;'[]#-="
# VALID_KEYS += '!"£$%^&*()_+{}~:@<>?'


current_canvas = None
# Tracks whether a drag event is currently in progress.
holding_mouse_button = False


def overall_bounds(rects):
    left = min(map(lambda r: r.x, rects))
    right = max(map(lambda r: r.x + r.width, rects))
    top = min(map(lambda r: r.y, rects))
    bottom = max(map(lambda r: r.y + r.height, rects))
    width = right - left
    height = bottom - top
    return Rect(left, top, width, height)


def entire_screen_area():
    """Get the entire canvas area to draw on.

    :rtype: Rect.

    """
    screens = screen.screens()
    return overall_bounds(screens)


class Cell(Rect):
    def __init__(self, left, top, width, height, text=""):
        """Single selectable cell.

        :param: a canvas.paint object with which to calculate label positioning.

        """
        super().__init__(left, top, width, height)
        self.text = text
        self.right = left + width
        self.bottom = top + height


canvases = []


def create_canvases():
    for screen in ui.screens():
        c = canvas.Canvas.from_screen(screen)
        if app.platform == "windows":
            # HACK: Compensate for `from_screen` being broken and giving wrong heights.
            new_rect = Rect(*screen.rect)
            new_rect.width -= 1
            c.rect = new_rect
        c.register("draw", redraw_grid)
        c.freeze()
        canvases.append(c)


def destroy_canvases():
    for c in canvases:
        c.resume()
        c.unregister("draw", redraw_grid)
        c.close()
    canvases.clear()


def redraw_canvases():
    for c in canvases:
        c.resume()
        c.freeze()


class Interface:
    """Holds the state of the cell interface - which cells are active?"""

    def __init__(self):
        self.reset([])

    def reset(self, cells: List[Cell]):
        global current_canvas
        # TODO: Eliminate this? It only holds cells. But might expand it later.
        self.cells = cells
        # HACK: Redraw the global canvas. Messy to structure it like this but
        #   whatever.
        redraw_canvases()


interface = Interface()


def redraw_grid(canvas):
    global interface

    paint = canvas.paint

    # Draw grid
    # --------------------

    # For sharp lines, need to draw the grid without antialiasing.
    #
    # Side note: AA + fractional line width will produce a translucent line,
    # which may be desirable.
    paint.antialias = False
    paint.style = paint.Style.STROKE
    paint.stroke_width = 1
    # FIXME: Alpha is additive at the moment.
    paint.blendmode = paint.Blend.SRC

    if DRAW_DROP_SHADOW:
        paint.color = DROP_SHADOW_COLOR
        for cell in interface.cells:
            canvas.draw_rect(
                Rect(cell.x + 1, cell.y + 1, cell.width - 1, cell.height - 1)
            )
    paint.color = GRID_COLOR
    for cell in interface.cells:
        canvas.draw_rect(cell)

    # Exclude background
    # --------------------

    paint.style = paint.Style.STROKE_AND_FILL

    # HACK: Make it clearer when the mouse is being held
    if holding_mouse_button:
        paint.color = "0228"
    else:
        # Normal color
        paint.color = "0008"
    excluded = overall_bounds(interface.cells)
    excluded_right = excluded.left + excluded.width
    canvas_right = canvas.x + canvas.width
    excluded_bottom = excluded.top + excluded.height
    canvas_bottom = canvas.y + canvas.height

    # There are fudge pixels to retain the grid border.
    #
    # Left
    if excluded.left > canvas.x:
        canvas.draw_rect(
            Rect(canvas.x, canvas.y, excluded.left - canvas.x, canvas.width - 1)
        )
    # Top
    if excluded.top > canvas.y:
        canvas.draw_rect(
            Rect(canvas.x, canvas.y, canvas.width, excluded.top - canvas.y - 1)
        )
    # Right
    if excluded_right < canvas_right:
        canvas.draw_rect(
            Rect(
                excluded_right + 1,
                canvas.y,
                canvas_right - excluded_right - 1,
                canvas.height,
            )
        )
    # Bottom
    if excluded_bottom < canvas_bottom:
        canvas.draw_rect(
            Rect(
                canvas.x,
                excluded_bottom + 1,
                canvas.width,
                canvas_bottom - excluded_bottom - 1,
            )
        )

    # Draw Labels - Backgrounds
    # --------------------

    # TODO: Better way to get bold text (if we do, use `fill` for the background?)

    # Draw background boxes for the text
    paint.antialias = True
    paint.textsize = CELL_FONT_SIZE
    paint.typeface = CELL_TYPEFACE
    # TODO: Instead of erasing the labels, offset them to the sides.
    cells_to_label = list(
        filter(
            lambda c: c.width >= MIN_LABEL_WIDTH and c.height >= MIN_LABEL_HEIGHT,
            interface.cells,
        )
    )
    # TODO: Preallocate? Faster, no?
    # text_bg_rects = [Rect(0,0,0,0) for _ in range()]
    text_bg_rects = []
    # Height should accomodate tops & tails, so it's even.
    text_height = paint.measure_text("ly")[1].height
    for cell in cells_to_label:
        # Measure ""
        center = cell.center
        # Padding should be even on all sides
        # padding = max(
        #     text_rect.width * TEXT_BACKGROUND_PADDING,
        #     -text_rect.top * TEXT_BACKGROUND_PADDING,
        # )
        padding = text_height * TEXT_BACKGROUND_PADDING
        # HACK: All kinds of dodgy offset corrections in here
        text_width = paint.measure_text(
            # HACK: Single letters hard to see. Just enlarge them.
            "ll"
            if len(cell.text) == 1
            else cell.text
        )[1].width
        width = text_width + padding * 2
        height = text_height + padding * 2 + 1
        x = cell.center.x - width / 2
        # Background tends to poke over the text, use some wizardry to move it.
        y = cell.center.y - height / 2 + 2
        text_bg_rects.append(Rect(x, y, width, height))
    paint.color = TEXT_BACKGROUND_COLOR
    paint.style = paint.Style.FILL
    for rect in text_bg_rects:
        canvas.draw_rect(rect)
    paint.style = paint.Style.STROKE
    paint.color = "F0FA"
    for rect in text_bg_rects:
        canvas.draw_rect(rect)

    # Draw Labels - Text
    # --------------------
    paint.style = paint.Style.FILL
    # HACK: Text drop shadow to make it a bit easier to read by rendering twice.
    #   This should be cleaned up.
    # paint.color = "000F"
    # for cell in cells_to_label:
    #     _, text_rect = paint.measure_text(cell.text)
    #     new_vertical_offset = (text_rect.top - 1) / 2
    #     horizontal_offset = text_rect.width / 2
    #     center = cell.center
    #     canvas.draw_text(
    #         cell.text,
    #         center.x - horizontal_offset + 1,
    #         center.y - new_vertical_offset + 1,
    #     )
    paint.color = TEXT_COLOR
    for cell in cells_to_label:
        _, text_rect = paint.measure_text(cell.text)
        # Text is rendered with a negative vertical offset so it rests on the y
        # position provided. Use this offset to position the text, not its
        # height - this will make it look more central. There tends to be a
        # pixel added to the top of the text during this offset, so we manually
        # compensate for that.
        #
        # TODO: Derive the top padding procedurally? For larger text, it will be
        #   >1 pixel.
        #
        # Note the fudge factor here to get actually correct centered text. I'm
        # unsure why it's needed.
        new_vertical_offset = (-text_height + 4) / 2
        horizontal_offset = text_rect.width / 2 + 1.5
        center = cell.center
        canvas.draw_text(
            cell.text, center.x - horizontal_offset, center.y - new_vertical_offset
        )


def yield_labels(valid_keys, levels):
    """Generate labels from depth `levels`."""
    if levels <= 1:
        yield from valid_keys
    else:
        for prefix_key in valid_keys:
            for tail in yield_labels(valid_keys, levels - 1):
                yield f"{prefix_key}{tail}"


def generate_labels(valid_keys, cell_count):
    """Generate unique letter combinations to cover a number of cells.

    Will use the minimum length string necessary to cover all cells, given the
    set of `VALID_KEYS`.

    """
    # TODO: Disallow repeats?
    n_levels = 1
    while len(valid_keys) ** n_levels < cell_count:
        n_levels += 1
    yield from yield_labels(valid_keys, n_levels)


def fractional_range(start, end, n_items):
    jump = (end - start) / n_items
    return [(start + xs * jump, jump) for xs in range(n_items)]


module = Module()
module.tag("mouse_grid_active", "Active when the mouse grid is active")

# Context to hold state tags, e.g. when the mouse grid is active.
global_context = Context()
global_context.tags = []


def add_tag(context, tag):
    context.tags = context.tags.union({tag})


def remove_tag(context, tag):
    context.tags = context.tags.difference({tag})


def grid_center(cells):
    min_x = min(map(lambda c: c.left, cells))


labels_4grid = (
    # NOTE: Change this depending on keyboard layout - use 4 keys in a square.
    "we"
    "sd"
)


def create_4grid(bounds):
    """Create a 9-cell grid with standard controls."""
    global interface

    center = bounds.center
    width = max(bounds.width, MIN_9CELL_WIDTH)
    height = max(bounds.height, MIN_9CELL_HEIGHT)
    left = center.x - width / 2
    top = center.y - height / 2
    # TODO: Minimum grid size
    cells = []
    i = 0
    # y first so label lookup works
    for y, cell_height in fractional_range(top, top + height, 2):
        for x, cell_width in fractional_range(left, left + width, 2):
            # TODO: Embed label in square, so can position it here.
            cells.append(
                Cell(
                    x,
                    y,
                    cell_width,
                    cell_height,
                    str(labels_4grid[i]),
                )
            )
            # TODO 1: Move text to the outside of the box
            i += 1

    interface.reset(cells)


@module.action_class
class Actions:
    def mouse_grid_move():
        """Move to the center of the active grid cells."""
        try:
            global interface

            # TODO: Is this necessary? No, raise an error if there are no cells.
            if interface.cells:
                area = overall_bounds(interface.cells)
                actions.mouse_move(*area.center)
                return True
            else:
                return False

        finally:
            user.mouse_grid_exit()

    def mouse_grid_shake_mouse(seconds: float = 0.1, allowed_deviation: int = 5):
        """Briefly shake the cursor around its current position.

        Can be used to compensate for instantaneous mouse movement not being
        detected as a drag, e.g. when clicking + dragging Firefox tabs.

        """
        FRAME_PAUSE = 16
        PIXEL_RANGE = 5
        # Use a defined number of moves (not time) so behaviour is predictable.
        n_moves = max(int(seconds // (FRAME_PAUSE / 1000)), 1)

        start_x = actions.mouse_x()
        # Technically a race condition, but never going to come up
        start_y = actions.mouse_y()
        for i in range(n_moves):
            # NOTE: This will move in a square pattern, not a circle. That's
            #   probably fine.
            actions.mouse_move(
                start_x + randint(-PIXEL_RANGE, PIXEL_RANGE),
                start_y + randint(-PIXEL_RANGE, PIXEL_RANGE),
            )
            actions.sleep(f"{FRAME_PAUSE}ms")
        actions.mouse_move(start_x, start_y)

    def mouse_grid_click(
        button: int, modifier: Optional[str] = "", drag: Optional[bool] = False
    ):
        """Move to the center of the active mouse grid and click.

        Provide `modifier` to hold a single modifier while clicking. Provide
        `drag` to start a mouse drag. If a drag is in progress, it will *always*
        be released no matter the button provided.

        """
        global holding_mouse_button

        # TODO: Integrate with queued actions?
        if modifier:
            user.key(f"{modifier}:down")
            sleep("200ms")
        if user.mouse_grid_move():
            if holding_mouse_button:
                holding_mouse_button = False
                # Needed for some programs to register the drag.
                actions.self.mouse_grid_shake_mouse()
                actions.mouse_release(button)
            elif drag:
                assert (
                    button == 0
                ), f"Can only drag with the left button (0), not {button}"
                # Needed for some programs to register the drag
                actions.self.mouse_grid_shake_mouse()
                actions.mouse_drag()
                holding_mouse_button = True
            else:
                actions.mouse_click(button)
        if modifier:
            sleep("200ms")
            user.key(f"{modifier}:up")

    def mouse_grid_exit():
        """Close the mouse grid and release shortcuts."""
        try:
            interface.reset([])
            destroy_canvases()
        finally:
            remove_tag(global_context, "user.mouse_grid_active")

    def mouse_grid_narrow(key: str):
        """Reduce the active grid cells based on a key prefix."""
        global interface

        keep = []
        for cell in interface.cells:
            # It might be left-padded (see the code below for why).
            stripped = cell.text.strip()
            if stripped.startswith(key):
                cell.text = stripped[1:]
                # TODO: Left pad it so the position of the letters doesn't
                #   change as they're narrowed. Currently disabled because it
                #   screws up the text positioning.
                # while len(cell.text) < 3:
                #     cell.text = f" {cell.text}"
                keep.append(cell)

        if len(keep) == 0:
            # Ignore invalid prefixes.
            user.play_thunk()
        elif len(keep) == 1:
            # Final cell selected - now switch to the 4-cell selector in case
            # the user still wants to narrow the area (the 4-cell also acts as a
            # crosshair for the final click location, giving a more precise
            # visual aid).
            create_4grid(keep[0])
        else:
            # Still multiple candidates - display the constrained selection of cells
            interface.reset(keep)

    def mouse_grid_start():
        """Start a new mouse grid."""
        global interface, current_canvas

        # Clear any prior state
        user.mouse_grid_exit()

        cells = []
        # Distribute cells of a set size across each screen individually
        #
        # TODO: Sort screens by position
        for s in screen.screens():
            n_cells_x = math.ceil(s.rect.width / CELL_WIDTH)
            n_cells_y = math.ceil(s.rect.height / CELL_HEIGHT)

            for x, x_jump in fractional_range(
                s.rect.left, s.rect.left + s.rect.width, n_cells_x
            ):
                for y, y_jump in fractional_range(
                    s.rect.top, s.rect.top + s.rect.height, n_cells_y
                ):
                    cell = Cell(
                        round(x),
                        round(y),
                        round(x + x_jump - round(x)),
                        round(y + y_jump - round(y)),
                    )
                    cells.append(cell)
        # TODO: Distribute characters more effectively?
        #
        # TODO: Configurable VALID_KEYS?
        labels_iter = iter(generate_labels(VALID_KEYS, len(cells)))
        for cell in cells:
            cell.text = next(labels_iter)

        create_canvases()

        # Push the cell data into the canvas.
        interface.reset(cells)

        add_tag(global_context, "user.mouse_grid_active")
