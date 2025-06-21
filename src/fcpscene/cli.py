import sys
from pathlib import Path
from argparse import ArgumentParser, ArgumentTypeError, RawDescriptionHelpFormatter

from fcpscene import __version__, __repo_url__, __description__
from fcpscene.utils import check_dependency
from fcpscene.video_attr import VideoAttr
from fcpscene.event_bus import EventBus
from fcpscene.scenes_to_fcp import scenes_to_fcp, PROXY_WIDTH


def main():
  parser = ArgumentParser(
    description=__description__,
    epilog=f'Source Code:\n{__repo_url__}\n\nPowered by FFmpeg',
    formatter_class=RawDescriptionHelpFormatter)
  parser.add_argument('video', help='Path to the input video file')
  parser.add_argument('-v', '--version', action='version', version=__version__)
  parser.add_argument('-s', '--sensitivity',
                      type=validate_percent,
                      default=85,
                      help='(0-100, default: %(default)s) frame difference percent for detecting scene changes')
  parser.add_argument('-w', '--proxy-width',
                      type=int,
                      default=PROXY_WIDTH,
                      help=' (default: %(default)s) width of scaled video used for speeding up analysis')
  args = parser.parse_args()

  check_dependency('ffmpeg')
  check_dependency('ffprobe')

  v = VideoAttr(args.video)

  if v.get_error():
    sys.stderr.write(f'\nERROR: {v.get_error()}\n')
    sys.exit(1)

  bus = EventBus()
  bus.subscribe_progress(print_progress)
  out_xml = scenes_to_fcp(v, bus, args.sensitivity, args.proxy_width)

  output_file = Path(args.video).with_suffix('.fcpxml')
  Path(output_file).write_text(out_xml, encoding='utf-8')
  print(f'\n💾 file://{Path(output_file).resolve()}')


def validate_percent(value):
  f = float(value)
  if not (0 <= f <= 100):
    raise ArgumentTypeError('Must be between 0 and 100')
  return f


def print_progress(cut_time: float, video_duration: float, n_cuts: int):
  progress = cut_time / video_duration
  bar = progress_bar(progress)
  print(f'\r{bar} {int(progress * 100)}% (Cuts {n_cuts})  ', end='', flush=True)


def progress_bar(progress):
  width = 42  # +1
  n_full = int(width * progress)
  f_partial = (width * progress) - n_full
  n_remaining = width - n_full
  partials = [' ', '▎', '▍', '▋']
  partial = partials[min(int(len(partials) * f_partial), len(partials) - 1)]
  return ('█' * n_full) + partial + ('⠂' * n_remaining)


if __name__ == '__main__':
  main()
