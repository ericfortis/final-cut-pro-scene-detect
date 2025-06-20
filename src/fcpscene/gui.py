#!/usr/bin/env python3

import sys

try:
  import tkinter as tk
except ImportError:
  print('ERROR: tkinter not found')
  sys.exit(1)

import threading
import webbrowser
from tkinter import filedialog, messagebox, scrolledtext, ttk
from pathlib import Path

from fcpscene.utils import format_seconds
from fcpscene.event_bus import EventBus
from fcpscene.scenes_to_fcp import scenes_to_fcp, __version__


class GUI:
  @staticmethod
  def run():
    root = tk.Tk()
    GUI(root)
    root.mainloop()


  def __init__(self, root):
    self.root = root
    self.bus = EventBus()

    self.running = False

    self.root.title('Final Cut Pro Scene Detect')
    self.root.resizable(False, False)
    self.last_browsed_dir = str(Path.home() / 'Movies')

    self.setup_menus()

    self.render_video_picker()
    self.render_sensitivity_slider()
    self.render_run_stop_button()
    self.render_progress_bar()
    self.render_cuts_list()


  def setup_menus(self):
    def open_help():
      webbrowser.open('https://github.com/ericfortis/final-cut-pro-scene-detect')

    def show_about():
      messagebox.showinfo(
        'About fcpscene',
        f'fcpscene {__version__}\n\n'
        'Dependencies: FFmpeg\n\n'
        'Source Code\n'
        'https://github.com/ericfortis/final-cut-pro-scene-detect'
      )

    menubar = tk.Menu(self.root)
    helpmenu = tk.Menu(menubar, tearoff=0)
    helpmenu.add_command(label='README', command=open_help)
    helpmenu.add_command(label=f'About {__version__}', command=show_about)
    menubar.add_cascade(label='Help', menu=helpmenu)

    self.root.config(menu=menubar)


  def render_video_picker(self):
    ttk.Label(self.root, text='Video File:').grid(row=0, padx=(10, 0), pady=(10, 0), sticky='w')
    self.video_entry = ttk.Entry(self.root, width=43)
    self.video_entry.grid(row=0, column=1, padx=(0, 0), pady=(10, 0), sticky='w')
    ttk.Button(self.root, text='Browse', command=self.browse_file).grid(row=0, column=2, padx=(0, 10), pady=(10, 0))

  def browse_file(self):
    file_path = filedialog.askopenfilename(
      title='Select Video File',
      initialdir=self.last_browsed_dir,
      filetypes=[
      ('Final Cut Pro-Compatible Files', '*.mp4 *.mov *.avi *.m4v *.3gp *.3g2 *.mts *.m2ts *.mxf'),
      ('All files', '*.*')
    ])
    if file_path:
      self.last_browsed_dir = str(Path(file_path).parent)
      self.video_entry.delete(0, tk.END)
      self.video_entry.insert(0, file_path)


  def render_sensitivity_slider(self):
    ttk.Label(self.root, text='Sensitivity:').grid(row=1, column=0, padx=(10, 0), pady=(10, 0), sticky='w')
    self.sensitivity_frame = ttk.Frame(self.root)
    self.sensitivity_frame.grid(row=1, column=1, columnspan=3, sticky='w', padx=0, pady=(10, 0))
    self.sensitivity_val = tk.IntVar(value=85)

    def on_slider_move(val):
      int_val = int(float(val))
      self.sensitivity_val.set(int_val)

    self.sensitivity_slider = ttk.Scale(
      self.sensitivity_frame,
      from_=0,
      to=100,
      orient='horizontal',
      command=on_slider_move,
      value=85.0,
      length=150
    )
    self.sensitivity_slider.pack(side='left')
    self.sensitivity_display = ttk.Label(self.sensitivity_frame, textvariable=self.sensitivity_val, width=3)
    self.sensitivity_display.pack(side='left')


  def render_run_stop_button(self):
    self.run_stop_button = ttk.Button(
      self.sensitivity_frame,
      text='Run',
      command=self.on_click_run_stop,
      width=15
    )
    self.run_stop_button.pack(side='left', padx=(80, 10), pady=(0, 0))

  def on_click_run_stop(self):
    if self.running:
      self.bus.emit_stop()
      self.bus.unsubscribe_progress()
      self.run_stop_button.config(text='Stop and Save')
    else:
      self.run_scene_detect()
      self.run_stop_button.config(text='Run')


  def render_progress_bar(self):
    self.n_cuts = tk.IntVar()
    self.progress = tk.DoubleVar()
    self.progress_label = tk.StringVar()
    ttk.Label(self.root, textvariable=self.progress_label).grid(row=4, column=1, pady=(10, 0))
    self.progress_bar = ttk.Progressbar(self.root, maximum=100, variable=self.progress, length=400)
    self.progress_bar.grid(row=5, column=0, columnspan=3)

  def set_progress(self, progress, n_cuts):
    self.progress.set(progress * 100)
    self.progress_label.set(f'{int(progress * 100)}% (Cuts {n_cuts})')


  def render_cuts_list(self):
    self.log_box = scrolledtext.ScrolledText(self.root, height=10)
    self.log_box.grid(row=6, column=0, columnspan=3, padx=10, pady=(5, 10))

  def update_cuts_list(self, cut_time: float, video_duration: float, n_cuts: int):
    progress = cut_time / video_duration
    self.set_progress(progress, n_cuts)
    self.log_box.insert(tk.END, f'{format_seconds(cut_time)} ')
    self.root.update_idletasks()


  def run_scene_detect(self):
    video = self.video_entry.get()
    if not video:
      messagebox.showinfo('No file', 'Please select a video file.')
      return

    sensitivity = float(self.sensitivity_val.get())

    self.log_box.delete(1.0, tk.END)
    self.set_progress(0, 0)

    self.bus.subscribe_progress(
      lambda *args: self.root.after(0, lambda: self.update_cuts_list(*args)))

    def run():
      try:
        self.running = True
        self.run_stop_button.config(text='Stop and Save')
        xml = scenes_to_fcp(video, self.bus, sensitivity)
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
    filetypes=[('Final Cut Pro XML', '*.fcpxml')]
  )
  if file:
    with open(file, 'w', encoding='utf-8') as f:
      f.write(xml)


if __name__ == '__main__':
  GUI.run()
