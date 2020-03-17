#!/usr/bin/env python

import sys
import os
import gi

gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
gi.require_version('Gtk', '3.0')


from gi.repository import Gst, GObject, Gtk
from gi.repository import GdkX11, GstVideo

class GTK_Main(object):

    def __init__(self):
        self.playing = False
        self.uri = ""

        window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        window.set_title("Player")
        window.set_default_size(800, 600)
        window.connect("destroy", Gtk.main_quit, "WM destroy")
        vbox = Gtk.VBox(False, 2)
        window.add(vbox)
        hbox = Gtk.HBox(False, 2)
        vbox.pack_start(hbox, False, False, 10)

        self.movie_window = Gtk.DrawingArea()
        vbox.add(self.movie_window)

        self.file_chooser = Gtk.Button.new()
        self.file_chooser_image = Gtk.Image()
        self.file_chooser_image.set_from_stock(
            "gtk-file", Gtk.IconSize.BUTTON)
        self.file_chooser.add(self.file_chooser_image)
        self.file_chooser.connect("clicked", self.on_file_clicked)
        hbox.pack_start(self.file_chooser, False, False, 5)

        self.playButtonImage = Gtk.Image()
        self.playButtonImage.set_from_stock(
            "gtk-media-play", Gtk.IconSize.BUTTON)
        self.playButton = Gtk.Button.new()
        self.playButton.add(self.playButtonImage)
        self.playButton.connect("clicked", self.playToggled)
        hbox.pack_start(self.playButton, False, False, 5)

        self.slider = Gtk.HScale()
        self.slider.set_margin_left(6)
        self.slider.set_margin_right(6)
        self.slider.set_draw_value(False)
        self.slider.set_range(0, 100)
        self.slider.set_increments(1, 10)
        hbox.pack_start(self.slider, True, True, 5)

        self.label = Gtk.Label(label='0:00')
        self.label.set_margin_left(6)
        self.label.set_margin_right(6)
        hbox.pack_start(self.label, False, False, 5)

        window.show_all()

        self.player = Gst.ElementFactory.make("playbin", "player")
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self.on_message)
        bus.connect("sync-message::element", self.on_sync_message)

    def on_file_clicked(self, widget):
        dialog = Gtk.FileChooserDialog("Open", None,
                                       Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
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

    def on_finished(self, player):
        self.playing = False
        self.slider.set_value(0)
        self.label.set_text("0:00")
        self.updateButtons()

    def play(self):
        self.player.set_property("uri", "file://" + self.uri)
        self.player.set_state(Gst.State.PLAYING)
        GObject.timeout_add(1000, self.updateSlider)

    def stop(self):
        self.player.set_state(Gst.State.NULL)

    def playToggled(self, w):
        if self.uri == "":
            print("No uri specified")
        else:
            self.slider.set_value(0)
            self.label.set_text("0:00")

            if(self.playing == False):
                self.play()
            else:
                self.stop()

            self.playing = not(self.playing)
            self.updateButtons()

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
            self.slider.set_value(position)
            self.label.set_text("%d" % (position / 60) +
                                ":%02d" % (position % 60))

            # self.slider.handler_unblock_by_func(self.on_slider_change)

        except Exception as e:
            # pipeline must not be ready and does not know position
            print(e)
            pass

        return True

    def updateButtons(self):
        if(self.playing == False):
            self.playButtonImage.set_from_stock(
                "gtk-media-play", Gtk.IconSize.BUTTON)
        else:
            self.playButtonImage.set_from_stock(
                "gtk-media-stop", Gtk.IconSize.BUTTON)

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
