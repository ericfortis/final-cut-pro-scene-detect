from pathlib import Path
from argparse import ArgumentParser, ArgumentTypeError

from fcpscene.utils import check_dependency
from fcpscene.event_bus import EventBus
from fcpscene.scenes_to_fcp import scenes_to_fcp, PROXY_WIDTH, __version__


def main():
  parser = ArgumentParser(description='Generates a Final Cut Pro XML project with scene cuts from a video')
  parser.add_argument('-v', '--version', action='version', version=__version__)
  parser.add_argument('video', help='Path to the input video file')
  parser.add_argument('-s', '--sensitivity',
                      type=validate_percent,
                      default=85,
                      help='Frame difference percent for detecting scene changes. (0-100, default: %(default)s)')
  parser.add_argument('-w', '--proxy-width',
                      type=int,
                      default=PROXY_WIDTH,
                      help='Width of scaled video used for speeding up analysis (default: %(default)s)')
  args = parser.parse_args()

  check_dependency('ffmpeg')
  check_dependency('ffprobe')

  bus = EventBus()
  bus.subscribe_progress(print_progress)
  out_xml = scenes_to_fcp(args.video, bus, args.sensitivity, args.proxy_width)

  output_file = Path(args.video).with_suffix('.fcpxml')
  Path(output_file).write_text(out_xml, encoding='utf-8')
  print(f'\n✅  Saved file://{Path(output_file).resolve()}')


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
