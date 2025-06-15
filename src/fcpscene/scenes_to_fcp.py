#!/usr/bin/env python3

__version__ = '1.0.1'

from pathlib import Path
from math import ceil
import re
import sys
import signal
import subprocess

from fcpscene.event_bus import EventBus

PROXY_WIDTH = 320


def scenes_to_fcp(video, bus, sensitivity, proxy_width=PROXY_WIDTH):
  video_path = Path(video).resolve()

  width = video_attr(video, 'width')
  height = video_attr(video, 'height')
  duration = float(video_attr(video, 'duration'))
  r_frame_rate = video_attr(video, 'r_frame_rate')  # real base e.g. '60/1', or '30000/1001' = 29.97

  fps_numerator, fps_denominator = map(int, r_frame_rate.split('/'))
  fps = fps_numerator / fps_denominator

  cuts = detect_scene_cuts(video, duration, proxy_width, sensitivity, bus)
  cuts.append(duration)
  cuts = [ceil(t * fps) for t in cuts]  # seconds to frames

  xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.13">
  <resources>
    <!-- Dummy `name` avoids import warnings https://github.com/OpenTimelineIO/otio-fcpx-xml-adapter/issues/6 -->
    <format id="r1" name="FFVideoFormat720p24"
      width="{width}"
      height="{height}"
      frameDuration="{fps_denominator}/{fps_numerator}s" />
    <asset id="r2" start="0s" format="r1">
      <media-rep kind="original-media" src="file://{video_path}"/>
    </asset>
  </resources>
  <library>
    <event>
      <project>
        <sequence format="r1" tcStart="0s">
          <spine>'''

  prev_frame = 0
  for frame in cuts:
    offset_ticks = prev_frame * fps_denominator
    duration_ticks = (frame - prev_frame) * fps_denominator
    xml += f'''
            <asset-clip ref="r2"
              offset="{offset_ticks}/{fps_numerator}s"
              start="{offset_ticks}/{fps_numerator}s"
              duration="{duration_ticks}/{fps_numerator}s"/>'''
    prev_frame = frame

  xml += f'''
          </spine>
        </sequence>
      </project>
    </event>
  </library>
</fcpxml>
'''
  return xml


def video_attr(video, attr) -> str:
  cmd = [
    'ffprobe', '-hide_banner',
    '-v', 'error',
    '-select_streams', 'v:0',
    '-show_entries', f'stream={attr}',
    '-of', 'csv=p=0',
    video
  ]
  try:
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()
  except subprocess.CalledProcessError as e:
    sys.stderr.write(f'\nERROR: {e.stderr.strip()}\n')
    sys.exit(1)
  except Exception as e:
    sys.stderr.write(f'\nAn unexpected error occurred during ffprobe execution: {e}\n')
    sys.exit(1)


def detect_scene_cuts(video, video_duration, proxy_width, sensitivity, bus: EventBus) -> list[float]:
  cut_time_regex = re.compile(r'Parsed_metadata.*pts_time:(\d+\.?\d*)')

  cmd = [
    'ffmpeg', '-nostats', '-hide_banner', '-an',
    '-i', video,
    '-vf', ','.join([
      f'scale={proxy_width}:-1',
      f"select='gt(scene, {1 - sensitivity / 100})'",  # select when cut probability is greater than `threshold`
      'metadata=print'  # outputs the scene change time to stderr
    ]),
    '-fps_mode', 'vfr',  # ensure the natural frame timing is not changed by the `scene` filter
    '-f', 'null',  # null-muxer for discarding the processed video (we won’t write encoded binary data)
    '-'  # output to stdout (needed although the null-muxer outputs nothing)
  ]

  cuts = []
  stderr_buffer = []
  stopped_from_gui = False

  try:
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as process:
      def on_stop_from_gui():
        if process and process.poll() is None:
          nonlocal stopped_from_gui
          stopped_from_gui = True
          process.send_signal(signal.SIGINT)

      bus.subscribe_stop(on_stop_from_gui)

      for line in process.stderr:  # while stderr is open
        stderr_buffer.append(line)
        match = cut_time_regex.search(line)
        if match:
          try:
            cut_time = float(match.group(1))
            cuts.append(cut_time)
            bus.emit_progress(cut_time, video_duration, len(cuts))
          except ValueError:
            pass

      process.wait()
      bus.emit_progress(video_duration, video_duration, len(cuts))

      if not stopped_from_gui and process.returncode != 0:
        raise RuntimeError(f'\nffmpeg exited with code {process.returncode}:\n' + ''.join(stderr_buffer))

  except KeyboardInterrupt:  # Ctrl+C terminates analysis, and we create a file with the progress so far
    if process:
      process.terminate()

  except Exception as e:
    sys.stderr.write(f'\nAn unexpected error occurred during ffmpeg execution: {e}\n')
    sys.exit(1)

  finally:
    bus.unsubscribe_stop()

  return cuts
