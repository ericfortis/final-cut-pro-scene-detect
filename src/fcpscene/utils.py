import sys
from urllib.parse import quote
from pathlib import Path
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
    result += f'{clean_decimals(f'{partial_seconds:.2f}')}s'
  return result


def clean_decimals(number) -> str:
  return str(number).rstrip('0').rstrip('.')


def check_dependency(program: str):
  if not which(program):
    sys.stderr.write(f'Missing dependency: {program}\n')
    sys.exit(1)


def file_uri(path: str) -> str:
  return 'file://' + quote(str(Path(path).resolve()))
