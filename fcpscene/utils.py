def format_seconds(seconds: float, max_decimals: int = 2) -> str:
  """Seconds to string 9h9m9s

  Examples:
      >>> format_seconds(1.1)
      '1.1s'
      >>> format_seconds(3661, 2)
      '1h1m1.00s'
  """
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
    result += f"{clean_decimals(f'{partial_seconds:.{max_decimals}f}')}s"
  return result


def clean_decimals(number) -> str:
  """Removes trailing zeros and a trailing decimal point

  Examples:
      >>> clean_decimals(3.1400)
      '3.14'
      >>> clean_decimals(5.0)
      '5'
  """
  return str(number).rstrip('0').rstrip('.') or '0'
