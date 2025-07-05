import sys
import argparse
from shutil import which
from pathlib import Path

from fcpscene import __version__, __repo_url__, __description__, PROXY_WIDTH
from .csv_clips import csv_clips
from .time_utils import date_mdy
from .video_attr import VideoAttr
from .event_bus import EventBus
from .fcpxml_clips import fcpxml_clips
from .fcpxml_markers import fcpxml_markers
from .fcpxml_compound_clips import fcpxml_compound_clips
from .detect_scene_cut_times import detect_scene_cut_times


def main():
  check_dependency('ffmpeg')
  check_dependency('ffprobe')

  parser = argparse.ArgumentParser(
    description=__description__,
    epilog=f'{__repo_url__}\nPowered by FFmpeg',
    formatter_class=argparse.RawDescriptionHelpFormatter)

  parser.add_argument(
    'video',
    type=argparse.FileType('r'),
    help='Path to the input video file'
  )
  parser.add_argument(
    '-v', '--version',
    action='version',
    version=__version__
  )
  parser.add_argument(
    '-s', '--sensitivity',
    type=validate_percent,
    default=89,
    help='(0-100, default: %(default)s) frame difference percent for detecting scene changes'
  )
  parser.add_argument(
    '-w', '--proxy-width',
    type=int,
    default=PROXY_WIDTH,
    help=' (default: %(default)s) width of scaled video used for speeding up analysis'
  )
  parser.add_argument(
    '-o', '--output',
    help='(default: <video-dir>/<video-name>.fcpxml) Name of the output .fcpxml or .csv file'
  )
  parser.add_argument(
    '-e', '--event-name',
    default=date_mdy(),
    help='Existing event name. Defaults to today’s date (e.g. %(default)s), which matches the default event in new libraries'
  )
  parser.add_argument(
    '-f', '--format',
    default='compound-clips',
    choices=['compound-clips', 'clips', 'markers'],
    help=(
      '(default: %(default)s)\n'
      'Options:\n'
      '  (compound-clips = Wraps each clip in its own compound clip)'
      '  (clips = Normal clips)'
      '  (markers = Only add markers)'
    )
  )
  args = parser.parse_args()

  if args.output and not args.output.endswith(('.csv', '.fcpxml')):
    exit_error('Invalid output format')

  v = VideoAttr(args.video.name)
  if v.error: exit_error(v.error)

  print(v.summary)

  bus = EventBus()
  bus.subscribe_progress(print_progress)
  cuts = []
  try:
    cuts = detect_scene_cut_times(v, bus, args.sensitivity, args.proxy_width)
    if not cuts: exit_error('No scene changes found')
  except Exception as e:
    exit_error(f'Unexpected error while running ffmpeg: {e}')

  if args.output and args.output.endswith('.csv'):
    txt = csv_clips(cuts, v.duration)
    output_file = args.output
  elif args.format == 'clips':
    txt = fcpxml_clips(cuts, v)
    output_file = args.output or v.path.with_suffix('.fcpxml')
  elif args.format == 'markers':
    txt = fcpxml_markers(cuts, v)
    output_file = args.output or v.path.with_suffix('.fcpxml')
  else:
    txt = fcpxml_compound_clips(cuts, v, args.event_name)
    output_file = args.output or v.path.with_name(f'{v.stem}-Event-{args.event_name}.fcpxml')

  try:
    Path(output_file).write_text(txt, encoding='utf-8')
    print(f'\n💾 file://{Path(output_file).resolve()}')
  except (OSError, IOError) as e:
    exit_error(f'Failed to write to {output_file}: {e}')


def validate_percent(value):
  f = float(value)
  if not (0 <= f <= 100):
    raise argparse.ArgumentTypeError('Must be between 0 and 100')
  return f


def print_progress(progress, cuts):
  bar = progress_bar(progress)
  print(f'\r{bar} {int(progress * 100)}% (Cuts {len(cuts)})  ', end='', flush=True)


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
