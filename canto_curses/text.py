# -*- coding: utf-8 -*-
#Canto-curses - ncurses RSS reader
#   Copyright (C) 2010 Jack Miller <jack@codezen.org>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License version 2 as 
#   published by the Free Software Foundation.

from .theme import FakePad, WrapPad, theme_print, theme_lstrip, theme_border
from .command import command_format
from .guibase import GuiBase
from .theme import theme_print

import logging
import curses

log = logging.getLogger("TEXTBOX")

class TextBox(GuiBase):
    def init(self, pad, callbacks):
        self.pad = pad

        self.max_offset = 0

        self.callbacks = callbacks

        self.text = ""

    def get_offset(self):
        return self.callbacks["get_var"](self.get_opt_name() + "_offset")

    def set_offset(self, offset):
        self.callbacks["set_var"](self.get_opt_name() + "_offset", offset)

    def update_text(self):
        pass

    def refresh(self):
        self.height, self.width = self.pad.getmaxyx()

        fp = FakePad(self.width)
        lines = self.render(fp)

        # Create pre-rendered pad
        self.fullpad = curses.newpad(lines, self.width)
        self.render(WrapPad(self.fullpad))

        # Update offset based on new display properties.
        self.max_offset = max((lines - 1) - (self.height - 1), 0)

        offset = min(self.get_offset(), self.max_offset)
        self.set_offset(offset)
        self.callbacks["set_var"]("needs_redraw", True)

    def redraw(self):
        offset = self.get_offset()
        tb, lb, bb, rb = self.callbacks["border"]()

        # Overwrite visible pad with relevant area of pre-rendered pad.
        self.pad.erase()

        realheight = min(self.height, self.fullpad.getmaxyx()[0]) - 1

        top = 0
        if tb:
            self.pad.move(0, 0)
            self.render_top_border(WrapPad(self.pad))
            top += 1

        self.fullpad.overwrite(self.pad, offset, 0, top, 0,\
                realheight - top, self.width - 1)

        if bb:
            # If we're not floating, then the bottom border
            # belongs at the bottom of the given window.

            if not self.callbacks["floating"]():
                padheight = self.pad.getmaxyx()[0] -1
                self.pad.move(padheight - 1, 0)
                self.render_bottom_border(WrapPad(self.pad))
                self.pad.move(padheight - 1, 0)
            else:
                self.pad.move(realheight - 1, 0)
                self.render_bottom_border(WrapPad(self.pad))
                self.pad.move(realheight - 1, 0)
        else:
            self.pad.move(realheight - 1, 0)

        self.callbacks["refresh"]()

    def render_top_border(self, pad):
        tb, lb, bb, rb = self.callbacks["border"]()

        lc = " "
        if lb:
            lc = "%1%C" + theme_border("tl") + "%c%0"

        rc = " "
        if rb:
            rc = "%1%C" + theme_border("tr") + "%c%0"

        mainbar = "%1%C" + (theme_border("ts") * (self.width - 1)) + "%0%c"
        theme_print(pad, mainbar, self.width, lc, rc)

    def render_bottom_border(self, pad):
        tb, lb, bb, rb = self.callbacks["border"]()

        lc = " "
        if lb:
            lc = "%1%C" + theme_border("bl") + "%c%0"

        rc = " "
        if rb:
            rc = "%1%C" + theme_border("br") + "%c%0"

        mainbar = "%1%C" + (theme_border("ts") * (self.width - 1)) + "%0%c"
        theme_print(pad, mainbar, self.width, lc, rc)

    def render(self, pad):
        self.update_text()

        tb, lb, bb, rb = self.callbacks["border"]()
        s = self.text

        lines = 0

        # Account for potential top border rendered on redraw.
        if tb:
            lines += 1

        # Prepare left and right borders

        l = " "
        if lb:
            l = "%1%C" + theme_border("ls") + " %c%0"
        r = " "
        if rb:
            r = "%1%C " + theme_border("rs") + "%c%0"

        # Render main content

        while s:
            s = theme_lstrip(pad, s)
            if s:
                s = theme_print(pad, s, self.width, l, r)
                lines += 1

        # Account for potential bottom rendered on redraw.
        if bb:
            lines += 1

        # Return one extra line because the rest of the reader
        # code knows to avoid the dead cell on the bottom right
        # of every curses pad.

        return lines + 1

    @command_format([])
    def cmd_scroll_up(self, **kwargs):
        self._relscroll(-1)

    @command_format([])
    def cmd_scroll_down(self, **kwargs):
        self._relscroll(1)

    @command_format([])
    def cmd_page_up(self, **kwargs):
        self._relscroll(-1 * (self.height - 1))

    @command_format([])
    def cmd_page_down(self, **kwargs):
        self._relscroll(self.height - 1)

    def _relscroll(self, factor):
        offset = self.get_offset()
        offset += factor
        offset = min(offset, self.max_offset)
        offset = max(offset, 0)

        self.set_offset(offset)
        self.callbacks["set_var"]("needs_redraw", True)

    def is_input(self):
        return False

    def get_opt_name(self):
        return "textbox"

    def get_height(self, mheight):
        return mheight

    def get_width(self, mwidth):
        return mwidth

class ErrorBox(TextBox):
    def update_text(self):
        self.text = "%7" + self.callbacks["get_var"]("error_msg") + "%0"

    def get_opt_name(self):
        return "errorbox"

class InfoBox(TextBox):
    def update_text(self):
        self.text = "%1" + self.callbacks["get_var"]("info_msg") + "%0"

    def get_opt_name(self):
        return "infobox"
