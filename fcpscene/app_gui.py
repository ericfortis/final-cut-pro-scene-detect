#!/usr/bin/env python3

import json
import tempfile
import threading
import subprocess
import webbrowser
import tkinter as tk
from enum import Enum
from shutil import which
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from dataclasses import dataclass

from fcpscene import __version__, __repo_url__, __title__, PROXY_WIDTH, DEFAULT_SENSITIVITY, MIN_SCENE_SECS
from .utils import debounce
from .ffmpeg import ffmpeg, ffprobe
from .event_bus import EventBus
from .video_attr import VideoAttr
from .to_csv_clips import to_csv_clips
from .to_fcpxml_clips import to_fcpxml_clips
from .to_fcpxml_markers import to_fcpxml_markers
from .to_fcpxml_compound_clips import to_fcpxml_compound_clips
from .detect_scene_changes import detect_scene_changes, CutTimes, count_scenes


class ExportMode(str, Enum):
  CLIPS = 'clips'
  MARKERS = 'markers'
  COMPOUND_CLIPS = 'compound-clips'


class LastUsed:
  def __init__(self):
    self.dir = str(Path.home() / 'Movies')
    self.mode = ExportMode.CLIPS.value
    self.sensitivity = DEFAULT_SENSITIVITY
    self.min_scene_seconds = str(MIN_SCENE_SECS)

    self.settings = Path.home() / '.config' / 'fcpscene' / 'last-used.json'
    settings = self.read_settings()
    if settings:
      last_used_dir = settings.get('dir')
      if last_used_dir and Path(last_used_dir).is_dir():
        self.dir = last_used_dir

      mode = settings.get('mode')
      if mode in ExportMode._value2member_map_:
        self.mode = mode

      try:
        s = int(settings.get('sensitivity'))
        if 0 <= s <= 100:
          self.sensitivity = s
      except (TypeError, ValueError):
        pass

      try:
        mss = float(settings.get('min_scene_seconds'))
        if mss >= 0:
          self.min_scene_seconds = str(mss)
      except (TypeError, ValueError):
        pass


  def read_settings(self):
    try:
      with open(self.settings, 'r') as f:
        return json.load(f)
    except Exception:
      return None


  def save_dir(self, value):
    self.dir = value
    self.save()

  def save_mode(self, value):
    self.mode = value
    self.save()

  def save_sensitivity(self, value):
    self.sensitivity = value
    self.save()

  def save_min_scene_seconds(self, value):
    self.min_scene_seconds = value
    self.save()

  @debounce(0.5)
  def save(self):
    try:
      self.settings.parent.mkdir(parents=True, exist_ok=True)
      with open(self.settings, 'w') as f:
        json.dump({
          'dir': self.dir,
          'mode': self.mode,
          'sensitivity': self.sensitivity,
          'min_scene_seconds': self.min_scene_seconds,
        }, f)
    except Exception:
      pass


@dataclass
class Style:
  root_win = dict(width=680, height=300)

  sensitivity_slider_width = 185
  sensitivity_label = dict(x=30, y=20)
  sensitivity_slider = dict(x=105, y=18)
  sensitivity_value = dict(x=295, y=19)

  min_scene_secs_label = dict(x=366, y=20)
  min_scene_secs_entry = dict(x=493, y=17)

  video_label = dict(x=30, y=70)
  video_entry = dict(x=102, y=65, width=450)
  video_browse_btn = dict(x=556, y=64)
  video_hint = dict(x=103, y=92)

  radio_clips = dict(x=205, y=143)
  radio_compound_clips = dict(x=265, y=143)
  radio_markers = dict(x=397, y=143)

  run_stop_btn = dict(x=30, y=170, width=96)
  send_to_fcp_btn = dict(x=154, y=170, width=146)
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


style = Style()


class GUI:
  @staticmethod
  def run(video=None):
    root = tk.Tk()
    GUI(root, video)
    root.mainloop()

  def __init__(self, root, video):
    check_dependencies()

    self.last_used = LastUsed()
    self.dir = self.last_used.dir
    self.mode = tk.StringVar(value=self.last_used.mode)
    self.sensitivity_val = tk.IntVar(value=self.last_used.sensitivity)
    self.min_scene_secs = tk.StringVar(value=self.last_used.min_scene_seconds)

    self.root = root
    self.center_window()
    self.root.title(__title__)
    self.root.resizable(False, False)
    self.root.focus_force()

    self.v = VideoAttr('')
    self.bus = EventBus()
    self.cuts = []
    self.running = False

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
    width = style.root_win['width']
    height = style.root_win['height']
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


  def Label(self, styl, **kwargs):
    el = ttk.Label(self.root, **kwargs)
    el.place(**styl)
    return el

  def Button(self, styl, **kwargs):
    el = ttk.Button(self.root, **kwargs)
    el.place(**styl)
    return el


  def render_sensitivity_slider(self):
    self.Label(style.sensitivity_label, text='Sensitivity')

    ttk.Scale(
      self.root,
      from_=0,
      to=100,
      orient='horizontal',
      command=self.act_change_sensitivity,
      value=self.sensitivity_val.get(),
      length=style.sensitivity_slider_width
    ).place(**style.sensitivity_slider)

    self.Label(style.sensitivity_value, textvariable=self.sensitivity_val)

  def act_change_sensitivity(self, val):
    int_val = int(float(val))
    self.sensitivity_val.set(int_val)
    self.stop_scene_detect()
    self.root.after(0, lambda: self.last_used.save_sensitivity(int_val))


  def render_min_scene_seconds_entry(self):
    self.Label(style.min_scene_secs_label, text='Min Scene Seconds')
    self.min_scene_secs_entry = ttk.Entry(
      self.root,
      textvariable=self.min_scene_secs,
      width=5
    )
    self.min_scene_secs_entry.place(**style.min_scene_secs_entry)
    self.min_scene_secs_entry.bind('<FocusOut>', self.act_change_min_scene_seconds)
    self.min_scene_secs_entry.bind('<Return>', self.act_change_min_scene_seconds)

  def act_change_min_scene_seconds(self, event=None):
    try:
      value = float(self.min_scene_secs.get())
      if value < 0:
        self.min_scene_secs.set(str(0))
      self.stop_scene_detect()
      self.root.after(0, lambda: self.last_used.save_min_scene_seconds(self.min_scene_secs.get()))
    except ValueError as e:
      self.min_scene_secs.set(self.last_used.min_scene_seconds)
      messagebox.showerror('Invalid Input', f'Invalid minimum scene seconds: {e}')


  def render_video_picker(self, initial_video):
    def load_video(file_path):
      if not file_path or not Path(file_path).exists():
        return
      self.dir = str(Path(file_path).parent)
      self.video_entry.delete(0, tk.END)
      self.video_entry.insert(0, file_path)
      self.v = VideoAttr(file_path)

      if self.v.error:
        messagebox.showerror('Error', self.v.error)
      else:
        self.video_hint.configure(text=self.v.summary)
        self.root.focus_force()
        self.run_scene_detect()

      self.root.after(0, lambda: self.last_used.save_dir(self.dir))

    def browse_file():
      file_path = filedialog.askopenfilename(
        title='Select Video File',
        initialdir=self.dir,
        filetypes=[
          ('Final Cut Pro-Compatible Files', '*.mp4 *.mov *.avi *.m4v *.3gp *.3g2 *.mts *.m2ts *.mxf'),
          ('All files', '*.*')
        ])
      load_video(file_path)

    self.Label(style.video_label, text='Video File')
    self.video_entry = ttk.Entry(self.root)
    self.video_entry.place(**style.video_entry)
    self.Button(style.video_browse_btn, text='Browse', command=browse_file)
    self.video_hint = self.Label(style.video_hint, text='Place video in your Home or Movies directory')

    self.root.after(0, lambda: load_video(initial_video))


  def render_mode_radio(self):
    self.mode.trace_add('write', self.act_change_mode)
    ttk.Radiobutton(
      self.root,
      text='Clips',
      value=ExportMode.CLIPS.value,
      variable=self.mode,
    ).place(**style.radio_clips)

    ttk.Radiobutton(
      self.root,
      text='Compound Clips',
      value=ExportMode.COMPOUND_CLIPS.value,
      variable=self.mode,
    ).place(**style.radio_compound_clips)

    ttk.Radiobutton(
      self.root,
      text='Markers',
      value=ExportMode.MARKERS.value,
      variable=self.mode,
    ).place(**style.radio_markers)

  def act_change_mode(self, *args):
    self.handle_hint_warning(visible=self.mode.get() == ExportMode.COMPOUND_CLIPS.value)
    self.root.after(0, lambda: self.last_used.save_mode(self.mode.get()))


  def render_run_stop_btn(self):
    self.run_stop_button = self.Button(
      style.run_stop_btn,
      text='▶ Run',
      command=self.act_toggle_run_stop)

  def act_toggle_run_stop(self):
    if self.running:
      self.stop_scene_detect()
    else:
      self.run_scene_detect()


  def render_send_to_fcp_btn(self):
    self.Button(
      style.send_to_fcp_btn,
      text='Send to Final Cut',
      command=self.act_send_to_fcp)

  def act_send_to_fcp(self):
    if not self.cuts:
      messagebox.showinfo('No cuts found', 'No scene changes were detected')
    else:
      xml = self.process_fcpxml()
      self.root.after(0, lambda: save_and_send(xml))


  def render_export_as_fcp_btn(self):
    self.Button(
      style.export_as_fcp_btn,
      text='Export as Final Cut Project',
      command=self.act_export_as_fcp)

  def act_export_as_fcp(self):
    if not self.cuts:
      messagebox.showinfo('No cuts found', 'No scene changes were detected')
    else:
      xml = self.process_fcpxml()
      self.root.after(0, lambda: save_fcpxml(xml, self.v.path.with_suffix('.fcpxml').name))


  def render_export_as_csv_btn(self):
    self.Button(
      style.export_as_csv_btn,
      text='Export as CSV',
      command=self.act_export_as_csv)

  def act_export_as_csv(self):
    if not self.cuts:
      messagebox.showinfo('No cuts found', 'No scene changes were detected')
    else:
      csv = to_csv_clips(self.cuts)
      self.root.after(0, lambda: save_csv(csv, self.v.path.with_suffix('.csv').name))


  def process_fcpxml(self):
    if self.mode.get() == ExportMode.MARKERS.value: return to_fcpxml_markers(self.cuts, self.v)
    if self.mode.get() == ExportMode.COMPOUND_CLIPS.value: return to_fcpxml_compound_clips(self.cuts, self.v)
    return to_fcpxml_clips(self.cuts, self.v)

  def render_hint_warning(self):
    self.hint_warning = self.Label(style.hint_warning, text='Your Library must have an event called "fcpscene"')
    self.hint_warning.update_idletasks()
    style.hint_warning['x'] -= self.hint_warning.winfo_reqwidth()
    self.handle_hint_warning(self.mode.get() == ExportMode.COMPOUND_CLIPS.value)

  def handle_hint_warning(self, visible):
    if visible:
      self.hint_warning.place(**style.hint_warning)
    else:
      self.hint_warning.place_forget()

  def render_progress_label(self):
    self.n_cuts = tk.IntVar()
    self.progress = tk.DoubleVar()
    self.progress_label = tk.StringVar()
    self.Label(style.progress_label, textvariable=self.progress_label)

  def render_progress_timeline(self):
    self.progress_canvas = tk.Canvas(
      self.root,
      width=style.progress_width,
      height=style.progress_height,
      bg=style.progress_track_color,
      highlightthickness=0
    )
    self.progress_canvas.place(**style.progress_canvas)

  def set_progress_label(self, progress, n_scenes):
    self.progress.set(progress * 100)
    self.progress_label.set(f'{int(progress * 100)}% ({n_scenes} Scenes)')

  def on_progress(self, progress: float, cuts: CutTimes):
    self.cuts = cuts
    self.set_progress_label(progress, max(count_scenes(cuts, progress), 0))
    self.update_progress_canvas(progress)
    self.root.update_idletasks()

  def update_progress_canvas(self, progress: float):
    self.progress_canvas.delete('all')
    self.progress_canvas.create_rectangle(
      0, 0,
      style.progress_width * progress,
      style.progress_height,
      fill=style.progress_color,
      outline=''
    )
    cuts = self.cuts[1:] if progress != 1 else self.cuts[1:-1]
    for cut in cuts:
      x = cut / self.v.duration * style.progress_width
      self.progress_canvas.create_line(
        x, 0,
        x, style.progress_height,
        fill=style.progress_cut_color,
        width=1
      )

  def stop_scene_detect(self):
    self.bus.emit_stop()
    self.bus.unsubscribe_progress()

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
        self.run_stop_button.config(text='🛑 Stop')
        self.cuts = []
        self.cuts = detect_scene_changes(v, self.bus, sensitivity, PROXY_WIDTH, float(self.min_scene_secs.get()))
        self.bus.unsubscribe_progress()
      except Exception as e:
        messagebox.showerror('Error', f'{e}')
      finally:
        self.running = False
        self.run_stop_button.config(text='▶ Run')

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


def check_dependencies():
  if not which(ffmpeg):
    messagebox.showerror('Error', 'Dependency "ffmpeg" not found')
  elif not which(ffprobe):
    messagebox.showerror('Error', 'Dependency "ffprobe" not found')
