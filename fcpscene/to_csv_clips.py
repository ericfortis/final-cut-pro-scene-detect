from .utils import clean_decimals
from .detect_scene_changes import CutTimes


def to_csv_clips(cuts: CutTimes) -> str:
  """CSV with one clip per row

  Example:
    >>> to_csv_clips([0, 5, 10, 15])
    start,end
    0,5
    5,10
    10,15
  """
  out = ['start,end']
  for start, end in zip(cuts, cuts[1:]):
    out.append(f'{clean_decimals(start)},{clean_decimals(end)}')
  return '\n'.join(out) + '\n'
