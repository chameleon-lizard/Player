#!/usr/bin/env python

import sys
import os
import gi

gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
gi.require_version('Gtk', '3.0')

from gi.repository import Gst, GObject, Gtk, GLib, Gdk
from gi.repository import GdkX11, GstVideo

class GTK_Main(object):

    def __init__(self):
        self.playing = False
        self.uri = ""
        self.isFullscreen = False
        self.menuVisible = True

        self.window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        self.window.set_title("Player")
        self.window.set_default_size(800, 600)
        self.window.connect("destroy", Gtk.main_quit, "WM destroy")
        self.window.connect('key-press-event', self.on_keypress)

        self.vbox = Gtk.VBox(homogeneous=False, spacing=2)
        self.window.add(self.vbox)
        self.hbox = Gtk.HBox(homogeneous=False, spacing=2)
        self.vbox.pack_start(self.hbox, False, False, 10)

        self.movie_window = Gtk.DrawingArea()
        self.vbox.add(self.movie_window)

        self.menuButton = Gtk.Button.new()
        self.menuButtonImage = Gtk.Image()
        self.menuButtonImage.set_from_icon_name(
            "open-menu-symbolic", Gtk.IconSize.BUTTON)
        self.menuButton.add(self.menuButtonImage)
        self.menuButton.connect("clicked", self.menu_clicked)
        self.hbox.pack_end(self.menuButton, False, False, 5)        

        self.popover = Gtk.Popover()
        self.popover.set_border_width(5)
        self.hboxMenu = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.popover.add(self.hboxMenu)
        self.popover.set_position(Gtk.PositionType.BOTTOM)

        self.fileChooser = Gtk.Button.new()
        self.fileChooserImage = Gtk.Image()
        self.fileChooserImage.set_from_icon_name(
            "gtk-file", Gtk.IconSize.BUTTON)
        self.fileChooser.add(self.fileChooserImage)
        self.fileChooser.connect("clicked", self.on_file_clicked)
        self.hboxMenu.pack_start(self.fileChooser, False, False, 10)

        self.playButtonImage = Gtk.Image()
        self.playButtonImage.set_from_icon_name(
            "gtk-media-play", Gtk.IconSize.BUTTON)
        self.playButton = Gtk.Button.new()
        self.playButton.add(self.playButtonImage)
        self.playButton.connect("clicked", self.playToggled)
        self.hbox.pack_start(self.playButton, False, False, 5)

        self.slider = Gtk.Scale()
        self.slider.set_draw_value(False)
        self.slider.set_range(0, 100)
        self.slider.set_increments(1, 10)
        self.slider_handler_id = self.slider.connect("value-changed", self.on_slider_clicked)
        self.hbox.pack_start(self.slider, True, True, 5)

        self.label = Gtk.Label(label='0:00')
        self.hbox.pack_start(self.label, False, False, 5)

        self.fullscreenButtonImage = Gtk.Image()
        self.fullscreenButtonImage.set_from_icon_name(
            "gtk-fullscreen", Gtk.IconSize.BUTTON)
        self.fullscreenButton = Gtk.Button.new()
        self.fullscreenButton.add(self.fullscreenButtonImage)
        self.fullscreenButton.connect("clicked", self.fullscreenToggle)
        self.hboxMenu.pack_start(self.fullscreenButton, False, False, 5)

        self.separator = Gtk.HSeparator()
        self.vbox.pack_end(self.separator, False, False, 1)

        self.window.show_all()

        self.player = Gst.ElementFactory.make("playbin", "player")
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self.on_message)
        bus.connect("sync-message::element", self.on_sync_message)

    def on_keypress(self, widget, event):
        if event.keyval == Gdk.KEY_H or event.keyval == Gdk.KEY_h: 
            if (self.menuVisible):
                self.hbox.hide()
                self.menuVisible = False
            else:
                self.hbox.show()
                self.menuVisible = True

    def menu_clicked(self, widget):
        self.popover.set_relative_to(widget)
        self.popover.show_all()
        self.popover.popup()

    def fullscreenToggle(self, widget):
        if not self.isFullscreen:
            self.window.fullscreen()
            self.isFullscreen = True
        else:
            self.window.unfullscreen()
            self.isFullscreen = False

    def on_file_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(title="Open", parent=None,
                                       action=Gtk.FileChooserAction.OPEN,
                                       buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        self.add_filters(dialog)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.uri = dialog.get_filename()
        elif response == Gtk.ResponseType.CANCEL:
            print("Cancelled")

        dialog.destroy()

    def add_filters(self, dialog):
        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("MP4 Videos")
        filter_any.add_pattern("*.mp4")
        dialog.add_filter(filter_any)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("WEBM Videos")
        filter_any.add_pattern("*.webm")
        dialog.add_filter(filter_any)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("MKV Videos")
        filter_any.add_pattern("*.mkv")
        dialog.add_filter(filter_any)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("MP3 Audio")
        filter_any.add_pattern("*.mp3")
        dialog.add_filter(filter_any)

    def on_finished(self, player):
        self.playing = False
        self.slider.set_value(0)
        self.label.set_text("0:00")
        self.updateButtons()

    def play(self):
        self.player.set_property("uri", "file://" + self.uri)
        self.player.set_state(Gst.State.PLAYING)
        GLib.timeout_add(1000, self.updateSlider)

    def pause(self):
        self.player.set_state(Gst.State.PAUSED)

    def playToggled(self, w):
        if self.uri == "":
            print("No uri specified")
        else:
            if(self.playing == False):
                self.play()
            else:
                self.pause()

            self.playing = not(self.playing)
            self.updateButtons()

    def on_slider_clicked(self, widget):
        seek_time_secs = self.slider.get_value()
        self.player.seek_simple(Gst.Format.TIME,  Gst.SeekFlags.FLUSH |
                                Gst.SeekFlags.KEY_UNIT, seek_time_secs * Gst.SECOND)

    def updateSlider(self):
        if(self.playing == False):
            return False  # cancel timeout

        try:
            nanosecs = self.player.query_position(Gst.Format.TIME)[1]
            duration_nanosecs = self.player.query_duration(Gst.Format.TIME)[1]

            # block seek handler so we don't seek when we set_value()
            # self.slider.handler_block_by_func(self.on_slider_change)

            duration = float(duration_nanosecs) / Gst.SECOND
            position = float(nanosecs) / Gst.SECOND
            self.slider.set_range(0, duration)

            self.slider.handler_block(self.slider_handler_id)
            self.slider.set_value(int(position))
            self.slider.handler_unblock(self.slider_handler_id)

            self.label.set_text("%d" % (position / 60) +
                                ":%02d" % (position % 60))

            # self.slider.handler_unblock_by_func(self.on_slider_change)

        except Exception as e:
            # pipeline must not be ready and does not know position
            print("kjghgukg")
            print(e)
            pass

        return True

    def updateButtons(self):
        if(self.playing == False):
            self.playButtonImage.set_from_icon_name(
                "gtk-media-play", Gtk.IconSize.BUTTON)
        else:
            self.playButtonImage.set_from_icon_name(
                "gtk-media-pause", Gtk.IconSize.BUTTON)

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self.player.set_state(Gst.State.NULL)
            self.playing = False
        elif t == Gst.MessageType.ERROR:
            self.player.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            print("Error: %s" % err, debug)
            self.playing = False
        self.updateButtons()

    def on_sync_message(self, bus, message):
        if message.get_structure().get_name() == 'prepare-window-handle':
            imagesink = message.src
            imagesink.set_property("force-aspect-ratio", True)
            imagesink.set_window_handle(
                self.movie_window.get_property('window').get_xid())

Gst.init(None)
GTK_Main()
Gtk.main()