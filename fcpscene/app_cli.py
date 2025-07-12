#!/usr/bin/env python3

import sys
import argparse
from shutil import which
from pathlib import Path

from fcpscene import __version__, __repo_url__, __description__, PROXY_WIDTH, DEFAULT_SENSITIVITY, MIN_SCENE_SECS
from .ffmpeg import ffmpeg, ffprobe
from .video_attr import VideoAttr
from .event_bus import EventBus
from .to_csv_clips import to_csv_clips
from .to_fcpxml_clips import to_fcpxml_clips
from .to_fcpxml_markers import to_fcpxml_markers
from .to_fcpxml_compound_clips import to_fcpxml_compound_clips
from .detect_cuts import detect_cuts

def main():
  check_dependency(ffmpeg)
  check_dependency(ffprobe)

  parser = argparse.ArgumentParser(
    description=__description__,
    epilog=f'{__repo_url__}\nPowered by FFmpeg',
    formatter_class=argparse.RawTextHelpFormatter
  )
  parser.add_argument(
    'video',
    type=argparse.FileType('r'),
    nargs='?',
    help='Path to the input video file'
  )
  parser.add_argument(
    '-v', '--version',
    action='version',
    version=__version__
  )
  parser.add_argument(
    '--gui',
    action='store_true',
    help='Open the GUI instead of running in CLI mode'
  )
  parser.add_argument(
    '-q', '--quiet',
    action='store_true',
    help='Do not print progress or video summary'
  )
  parser.add_argument(
    '-s', '--sensitivity',
    type=validate_percent,
    default=DEFAULT_SENSITIVITY,
    help='(0-100, default: %(default)s) frame difference percent for detecting scene changes'
  )
  parser.add_argument(
    '-mss', '--min-scene-secs',
    type=float,
    default=MIN_SCENE_SECS,
    help='(default: %(default)s) ignore scene changes shorter than this duration (in seconds) to avoid noise'
  )
  parser.add_argument(
    '-o', '--output',
    help='(default: <video-dir>/<video-name>.fcpxml) Name of the output .fcpxml or .csv file'
  )
  parser.add_argument(
    '-m', '--mode',
    default='compound-clips',
    choices=['compound-clips', 'clips', 'markers', 'count'],
    help=(
      '(default: %(default)s)\n'
      'Options:\n'
      '    compound-clips: Wraps each clip in its own compound clip\n'
      '    clips: Normal clips\n'
      '    markers: Only add markers\n'
      '    count: Print cut count (no file is saved)\n'
    )
  )
  parser.add_argument(
    '-w', '--proxy-width',
    type=int,
    default=PROXY_WIDTH,
    help=' (default: %(default)s) width of scaled video used for speeding up analysis'
  )
  args = parser.parse_args()

  if args.gui:
    from .app_gui import GUI
    GUI.run(args.video.name if args.video else None)
    return

  if args.video is None:
    parser.error('The "video" is required')

  if args.output and not args.output.endswith(('.csv', '.fcpxml')):
    parser.error('Invalid output format. Only .fcpxml and .csv are supported')

  v = VideoAttr(args.video.name)
  if v.error:
    exit_error(v.error)

  bus = EventBus()
  if not args.quiet:
    print(v.summary)
    bus.subscribe_progress(print_progress)
  try:
    stamps = detect_cuts(v, bus, args.sensitivity, args.proxy_width, args.min_scene_secs)
    process_stamps(stamps, v, args.mode, args.output)
  except Exception as e:
    exit_error(f'Unexpected error while running ffmpeg: {e}')


def process_stamps(stamps, v, mode, out_file):
  if mode == 'count':
    print(f'{len(stamps) - 2}')
    return

  if out_file and out_file.endswith('.csv'):
    txt = to_csv_clips(stamps)
  elif mode == 'clips':
    txt = to_fcpxml_clips(stamps, v)
  elif mode == 'markers':
    txt = to_fcpxml_markers(stamps, v)
  else:
    txt = to_fcpxml_compound_clips(stamps, v)

  try:
    out_file = Path(out_file or v.path.with_suffix('.fcpxml'))
    out_file.write_text(txt, encoding='utf-8')
    print(f'\n💾 file://{out_file.resolve()}')
  except Exception as e:
    exit_error(f'Failed to write to {out_file}: {e}')


def validate_percent(value):
  f = float(value)
  if not (0 <= f <= 100):
    raise argparse.ArgumentTypeError('Must be between 0 and 100')
  return f


def print_progress(progress, stamps):
  bar = progress_bar(progress)
  n_cuts = len(stamps) - 1 if progress != 1 else len(stamps) - 2
  print(f'\r{bar} {int(progress * 100)}% (Cuts {n_cuts})  ', end='', flush=True)


def progress_bar(progress):
  width = 42  # +1
  n_full = int(width * progress)
  f_partial = (width * progress) - n_full
  n_remaining = width - n_full
  partials = [' ', '▎', '▍', '▋']
  partial = partials[min(int(len(partials) * f_partial), len(partials) - 1)]
  return ('█' * n_full) + partial + ('⠂' * n_remaining)


def check_dependency(program: str):
  if not which(program):
    exit_error(f'Missing dependency {program}')


def exit_error(msg: str):
  sys.stderr.write(f'\nERROR: {msg}\n')
  sys.exit(1)


if __name__ == '__main__':
  main()
