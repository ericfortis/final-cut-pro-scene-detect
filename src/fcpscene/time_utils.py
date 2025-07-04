from datetime import date


def format_seconds(seconds: float, n_decimals: int = 2) -> str:
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
    raw = f'{partial_seconds:.{n_decimals}f}'
    cleaned = clean_decimals(raw) or '0'
    result += f'{cleaned}s'
  return result


def clean_decimals(number) -> str:
  return str(number).rstrip('0').rstrip('.')


def date_mdy() -> str:
  return date.today().strftime('%-m-%-d-%y')
