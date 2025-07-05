#!/usr/bin/env python3

# TODO event name only needed when compound clip (disable it?, or no hint)
# TODO export to csv,
# TODO check dep in UI
# TODO handle no scenes detected


import sys

from .fcpxml_markers import fcpxml_markers

try:
  import tkinter as tk
except ImportError:
  print('ERROR: tkinter not found')
  sys.exit(1)

import threading
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from fcpscene import __version__, __repo_url__, __title__, PROXY_WIDTH
from .time_utils import date_mdy
from .event_bus import EventBus
from .video_attr import VideoAttr
from .fcpxml_clips import fcpxml_clips
from .fcpxml_compound_clips import fcpxml_compound_clips
from .detect_scene_cut_times import detect_scene_cut_times, CutTimes


video_label = dict(x=30, y=25)
video_entry = dict(x=100, y=20, width=450)
video_browse_btn = dict(x=556, y=19)
video_hint = dict(x=101, y=46)

radio_compound_clips = dict(x=30, y=92)
radio_clips = dict(x=162, y=92)
radio_markers = dict(x=226, y=92)

sensitivity_label = dict(x=340, y=92)
sensitivity_slider = dict(x=414, y=92)
sensitivity_value = dict(x=625, y=92)

event_label = dict(x=340, y=130)
event_entry = dict(x=340, y=150, width=200)
event_hint = dict(x=340, y=175)

run_stop_btn = dict(x=30, y=150, width=140)

progress_width = 620
progress_height = 24
progress_track_color = '#888'
progress_color = '#304ffe'
progress_cut_color = '#fff'
progress_label = dict(x=30, y=202)
progress_canvas = dict(x=30, y=225)


class GUI:
  @staticmethod
  def run():
    root = tk.Tk()
    GUI(root)
    root.mainloop()


  def __init__(self, root):
    self.cuts = []
    self.v = VideoAttr('')

    self.root = root
    self.root.title(__title__)
    self.center_window(680, 270)
    self.root.resizable(False, False)
    self.root.focus_force()

    self.initial_dir = str(Path.home() / 'Movies')

    self.bus = EventBus()
    self.running = False

    self.setup_menus()

    self.render_video_picker()
    self.render_format_radio_buttons()
    self.render_sensitivity_slider()
    self.render_run_stop_button()
    self.render_event_name_textbox()
    self.render_progress_label()
    self.render_progress_timeline()

  def center_window(self, width, height):
    screen_width = self.root.winfo_screenwidth()
    screen_height = self.root.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    self.root.geometry(f'{width}x{height}+{x}+{y}')


  def setup_menus(self):
    def open_help():
      webbrowser.open(__repo_url__)

    def show_about():
      messagebox.showinfo(
        'About ms-fcpscene',
        f'ms-fcpscene {__version__}\n\n'
        f'{__repo_url__}\n\n'
        'Powered by FFmpeg')

    menubar = tk.Menu(self.root)
    helpmenu = tk.Menu(menubar, tearoff=0)
    helpmenu.add_command(label='README', command=open_help)
    helpmenu.add_command(label=f'About {__version__}', command=show_about)
    menubar.add_cascade(label='Help', menu=helpmenu)

    self.root.config(menu=menubar)


  def render_video_picker(self):
    def browse_file():
      file_path = filedialog.askopenfilename(
        title='Select Video File',
        initialdir=self.initial_dir,
        filetypes=[
          ('Final Cut Pro-Compatible Files', '*.mp4 *.mov *.avi *.m4v *.3gp *.3g2 *.mts *.m2ts *.mxf'),
          ('All files', '*.*')
        ])
      if file_path:
        self.initial_dir = str(Path(file_path).parent)
        self.video_entry.delete(0, tk.END)
        self.video_entry.insert(0, file_path)
        self.v = VideoAttr(file_path)

        if not self.v.error:
          self.video_hint.configure(text=self.v.summary)
          self.root.focus_force()
        else:
          messagebox.showerror('Error', self.v.error)

    ttk.Label(self.root, text='Video File').place(**video_label)
    self.video_entry = ttk.Entry(self.root)
    self.video_entry.place(**video_entry)
    ttk.Button(self.root, text='Browse', command=browse_file).place(**video_browse_btn)
    self.video_hint = ttk.Label(self.root, text='Place video in your Home or Movies directory')
    self.video_hint.place(**video_hint)


  def render_sensitivity_slider(self):
    ttk.Label(self.root, text='Sensitivity').place(**sensitivity_label)
    self.sensitivity_val = tk.IntVar(value=88)

    def on_slider_move(val):
      int_val = int(float(val))
      self.sensitivity_val.set(int_val)

    self.sensitivity_slider = ttk.Scale(
      self.root,
      from_=0,
      to=100,
      orient='horizontal',
      command=on_slider_move,
      value=88.0,
      length=202
    )
    self.sensitivity_slider.place(**sensitivity_slider)
    self.sensitivity_display = ttk.Label(self.root, textvariable=self.sensitivity_val)
    self.sensitivity_display.place(**sensitivity_value)


  def render_format_radio_buttons(self):
    self.format_val = tk.StringVar(value='compound')
    ttk.Radiobutton(
      self.root,
      text='Compound Clips',
      variable=self.format_val,
      value='compound'
    ).place(**radio_compound_clips)

    ttk.Radiobutton(
      self.root,
      text='Clips',
      variable=self.format_val,
      value='clips'
    ).place(**radio_clips)

    ttk.Radiobutton(
      self.root,
      text='Markers',
      variable=self.format_val,
      value='markers'
    ).place(**radio_markers)


  def render_run_stop_button(self):
    def on_click_run_stop():
      if self.running:
        self.bus.emit_stop()
        self.bus.unsubscribe_progress()
        self.run_stop_button.config(text='Stop and Save')
      else:
        self.run_scene_detect()
        self.run_stop_button.config(text='Run')

    self.run_stop_button = ttk.Button(
      self.root,
      text='Run',
      command=on_click_run_stop)
    self.run_stop_button.place(**run_stop_btn)


  def render_event_name_textbox(self):
    ttk.Label(self.root, text='Event Name').place(**event_label)
    self.event_name_val = tk.StringVar(value=date_mdy())
    self.event_name_entry = ttk.Entry(self.root, textvariable=self.event_name_val, width=18)
    self.event_name_entry.place(**event_entry)
    ttk.Label(self.root, text='Must exist in Library before importing').place(**event_hint)


  def render_progress_label(self):
    self.n_cuts = tk.IntVar()
    self.progress = tk.DoubleVar()
    self.progress_label = tk.StringVar()
    ttk.Label(self.root, textvariable=self.progress_label).place(**progress_label)

  def render_progress_timeline(self):
    self.progress_canvas = tk.Canvas(self.root, width=progress_width, height=progress_height, bg=progress_track_color,
                                     highlightthickness=0)
    self.progress_canvas.place(**progress_canvas)

  def set_progress_label(self, progress, n_cuts):
    self.progress.set(progress * 100)
    self.progress_label.set(f'{int(progress * 100)}% (Cuts {n_cuts})')

  def on_progress(self, progress: float, cuts: CutTimes):
    self.cuts = cuts
    self.set_progress_label(progress, len(cuts))
    self.update_progress_canvas(progress)
    self.root.update_idletasks()

  def update_progress_canvas(self, progress: float):
    self.progress_canvas.delete('all')
    self.progress_canvas.create_rectangle(0, 0, progress_width * progress, progress_height, fill=progress_color, outline='')
    for cut in self.cuts:
      x = cut / self.v.duration * progress_width
      self.progress_canvas.create_line(x, 0, x, progress_height, fill=progress_cut_color, width=1)


  def run_scene_detect(self):
    video = self.video_entry.get()
    if not video:
      messagebox.showinfo('No file', 'Please select a video file.')
      return

    sensitivity = float(self.sensitivity_val.get())

    self.set_progress_label(0, 0)
    self.bus.subscribe_progress(
      lambda *args: self.root.after(0, lambda: self.on_progress(*args)))

    def run():
      try:
        v = self.v
        self.running = True
        self.run_stop_button.config(text='Stop and Export')
        cut_times = detect_scene_cut_times(v, self.bus, sensitivity, PROXY_WIDTH)

        if self.format_val.get() == 'compound':
          xml = fcpxml_compound_clips(cut_times, v, self.event_name_val.get())
        elif self.format_val.get() == 'markers':
          xml = fcpxml_markers(cut_times, v)
        else:
          xml = fcpxml_clips(cut_times, v)

        self.bus.unsubscribe_progress()
        self.root.after(0, lambda: save_file(xml, Path(video).with_suffix('.fcpxml').name))
      except Exception as e:
        messagebox.showerror('Error', f'{e}')
      finally:
        self.running = False
        self.run_stop_button.config(text='Run')

    threading.Thread(target=run, daemon=True).start()


def save_file(xml, suggested_filename):
  file = filedialog.asksaveasfilename(
    defaultextension='.fcpxml',
    initialfile=suggested_filename,
    filetypes=[('Final Cut Pro XML', '*.fcpxml')])
  if file:
    try:
      with open(file, 'w', encoding='utf-8') as f:
        f.write(xml)
    except PermissionError as e:
      messagebox.showerror('Write Error', f'Permission denied:\n{e}')
    except OSError as e:
      messagebox.showerror('Write Error', f'Failed to write file:\n{e}')
