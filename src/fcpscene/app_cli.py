import sys
import argparse
from shutil import which
from pathlib import Path

from fcpscene import __version__, __repo_url__, __description__, PROXY_WIDTH, DEFAULT_SENSITIVITY
from .video_attr import VideoAttr
from .event_bus import EventBus
from .to_csv_clips import to_csv_clips
from .to_fcpxml_clips import to_fcpxml_clips
from .to_fcpxml_markers import to_fcpxml_markers
from .to_fcpxml_compound_clips import to_fcpxml_compound_clips
from .detect_scene_cuts import detect_scene_cut_times


def main():
  check_dependency('ffmpeg')
  check_dependency('ffprobe')

  parser = argparse.ArgumentParser(
    description=__description__,
    epilog=f'{__repo_url__}\nPowered by FFmpeg',
    formatter_class=argparse.RawTextHelpFormatter)

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
    default=DEFAULT_SENSITIVITY,
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
    '-m', '--mode',
    default='compound-clips',
    choices=['compound-clips', 'clips', 'markers'],
    help=(
      '(default: %(default)s)\n'
      'Options:\n'
      '    compound-clips: Wraps each clip in its own compound clip\n'
      '    clips: Normal clips\n'
      '    markers: Only add markers'
    )
  )
  args = parser.parse_args()

  if args.output and not args.output.endswith(('.csv', '.fcpxml')):
    exit_error('Invalid output format')

  v = VideoAttr(args.video.name)
  if v.error:
    exit_error(v.error)

  print(v.summary)
  bus = EventBus()
  bus.subscribe_progress(print_progress)
  try:
    cuts = detect_scene_cut_times(v, bus, args.sensitivity, args.proxy_width)
    if cuts:
      process_cuts(cuts, v, args.mode, args.output)
    else:
      exit_error('No scene changes found')
  except Exception as e:
    exit_error(f'Unexpected error while running ffmpeg: {e}')


def process_cuts(cuts, v, mode, out_file):
  if out_file and out_file.endswith('.csv'):
    txt = to_csv_clips(cuts, v.duration)
  elif mode == 'clips':
    txt = to_fcpxml_clips(cuts, v)
  elif mode == 'markers':
    txt = to_fcpxml_markers(cuts, v)
  else:
    txt = to_fcpxml_compound_clips(cuts, v)

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
