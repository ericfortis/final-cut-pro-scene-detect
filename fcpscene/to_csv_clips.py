from .utils import clean_decimals
from .cuts_to_clips import cuts_to_file_clips
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
  for clip in cuts_to_file_clips(cuts):
    out.append(f'{clean_decimals(clip.start)},{clean_decimals(clip.end)}')
  return '\n'.join(out) + '\n'
