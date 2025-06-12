#!/usr/bin/env python3

# Author: Eric Fortis
# License: MIT

__version__ = "1.0.0"

from argparse import ArgumentParser, ArgumentTypeError
from pathlib import Path
from math import ceil
from html import escape
import re
import sys
import shutil
import subprocess

THRESHOLD = 15
PROXY_WIDTH = 320  # lower-res is OK for analysis


def main():
  parser = ArgumentParser(description='Generates a Final Cut Pro XML project with scene cuts from a video')
  parser.add_argument('video', help='Path to the input video file')
  parser.add_argument('-t', '--threshold',
                      type=validate_percent,
                      default=THRESHOLD,
                      help='Minimum frame difference percent for detecting scene changes. Lower is more sensitive. (0-100, default: %(default)s)')
  parser.add_argument('-w', '--proxy-width',
                      type=int,
                      default=PROXY_WIDTH,
                      help='Width of scaled video used for speeding up analysis (default: %(default)s)')
  args = parser.parse_args()

  check_dependencies()
  out_xml = scenes_to_fcp(args.video, args.proxy_width, args.threshold)

  output_file = Path(args.video).with_suffix('.fcpxml')
  Path(output_file).write_text(out_xml, encoding='utf-8')
  print(f'\n✅  Saved file://{Path(output_file).resolve()}')


def validate_percent(value):
  f = float(value)
  if not (0 <= f <= 100):
    raise ArgumentTypeError('Must be between 0 and 100')
  return f


def check_dependencies():
  if not shutil.which('ffmpeg'):
    sys.stderr.write("ERROR: 'ffmpeg' not found\n")
    sys.exit(1)
  if not shutil.which('ffprobe'):
    sys.stderr.write("ERROR: 'ffprobe' not found\n")
    sys.exit(1)


def scenes_to_fcp(video, proxy_width=PROXY_WIDTH, threshold=THRESHOLD):
  video_name = escape(Path(video).stem)
  video_url = Path(video).name

  width = video_attr(video, 'width')
  height = video_attr(video, 'height')
  duration = float(video_attr(video, 'duration'))
  r_frame_rate = video_attr(video, 'r_frame_rate')  # real base e.g. '60/1', or '30000/1001' = 29.97

  fps_numerator, fps_denominator = map(int, r_frame_rate.split('/'))
  fps = fps_numerator / fps_denominator

  cuts = detect_scene_cuts(video, duration, proxy_width, threshold)
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
      <media-rep kind="original-media" src="{video_url}"/>
    </asset>
  </resources>
  <library>
    <event>
      <project>
        <sequence format="r1" tcStart="0s" tcFormat="NDF">
          <spine>'''

  prev_frame = 0
  for frame in cuts:
    offset_ticks = prev_frame * fps_denominator
    duration_ticks = (frame - prev_frame) * fps_denominator
    xml += f'''
            <asset-clip ref="r2" tcFormat="NDF" name="{video_name}"
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


def detect_scene_cuts(video, duration, proxy_width, threshold) -> list[float]:
  pts_time_pattern = re.compile(r'pts_time:(\d+\.?\d*)')
  cmd = [
    'ffmpeg', '-nostats', '-hide_banner', '-an',
    '-i', video,
    '-vf', f"scale={proxy_width}:-1,select='gt(scene,{threshold / 100})',metadata=print",
    '-fps_mode', 'vfr',
    '-f', 'null',
    '-'
  ]
  cuts = []
  stderr_buffer = []
  try:
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as process:
      for line in process.stderr:
        stderr_buffer.append(line)
        match = pts_time_pattern.search(line)
        if match:
          try:
            time_str = float(match.group(1))
            cuts.append(time_str)
            print_progress(time_str / duration, len(cuts))
          except ValueError:
            pass
      process.wait()
      print_progress(1, len(cuts))
      if process.returncode != 0:
        raise RuntimeError(f'\nffmpeg exited with code {process.returncode}:\n{''.join(stderr_buffer)}')
  except KeyboardInterrupt:  # Ctrl+C terminates analysis, and we create a file with the progress so far
    if process:
      process.terminate()
  except Exception as e:
    sys.stderr.write(f'\nAn unexpected error occurred during ffmpeg execution: {e}\n')
    sys.exit(1)
  return cuts


def print_progress(progress: float, n_cuts):
  length = 33
  filled = int(length * progress)
  bar = '█' * filled + '⠂' * (length - filled)
  print(f'\r{bar} {int(progress * 100)}% (Cuts {n_cuts})', end='')


if __name__ == '__main__':
  main()
