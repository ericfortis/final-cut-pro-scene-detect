from .utils import clean_decimals
from .detect_scene_cuts import CutTimes


def to_csv_clips(cuts: CutTimes, video_duration: float):
  """CSV with one clip per row

  Example:
    >>> to_csv_clips([5, 10], 15.1)
    start,end
    0,5
    5,10
    10,15.1
  """
  clips = [0] + cuts + [video_duration]
  out = ['start,end']
  for start, end in zip(clips, clips[1:]):
    out.append(f'{clean_decimals(start)},{clean_decimals(end)}')
  return '\n'.join(out) + '\n'
