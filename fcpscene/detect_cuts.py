import re
from signal import SIGINT
from subprocess import Popen, PIPE

from .ffmpeg import ffmpeg
from .event_bus import EventBus


TimelineStamps = list[float]
"""[Start + [SceneChanges] + End] in seconds"""


def detect_cuts(v, bus, sensitivity, proxy_width, min_scene_secs, start_time=0) -> TimelineStamps:
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
      min_scene_secs (float): Ignore scene changes shorter than this duration
      start_time (float):
  """

  cut_time_regex = re.compile(r'Parsed_metadata.*pts_time:(\d+\.?\d*)')

  cmd = [
    ffmpeg,
    '-hide_banner',
    '-an',  # Don’t process audio
    '-ss', str(start_time),
    '-i', v.path,
    '-vf', ','.join([
      f'scale={proxy_width}:-1',
      f"select='gt(scene, {1 - sensitivity / 100})'",
      'metadata=print'
    ]),
    '-f', 'null', '-',  # Don’t generate an output video
  ]

  stamps = [start_time]
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
            if (cut_time - stamps[-1]) >= min_scene_secs:
              stamps.append(cut_time)
              bus.emit_progress(cut_time / v.duration, stamps)
          except ValueError:
            pass

      process.wait()
      stamps.append(v.duration)
      bus.emit_progress(1, stamps)

      if not stopped_from_ui and process.returncode != 0:
        raise RuntimeError(''.join(stderr_buffer))

      return stamps
  except KeyboardInterrupt:  # Ctrl+C terminates analysis, and we create a file with the progress so far
    if process:
      process.terminate()
  except Exception:
    raise
  finally:
    bus.unsubscribe_stop()
