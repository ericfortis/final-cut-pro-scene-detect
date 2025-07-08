import re
from signal import SIGINT
from subprocess import Popen, PIPE

from .ffmpeg import ffmpeg
from .event_bus import EventBus


CutTimes = list[float]
"""Seconds where scene changes were detected"""


def detect_scene_cut_times(v, bus, sensitivity, proxy_width) -> CutTimes:
  """Finds the timestamps of scene changes using FFmpeg

  Video filter chain:
    - `scale`: For speed. Downscales video to `proxy_width` in aspect ratio
    - `select`: if scene-change-probability > threshold
    - `metadata`: Writes the selected frame timestamp to stderr

  Args:
      v (VideoAttr):
      bus (EventBus): For listening to a UI stop signal and reporting progress
      sensitivity (float): 0 to 100; inversely mapped to the scene-change threshold
      proxy_width (int): Width in pixels for downscaling video
  """

  cut_time_regex = re.compile(r'Parsed_metadata.*pts_time:(\d+\.?\d*)')

  cmd = [
    ffmpeg,
    '-hide_banner',
    '-an',  # Don’t process audio
    '-i', v.path,
    '-vf', ','.join([
      f'scale={proxy_width}:-1',
      f"select='gt(scene, {1 - sensitivity / 100})'",
      'metadata=print'
    ]),
    '-f', 'null', '-',  # Don’t generate an output video
  ]

  cuts = []
  stderr_buffer = []
  stopped_from_ui = False

  try:
    with Popen(cmd, stdout=PIPE, stderr=PIPE, text=True) as process:
      def on_stop_from_ui():
        if process and process.poll() is None:
          nonlocal stopped_from_ui
          stopped_from_ui = True
          process.send_signal(SIGINT)

      bus.subscribe_stop(on_stop_from_ui)

      for line in process.stderr:  # while stderr is open
        stderr_buffer.append(line)
        match = cut_time_regex.search(line)
        if match:
          try:
            cut_time = float(match.group(1))
            cuts.append(cut_time)
            bus.emit_progress(cut_time / v.duration, cuts)
          except ValueError:
            pass

      process.wait()
      bus.emit_progress(1, cuts)

      if not stopped_from_ui and process.returncode != 0:
        raise RuntimeError(''.join(stderr_buffer))

      return cuts
  except KeyboardInterrupt:  # Ctrl+C terminates analysis, and we create a file with the progress so far
    if process:
      process.terminate()
  except Exception:
    raise
  finally:
    bus.unsubscribe_stop()
