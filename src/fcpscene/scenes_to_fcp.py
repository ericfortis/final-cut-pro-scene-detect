#!/usr/bin/env python3

from math import ceil
from signal import SIGINT
from subprocess import Popen, PIPE
import re
import sys

from fcpscene.utils import file_uri
from fcpscene.event_bus import EventBus
from fcpscene.video_attr import VideoAttr

PROXY_WIDTH = 320


def scenes_to_fcp(v: VideoAttr, bus: EventBus, sensitivity, proxy_width=PROXY_WIDTH) -> str:
  cuts = detect_scene_cuts(v.video_path, v.duration, bus, sensitivity, proxy_width)
  cuts.append(v.duration)
  cuts = [ceil(t * v.fps) for t in cuts]  # seconds to frames

  xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.13">
  <resources>
    <!-- Dummy `name` avoids import warnings https://github.com/OpenTimelineIO/otio-fcpx-xml-adapter/issues/6 -->
    <format id="r1" name="FFVideoFormat720p24"
      width="{v.width}"
      height="{v.height}"
      frameDuration="{v.fps_denominator}/{v.fps_numerator}s" />
    <asset id="r2" start="0s" format="r1">
      <media-rep kind="original-media" src="{file_uri(v.video_path)}"/>
    </asset>
  </resources>
  <library>
    <event>
      <project>
        <sequence format="r1" tcStart="0s">
          <spine>'''

  # The clip’s [left and right] edges, `offset` and `offset+duration`, are in timeline times.
  # On the other hand, `start` is in video time. For our purposes, `offset=start`.
  prev_frame = 0
  for frame in cuts:
    if frame - prev_frame <= 1:  # ignore 1-frame cuts
      continue
    offset_ticks = prev_frame * v.fps_denominator
    duration_ticks = (frame - prev_frame) * v.fps_denominator
    xml += f'''
            <asset-clip ref="r2"
              offset="{offset_ticks}/{v.fps_numerator}s"
              start="{offset_ticks}/{v.fps_numerator}s"
              duration="{duration_ticks}/{v.fps_numerator}s"/>'''
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


def detect_scene_cuts(video, video_duration, bus: EventBus, sensitivity, proxy_width) -> list[float]:
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
    '-fps_mode', 'vfr',  # ensure the natural frame timing is not changed by the `scene` filter
    '-f', 'null',  # null-muxer for discarding the processed video (we won’t write encoded binary data)
    '-'  # output to stdout (needed although the null-muxer outputs nothing)
  ]

  cuts = []
  stderr_buffer = []
  stopped_from_gui = False

  try:
    with Popen(cmd, stdout=PIPE, stderr=PIPE, text=True) as process:
      def on_stop_from_gui():
        if process and process.poll() is None:
          nonlocal stopped_from_gui
          stopped_from_gui = True
          process.send_signal(SIGINT)

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
