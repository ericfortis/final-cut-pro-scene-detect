import re
import sys
from signal import SIGINT
from subprocess import Popen, PIPE

from .event_bus import EventBus


def detect_scene_cut_times(video, video_duration, bus: EventBus, sensitivity, proxy_width) -> list[float]:
  cut_time_regex = re.compile(r'Parsed_metadata.*pts_time:(\d+\.?\d*)')

  # ffmpeg’s video filters write to stderr. The metadata we need for the cut times is there.
  cmd = [
    'ffmpeg', '-nostats', '-hide_banner', '-an',
    '-i', video,

    '-vf', ','.join([
      f'scale={proxy_width}:-1',
      f"select='gt(scene, {1 - sensitivity / 100})'",  # select when cut probability is greater than `threshold`
      'metadata=print'
    ]),

    # ensure the natural frame timing is not changed by the `scene` filter (Not sure if it’s really needed)
    '-fps_mode', 'vfr',

    '-f', 'null',  # null-muxer for discarding processed video
    '-'  # output to stdout (needed although the null-muxer outputs nothing)
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
            bus.emit_progress(cut_time / video_duration, cuts)
          except ValueError:
            pass

      process.wait()
      bus.emit_progress(1, cuts)

      if not stopped_from_ui and process.returncode != 0:
        raise RuntimeError(f'\nffmpeg exited with code {process.returncode}:\n' + ''.join(stderr_buffer))

  except KeyboardInterrupt:  # Ctrl+C terminates analysis, and we create a file with the progress so far
    if process:
      process.terminate()
  except Exception as e:
    sys.stderr.write(f'\nUnexpected error while running ffmpeg: {e}\n')
    sys.exit(1)
  finally:
    bus.unsubscribe_stop()

  return cuts
