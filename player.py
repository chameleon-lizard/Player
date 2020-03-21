#!/usr/bin/env python3

# TODO: Networking

import sys
import gi

gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
gi.require_version('Gtk', '3.0')

from gi.repository import Gst, GObject, Gtk, GLib, Gdk
from gi.repository import GdkX11, GstVideo

class GTK_Main(object):

    def __init__(self):
        # Class variables
        self.updateTime = True
        self.playing = False
        if len(sys.argv) == 1:
            self.uri = ""
        else:
            self.uri = sys.argv[1]
        self.isFullscreen = False
        self.menuVisible = True

        # Window and its geometry
        geometry = Gdk.Geometry()
        geometry.min_width = 800
        geometry.min_height = 600
        geometry.base_width = -1
        geometry.base_height = -1
        geometry.width_inc = -1
        geometry.height_inc = -1
        self.window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        self.window.set_title("Player")
        self.window.set_default_size(800, 600)
        self.window.set_geometry_hints(self.window, geometry, Gdk.WindowHints.MIN_SIZE)
        self.window.connect("destroy", Gtk.main_quit, "WM destroy")
        self.window.connect('key-press-event', self.on_keypress)

        # Boxes for video and bar
        self.vbox = Gtk.VBox(homogeneous=False, spacing=2)
        self.window.add(self.vbox)
        self.hbox = Gtk.HBox(homogeneous=False, spacing=2)
        self.vbox.pack_start(self.hbox, False, False, 10)

        # Movie space and eventbox for it
        self.movie_window = Gtk.DrawingArea()
        self.eventbox = Gtk.EventBox.new()
        self.eventbox.set_above_child(False)
        self.eventbox.connect("button_press_event", self.movie_button_press)
        self.eventbox.add(self.movie_window)
        self.vbox.add(self.eventbox)
        self.eventbox.set_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.eventbox.realize()

        # Menu button
        self.menuButton = Gtk.Button.new()
        self.menuButtonImage = Gtk.Image()
        self.menuButtonImage.set_from_icon_name(
            "open-menu-symbolic", Gtk.IconSize.BUTTON)
        self.menuButton.add(self.menuButtonImage)
        self.menuButton.set_can_focus(False)
        self.menuButton.connect("clicked", self.menu_clicked)
        self.hbox.pack_end(self.menuButton, False, False, 5)        

        # Popover menu
        self.popover = Gtk.Popover()
        self.popover.set_border_width(10)
        self.hboxMenu = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.vboxMenu = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.popover.add(self.vboxMenu)
        self.vboxMenu.pack_start(self.hboxMenu, False, False, 5)
        self.popover.set_position(Gtk.PositionType.BOTTOM)

        # File chooser button for the popover menu
        self.fileChooser = Gtk.Button.new()
        self.fileChooserImage = Gtk.Image()
        self.fileChooserImage.set_from_icon_name(
            "gtk-file", Gtk.IconSize.BUTTON)
        self.fileChooser.add(self.fileChooserImage)
        self.fileChooser.set_can_focus(False)
        self.fileChooser.connect("clicked", self.on_file_clicked)
        self.hboxMenu.pack_start(self.fileChooser, False, False, 10)

        # Fullscreen button for the popover menu
        self.fullscreenButtonImage = Gtk.Image()
        self.fullscreenButtonImage.set_from_icon_name(
                "gtk-fullscreen", Gtk.IconSize.BUTTON)
        self.fullscreenButton = Gtk.Button.new()
        self.fullscreenButton.add(self.fullscreenButtonImage)
        self.fullscreenButton.set_can_focus(False)
        self.fullscreenButton.connect("clicked", self.fullscreenToggle)
        self.hboxMenu.pack_start(self.fullscreenButton, False, False, 10)

        # Connect button for the popover menu
        self.connectButtonImage = Gtk.Image()
        self.connectButtonImage.set_from_icon_name(
                "insert-link", Gtk.IconSize.BUTTON)
        self.connectButton = Gtk.Button.new()
        self.connectButton.add(self.connectButtonImage)
        self.connectButton.set_can_focus(False)
        self.connectButton.connect("clicked", self.connectDialog)
        self.hboxMenu.pack_start(self.connectButton, False, False, 10)

        # Label with info for the popover menu
        self.labelInfo = Gtk.Label(label="Press h to hide the bar")
        self.vboxMenu.pack_start(self.labelInfo, False, False, 5)

        # Seek left button for the bar
        self.seekLeftButtonImage = Gtk.Image()
        self.seekLeftButtonImage.set_from_icon_name(
            "media-seek-backward", Gtk.IconSize.BUTTON)
        self.seekLeftButton = Gtk.Button.new()
        self.seekLeftButton.add(self.seekLeftButtonImage)
        self.seekLeftButton.set_can_focus(False)
        self.seekLeftButton.connect("clicked", self.seek_left)
        self.hbox.pack_start(self.seekLeftButton, False, False, 5)

        # Play button for the bar
        self.playButtonImage = Gtk.Image()
        self.playButtonImage.set_from_icon_name(
            "gtk-media-play", Gtk.IconSize.BUTTON)
        self.playButton = Gtk.Button.new()
        self.playButton.add(self.playButtonImage)
        self.playButton.set_can_focus(False)
        self.playButton.connect("clicked", self.playToggled)
        self.hbox.pack_start(self.playButton, False, False, 5)

        # Seek left button for the bar
        self.seekRightButtonImage = Gtk.Image()
        self.seekRightButtonImage.set_from_icon_name(
            "media-seek-forward", Gtk.IconSize.BUTTON)
        self.seekRightButton = Gtk.Button.new()
        self.seekRightButton.add(self.seekRightButtonImage)
        self.seekRightButton.set_can_focus(False)
        self.seekRightButton.connect("clicked", self.seek_right)
        self.hbox.pack_start(self.seekRightButton, False, False, 5)

        # Slider for seeking
        self.slider = Gtk.Scale()
        self.slider.set_draw_value(False)
        self.slider.set_range(0, 100)
        self.slider.set_increments(1, 100)
        self.slider.set_can_focus(False)
        self.slider_handler_id = self.slider.connect("value-changed", self.on_slider_clicked)
        self.hbox.pack_start(self.slider, True, True, 5)

        # Time label
        self.label = Gtk.Label(label='0:00')
        self.hbox.pack_start(self.label, False, False, 5)

        # Showing all the stuff
        self.window.show_all()

        # GStreamer configuration
        self.player = Gst.ElementFactory.make("playbin", "player")
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect("message", self.on_message)
        bus.connect("sync-message::element", self.on_sync_message)

        # Start playing if the uri for the video was given via command line parameter
        if self.uri != "":
            self.updateTime = True
            self.playToggled(self.playButton)

    # Single and doubleclick on movie space
    def movie_button_press(self, widget, event):
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            self.fullscreenToggle(widget)
        elif event.type == Gdk.EventType.BUTTON_PRESS:
            if self.uri == "":
                self.on_file_clicked(widget)
            else:
                self.playToggled(widget)

    # For handling keyboard shortcuts
    def on_keypress(self, widget, event):
        if event.keyval == Gdk.KEY_H or event.keyval == Gdk.KEY_h: 
            if (self.menuVisible):
                self.hbox.hide()
                self.menuVisible = False
            else:
                self.hbox.show()
                self.menuVisible = True
        elif event.keyval == Gdk.KEY_Right:
            self.seek_right(widget)
        elif event.keyval == Gdk.KEY_Left:
            self.seek_left(widget)
        elif event.keyval == Gdk.KEY_space:
            self.playToggled(widget)
        elif event.keyval == Gdk.KEY_Escape:
            if self.isFullscreen:
                self.fullscreenToggle(widget)
            else:
                pass

    # Popup menu
    def menu_clicked(self, widget):
        self.popover.set_relative_to(widget)
        self.popover.show_all()
        self.popover.popup()

    # Toggling fullscreen
    def fullscreenToggle(self, widget):
        if widget == self.fullscreenButton:
            self.popover.popdown()

        if not self.isFullscreen:
            self.window.fullscreen()
            self.isFullscreen = True
            self.updateButtons()
        else:
            self.window.unfullscreen()
            self.isFullscreen = False
            self.updateButtons()

    # TODO: Connect dialog
    def connectDialog(self, widget):
        self.popover.popdown()

        dialog = Gtk.Dialog(title="Remote play", parent=self.window,
                                       modal=True, destroy_with_parent=False, 
                                       use_header_bar=True)
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        labelInfo = Gtk.Label(label="Please, connect to the server")

        ipEntry = Gtk.Entry()
        ipEntry.set_placeholder_text("IP address")

        passwordEntry = Gtk.Entry()
        passwordEntry.set_placeholder_text("Password")
        passwordEntry.set_invisible_char("•")
        passwordEntry.set_visibility(False)

        hbox.pack_start(ipEntry, False, False, 5)
        hbox.pack_start(passwordEntry, False, False, 5)
        dialog.vbox.pack_start(labelInfo, False, False, 5)
        dialog.vbox.pack_end(hbox, False, False, 10)

        dialog.add_button("OK", Gtk.ResponseType.OK)
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)

        dialog.show_all()

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            print("Connecting")
            self.ip = ipEntry.get_text()
            self.password = passwordEntry.get_text()
            print(self.ip, self.password)
        elif response == Gtk.ResponseType.CANCEL:
            print("Cancelled")

        dialog.destroy()

    # Creating file chooser dialog
    def on_file_clicked(self, widget):
        self.popover.popdown()
        self.player.set_state(Gst.State.PAUSED)
        dialog = Gtk.FileChooserDialog(title="Open", parent=self.window,
                                       action=Gtk.FileChooserAction.OPEN)
        dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        dialog.add_button(Gtk.STOCK_OPEN, Gtk.ResponseType.OK)

        self.add_filters(dialog)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            if self.uri != "":
                self.player.set_state(Gst.State.NULL)
                self.playing = False
            self.uri = dialog.get_filename()
            print(self.uri)
        elif response == Gtk.ResponseType.CANCEL:
            print("Cancelled")

        dialog.destroy()

        self.updateTime = True
        self.playToggled(widget)


    # Adding filters for file chooser dialog
    def add_filters(self, dialog):
        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any videos")
        filter_any.add_mime_type("video/*")
        dialog.add_filter(filter_any)

        filter_audio = Gtk.FileFilter()
        filter_audio.set_name("Any audio")
        filter_audio.add_mime_type("audio/*")
        dialog.add_filter(filter_audio)

    # If the video ends, this starts
    def on_finished(self, player):
        self.playing = False
        self.slider.set_value(0)
        self.label.set_text("0:00")
        self.updateButtons()

    # Called if we want to continue (or start) the video
    def play(self):
        self.player.set_property("uri", "file://" + self.uri)
        self.player.set_state(Gst.State.PLAYING)
        GLib.timeout_add(5, self.updateSlider)
        self.playing = True

    # Called if we want to pause the video
    def pause(self):
        self.player.set_state(Gst.State.PAUSED)
        self.playing = False

    # Called if we toggle the video
    def playToggled(self, w):
        if self.uri == "":
            print("No uri specified")
        else:
            if(self.playing == False):
                self.play()
            else:
                self.pause()

            self.updateButtons()

    # Called when we seek
    def on_slider_clicked(self, widget):
        if self.playing:
            self.pause()
            self.updateButtons()
        seek_time_secs = self.slider.get_value()
        self.player.seek_simple(Gst.Format.TIME,  Gst.SeekFlags.FLUSH |
                                Gst.SeekFlags.KEY_UNIT, seek_time_secs * Gst.SECOND)
        self.play()
        self.updateButtons()
        
    # Called when we seek left
    def seek_left(self, widget):
        seek_time_secs = self.player.query_position(Gst.Format.TIME)[1] / Gst.SECOND
        seek_time_secs -= 10
        if seek_time_secs <= 0:
            seek_time_secs = 0
        self.player.seek_simple(Gst.Format.TIME,  Gst.SeekFlags.FLUSH |
                                Gst.SeekFlags.KEY_UNIT, seek_time_secs * Gst.SECOND)
        self.updateSlider()

    # Called when we seek right
    def seek_right(self, widget):
        seek_time_secs = self.player.query_position(Gst.Format.TIME)[1] / Gst.SECOND
        seek_time_secs += 10
        if seek_time_secs >= self.player.query_duration(Gst.Format.TIME)[1] / Gst.SECOND:
            seek_time_secs = 0
            self.pause()
            self.updateButtons()
            self.updateSlider()
            return
            
        self.player.seek_simple(Gst.Format.TIME,  Gst.SeekFlags.FLUSH |
                                Gst.SeekFlags.KEY_UNIT, seek_time_secs * Gst.SECOND)
        self.updateSlider()

    # Called when the slider is updated
    def updateSlider(self):
        if self.updateTime:
            self.slider.set_increments(
                1, self.player.query_duration(Gst.Format.TIME)[1] / Gst.SECOND)
            self.slider.set_range(
                0, self.player.query_duration(Gst.Format.TIME)[1] / Gst.SECOND)

            self.updateTime = False
    
        if(self.playing == False):
            return False  # cancel timeout

        try:
            nanosecs = self.player.query_position(Gst.Format.TIME)[1]
            duration_nanosecs = self.player.query_duration(Gst.Format.TIME)[1]

            # block seek handler so we don't seek when we set_value()

            duration = float(duration_nanosecs) / Gst.SECOND
            position = float(nanosecs) / Gst.SECOND
            self.slider.set_range(0, duration)

            self.slider.handler_block(self.slider_handler_id)
            self.slider.set_value(int(position))
            self.slider.handler_unblock(self.slider_handler_id)

            self.slider.handler_block(self.slider_handler_id)
            self.slider.set_value(int(position))
            self.slider.handler_unblock(self.slider_handler_id)

            if position / 3600 < 1:
                self.label.set_text("%d" % (position / 60) +
                                    ":%02d" % (position % 60))
            else:
                self.label.set_text("%d:" % (position / 3600) +
                                    "%02d" % (position % 3600 / 60) +
                                    ":%02d" % (position % 60))

        except Exception as e:
            # pipeline must not be ready and does not know position
            print(e)
            pass

        return True

    # Updating the buttons
    def updateButtons(self):
        if not self.playing:
            self.playButtonImage.set_from_icon_name(
                "gtk-media-play", Gtk.IconSize.BUTTON)
        else:
            self.playButtonImage.set_from_icon_name(
                "gtk-media-pause", Gtk.IconSize.BUTTON)
        
        if self.isFullscreen:
            self.fullscreenButtonImage.set_from_icon_name(
                "view-restore", Gtk.IconSize.BUTTON)
        else:
            self.fullscreenButtonImage.set_from_icon_name(
                "gtk-fullscreen", Gtk.IconSize.BUTTON)

    # Called when we receive a message
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