#!/usr/bin/env python3

import tempfile
import threading
import subprocess
import webbrowser
import tkinter as tk
from shutil import which
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from fcpscene import __version__, __repo_url__, __title__, PROXY_WIDTH, DEFAULT_SENSITIVITY, MIN_SCENE_SECS
from .ffmpeg import ffmpeg, ffprobe
from .event_bus import EventBus
from .video_attr import VideoAttr
from .to_csv_clips import to_csv_clips
from .to_fcpxml_clips import to_fcpxml_clips
from .to_fcpxml_markers import to_fcpxml_markers
from .to_fcpxml_compound_clips import to_fcpxml_compound_clips
from .detect_cuts import detect_cuts, TimelineStamps

root_win = dict(width=680, height=300)

sensitivity_slider_width = 150
sensitivity_label = dict(x=30, y=20)
sensitivity_slider = dict(x=103, y=18)
sensitivity_value = dict(x=260, y=20)

min_scene_secs_label = dict(x=366, y=20)
min_scene_secs_entry = dict(x=493, y=17)

video_label = dict(x=30, y=70)
video_entry = dict(x=102, y=65, width=450)
video_browse_btn = dict(x=556, y=65)
video_hint = dict(x=103, y=92)

radio_compound_clips = dict(x=197, y=140)
radio_clips = dict(x=329, y=140)
radio_markers = dict(x=392, y=140)

run_stop_btn = dict(x=30, y=170, width=76)
send_to_fcp_btn = dict(x=150, y=170, width=150)
export_as_fcp_btn = dict(x=310, y=170, width=200)
export_as_csv_btn = dict(x=520, y=170, width=130)

progress_label = dict(x=30, y=225)
hint_warning = dict(x=650, y=225)  # right aligned

progress_width = 620
progress_height = 24
progress_canvas = dict(x=30, y=248)
progress_track_color = '#888'
progress_color = '#304ffe'
progress_cut_color = '#fff'


class GUI:
  @staticmethod
  def run(video=None):
    root = tk.Tk()
    GUI(root, video)
    root.mainloop()

  @staticmethod
  def check_dependencies():
    if not which(ffmpeg):
      messagebox.showerror('Error', 'Dependency "ffmpeg" not found')
    elif not which(ffprobe):
      messagebox.showerror('Error', 'Dependency "ffprobe" not found')


  def __init__(self, root, video):
    self.check_dependencies()

    self.min_scene_secs = tk.StringVar(value=str(MIN_SCENE_SECS))

    self.root = root
    self.center_window()
    self.root.title(__title__)
    self.root.resizable(False, False)
    self.root.focus_force()

    self.v = VideoAttr('')
    self.bus = EventBus()
    self.stamps = []
    self.running = False
    self.initial_dir = str(Path.home() / 'Movies')

    self.setup_menus()

    self.render_sensitivity_slider()
    self.render_min_scene_seconds_entry()

    self.render_video_picker(video)
    self.render_mode_radio()

    self.render_run_stop_btn()
    self.render_send_to_fcp_btn()
    self.render_export_as_fcp_btn()
    self.render_export_as_csv_btn()

    self.render_progress_label()
    self.render_hint_warning()
    self.render_progress_timeline()


  def center_window(self):
    width = root_win['width']
    height = root_win['height']
    x = (self.root.winfo_screenwidth() - width) // 2
    y = (self.root.winfo_screenheight() - height) // 2
    self.root.geometry(f'{width}x{height}+{x}+{y}')


  def setup_menus(self):
    def open_help():
      webbrowser.open(__repo_url__)

    def show_about():
      messagebox.showinfo(
        'About fcpscene',
        f'fcpscene {__version__}\n\n'
        f'{__repo_url__}\n\n'
        'Powered by FFmpeg'
      )

    menubar = tk.Menu(self.root)
    help_menu = tk.Menu(menubar, tearoff=0)
    help_menu.add_command(label='README', command=open_help)
    help_menu.add_command(label=f'About {__version__}', command=show_about)
    menubar.add_cascade(label='Help', menu=help_menu)
    self.root.config(menu=menubar)


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
    ttk.Label(self.root, textvariable=self.sensitivity_val).place(**sensitivity_value)


  def render_min_scene_seconds_entry(self):
    def on_change(event=None):
      try:
        value = float(self.min_scene_secs.get())
        if value < 0:
          self.min_scene_secs.set(str(0))
      except ValueError as e:
        messagebox.showerror('Invalid Input', f'Invalid minimum scene seconds: {e}')
        self.min_scene_secs.set(str(MIN_SCENE_SECS))

    ttk.Label(self.root, text='Min Scene Seconds').place(**min_scene_secs_label)
    self.min_scene_secs_entry = ttk.Entry(
      self.root,
      textvariable=self.min_scene_secs,
      width=5
    )
    self.min_scene_secs_entry.place(**min_scene_secs_entry)
    self.min_scene_secs_entry.bind('<FocusOut>', on_change)
    self.min_scene_secs_entry.bind('<Return>', on_change)


  def render_video_picker(self, initial_video):
    def load_video(file_path):
      if not file_path or not Path(file_path).exists():
        return
      self.initial_dir = str(Path(file_path).parent)
      self.video_entry.delete(0, tk.END)
      self.video_entry.insert(0, file_path)
      self.v = VideoAttr(file_path)

      if self.v.error:
        messagebox.showerror('Error', self.v.error)
      else:
        self.video_hint.configure(text=self.v.summary)
        self.root.focus_force()
        self.run_scene_detect()

    def browse_file():
      file_path = filedialog.askopenfilename(
        title='Select Video File',
        initialdir=self.initial_dir,
        filetypes=[
          ('Final Cut Pro-Compatible Files', '*.mp4 *.mov *.avi *.m4v *.3gp *.3g2 *.mts *.m2ts *.mxf'),
          ('All files', '*.*')
        ])
      load_video(file_path)

    ttk.Label(self.root, text='Video File').place(**video_label)
    self.video_entry = ttk.Entry(self.root)
    self.video_entry.place(**video_entry)
    ttk.Button(self.root, text='Browse', command=browse_file).place(**video_browse_btn)
    self.video_hint = ttk.Label(self.root, text='Place video in your Home or Movies directory')
    self.video_hint.place(**video_hint)

    self.root.after(0, lambda: load_video(initial_video))


  def render_mode_radio(self):
    self.mode = tk.StringVar(value='compound')

    def on_mode_change(*args):
      self.handle_hint_warning(visible=self.mode.get() == 'compound')

    self.mode.trace_add('write', on_mode_change)

    ttk.Radiobutton(
      self.root,
      text='Compound Clips',
      variable=self.mode,
      value='compound'
    ).place(**radio_compound_clips)

    ttk.Radiobutton(
      self.root,
      text='Clips',
      variable=self.mode,
      value='clips'
    ).place(**radio_clips)

    ttk.Radiobutton(
      self.root,
      text='Markers',
      variable=self.mode,
      value='markers'
    ).place(**radio_markers)


  def render_run_stop_btn(self):
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
      if not self.stamps:
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
      if not self.stamps:
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
    if self.mode.get() == 'markers': return to_fcpxml_markers(self.stamps, self.v)
    if self.mode.get() == 'clips': return to_fcpxml_clips(self.stamps, self.v)
    return to_fcpxml_compound_clips(self.stamps, self.v)


  def render_export_as_csv_btn(self):
    def on_click():
      if not self.stamps:
        messagebox.showinfo('No cuts found', 'No scene changes were detected')
      else:
        csv = to_csv_clips(self.stamps)
        self.root.after(0, lambda: save_csv(csv, self.v.path.with_suffix('.csv').name))

    self.export_as_csv_btn = ttk.Button(
      self.root,
      text='Export as CSV',
      command=on_click)
    self.export_as_csv_btn.place(**export_as_csv_btn)

  def render_hint_warning(self):
    self.hint_warning = ttk.Label(
      self.root,
      text='Your Library must have an event called "fcpscene"')
    self.hint_warning.update_idletasks()
    hint_warning['x'] -= self.hint_warning.winfo_reqwidth()
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
    self.progress_canvas = tk.Canvas(
      self.root,
      width=progress_width,
      height=progress_height,
      bg=progress_track_color,
      highlightthickness=0
    )
    self.progress_canvas.place(**progress_canvas)

  def set_progress_label(self, progress, n_cuts):
    self.progress.set(progress * 100)
    self.progress_label.set(f'{int(progress * 100)}% (Cuts {n_cuts})')

  def on_progress(self, progress: float, stamps: TimelineStamps):
    self.stamps = stamps
    n_cuts = len(stamps) - 1 if progress != 1 else len(stamps) - 2
    self.set_progress_label(progress, max(n_cuts, 0))
    self.update_progress_canvas(progress)
    self.root.update_idletasks()

  def update_progress_canvas(self, progress: float):
    self.progress_canvas.delete('all')
    self.progress_canvas.create_rectangle(
      0, 0,
      progress_width * progress,
      progress_height,
      fill=progress_color,
      outline=''
    )
    cuts = self.stamps[1:] if progress != 1 else self.stamps[1:-1]
    for cut in cuts:
      x = cut / self.v.duration * progress_width
      self.progress_canvas.create_line(
        x, 0,
        x, progress_height,
        fill=progress_cut_color,
        width=1
      )


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
        self.stamps = []
        self.stamps = detect_cuts(v, self.bus, sensitivity, PROXY_WIDTH, float(self.min_scene_secs.get()))
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
