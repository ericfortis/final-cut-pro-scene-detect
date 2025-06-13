import sys
from shutil import which


def format_seconds(seconds: float) -> str:
  int_seconds = int(seconds)
  partial_seconds = seconds % 60
  minutes = (int_seconds % 3600) // 60
  hours = int_seconds // 3600
  result = ''
  if hours:
    result += f'{hours}h'
  if minutes:
    result += f'{minutes}m'
  if partial_seconds or not result:
    s = f'{partial_seconds:.2f}'.rstrip('0').rstrip('.')
    result += f'{s}s'
  return result


def check_dependency(program):
  if not which(program):
    sys.stderr.write(f'Missing dependency: {program}\n')
    sys.exit(1)
