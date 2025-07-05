from .time_utils import clean_decimals
from .detect_scene_cut_times import CutTimes


def csv_clips(cut_times: CutTimes, video_duration: float):
  """
  Returns:
    str: CSV with one clip per row with its start and end seconds

  Example:
    >>> csv_clips([5, 10], 15.1)
    0,5
    5,10
    10,15.1
  """
  clips = [0] + cut_times + [video_duration]
  out = []
  for start, end in zip(clips, clips[1:]):
    out.append(f'{clean_decimals(start)},{clean_decimals(end)}')
  return '\n'.join(out) + '\n'
