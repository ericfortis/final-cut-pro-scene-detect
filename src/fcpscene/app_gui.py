#!/usr/bin/env python3

import sys

try:
  import tkinter as tk
except ImportError:
  tk = None
  print('ERROR: tkinter not found')
  sys.exit(1)

import tempfile
import threading
import subprocess
import webbrowser
from shutil import which
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from fcpscene import __version__, __repo_url__, __title__, PROXY_WIDTH, DEFAULT_SENSITIVITY
from .event_bus import EventBus
from .video_attr import VideoAttr
from .to_csv_clips import to_csv_clips
from .to_fcpxml_clips import to_fcpxml_clips
from .to_fcpxml_markers import to_fcpxml_markers
from .to_fcpxml_compound_clips import to_fcpxml_compound_clips
from .detect_scene_cuts import detect_scene_cut_times, CutTimes


video_label = dict(x=30, y=25)
video_entry = dict(x=100, y=20, width=450)
video_browse_btn = dict(x=556, y=19)
video_hint = dict(x=101, y=46)

radio_compound_clips = dict(x=30, y=92)
radio_clips = dict(x=162, y=92)
radio_markers = dict(x=226, y=92)

sensitivity_label = dict(x=380, y=92)
sensitivity_slider_width = 164
sensitivity_slider = dict(x=456, y=92)
sensitivity_value = dict(x=630, y=92)

run_stop_btn = dict(x=30, y=140, width=80)
send_to_fcp_btn = dict(x=150, y=140, width=150)
export_as_fcp_btn = dict(x=310, y=140, width=200)
export_as_csv_btn = dict(x=520, y=140, width=130)

progress_label = dict(x=30, y=195)
hint_warning = dict(x=210, y=195)

progress_width = 620
progress_height = 24
progress_track_color = '#888'
progress_color = '#304ffe'
progress_cut_color = '#fff'
progress_canvas = dict(x=30, y=218)


class GUI:
  @staticmethod
  def run():
    root = tk.Tk()
    GUI(root)
    root.mainloop()

  @staticmethod
  def check_dependencies():
    if not which('ffmpeg'):
      messagebox.showerror('Error', 'Dependency "ffmpeg" not found')
    elif not which('ffprobe'):
      messagebox.showerror('Error', 'Dependency "ffprobe" not found')

  def __init__(self, root):
    self.cuts = []
    self.check_dependencies()
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
    self.render_send_to_fcp_btn()
    self.render_export_as_fcp_btn()
    self.render_export_as_csv_btn()

    self.render_progress_label()
    self.render_hint_warning()
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
        'About fcpscene',
        f'fcpscene {__version__}\n\n'
        f'{__repo_url__}\n\n'
        'Powered by FFmpeg')

    menubar = tk.Menu(self.root)
    help_menu = tk.Menu(menubar, tearoff=0)
    help_menu.add_command(label='README', command=open_help)
    help_menu.add_command(label=f'About {__version__}', command=show_about)
    menubar.add_cascade(label='Help', menu=help_menu)

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
          self.run_scene_detect()
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
    self.sensitivity_val = tk.IntVar(value=DEFAULT_SENSITIVITY)

    def on_slider_move(val):
      int_val = int(float(val))
      self.sensitivity_val.set(int_val)

    self.sensitivity_slider = ttk.Scale(
      self.root,
      from_=0,
      to=100,
      orient='horizontal',
      command=on_slider_move,
      value=DEFAULT_SENSITIVITY,
      length=sensitivity_slider_width
    )
    self.sensitivity_slider.place(**sensitivity_slider)
    self.sensitivity_display = ttk.Label(self.root, textvariable=self.sensitivity_val)
    self.sensitivity_display.place(**sensitivity_value)


  def render_format_radio_buttons(self):
    self.format_val = tk.StringVar(value='compound')

    def on_format_change(*args):
      self.handle_hint_warning(visible=self.format_val.get() == 'compound')
    self.format_val.trace_add('write', on_format_change)

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
        self.run_stop_button.config(text='Stop')
      else:
        self.run_scene_detect()
        self.run_stop_button.config(text='Run')

    self.run_stop_button = ttk.Button(
      self.root,
      text='Run',
      command=on_click_run_stop)
    self.run_stop_button.place(**run_stop_btn)


  def render_send_to_fcp_btn(self):
    def on_click():
      if not self.cuts:
        messagebox.showinfo('No cuts found', 'No scene changes were detected')
      else:
        xml = self.process_fcpxml()
        self.root.after(0, lambda: save_and_send(xml))

    self.send_to_fcp_btn = ttk.Button(
      self.root,
      text='Send to Final Cut',
      command=on_click)
    self.send_to_fcp_btn.place(**send_to_fcp_btn)


  def render_export_as_fcp_btn(self):
    def on_click():
      if not self.cuts:
        messagebox.showinfo('No cuts found', 'No scene changes were detected')
      else:
        xml = self.process_fcpxml()
        self.root.after(0, lambda: save_fcpxml(xml, self.v.path.with_suffix('.fcpxml').name))

    self.export_as_fcp_btn = ttk.Button(
      self.root,
      text='Export as Final Cut Project',
      command=on_click)
    self.export_as_fcp_btn.place(**export_as_fcp_btn)


  def process_fcpxml(self):
    if self.format_val.get() == 'compound':
      return to_fcpxml_compound_clips(self.cuts, self.v)
    if self.format_val.get() == 'markers':
      return to_fcpxml_markers(self.cuts, self.v)
    return to_fcpxml_clips(self.cuts, self.v)


  def render_export_as_csv_btn(self):
    def on_click():
      if not self.cuts:
        messagebox.showinfo('No cuts found', 'No scene changes were detected')
      else:
        csv = to_csv_clips(self.cuts, self.v.duration)
        self.root.after(0, lambda: save_csv(csv, self.v.path.with_suffix('.csv').name))

    self.export_as_csv_btn = ttk.Button(
      self.root,
      text='Export as CSV',
      command=on_click)
    self.export_as_csv_btn.place(**export_as_csv_btn)

  def render_hint_warning(self):
    self.hint_warning = ttk.Label(
      self.root,
      text='Your Library must have an event called "fcpscene" (for compound clips)')
    self.hint_warning.place(**hint_warning)

  def handle_hint_warning(self, visible):
    if visible:
      self.hint_warning.place(**hint_warning)
    else:
      self.hint_warning.place_forget()

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
    self.progress_canvas.create_rectangle(0, 0, progress_width * progress, progress_height, fill=progress_color,
                                          outline='')
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
        self.on_progress(0, [])
        self.sensitivity_slider.config(state='disabled')
        self.run_stop_button.config(text='Stop')
        self.cuts = []
        self.cuts = detect_scene_cut_times(v, self.bus, sensitivity, PROXY_WIDTH)
        self.bus.unsubscribe_progress()
      except Exception as e:
        messagebox.showerror('Error', f'{e}')
      finally:
        self.running = False
        self.sensitivity_slider.config(state='normal')
        self.run_stop_button.config(text='Run')

    threading.Thread(target=run, daemon=True).start()


def save_fcpxml(xml, suggested_filename):
  file = filedialog.asksaveasfilename(
    defaultextension='.fcpxml',
    initialfile=suggested_filename,
    filetypes=[('Final Cut Pro XML', '*.fcpxml')])
  if file:
    write(xml, file)


def save_csv(csv, suggested_filename):
  file = filedialog.asksaveasfilename(
    defaultextension='.csv',
    initialfile=suggested_filename,
    filetypes=[('CSV', '*.csv')])
  if file:
    write(csv, file)


def save_and_send(xml):
  with tempfile.NamedTemporaryFile(suffix='.fcpxml', dir='/tmp', delete=False) as tmp:
    write(xml, tmp.name)
    try:
      subprocess.run([
        'open',
        str(tmp.name)
      ])
    except Exception as e:
      messagebox.showerror('Open FCP Error', f'Failed to send project to Final Cut:\n{e}')


def write(txt, filename):
  try:
    with open(filename, 'w', encoding='utf-8') as f:
      f.write(txt)
  except PermissionError as e:
    messagebox.showerror('Write Error', f'Permission denied:\n{e}')
  except Exception as e:
    messagebox.showerror('Write Error', f'Failed to write file:\n{e}')
