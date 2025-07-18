from dataclasses import dataclass

from .video_attr import VideoAttr
from .detect_scene_changes import CutTimes, count_scenes


@dataclass
class Clip:
  """Describes a Final Cut Pro clip

  Attributes:
      seq (str): Suffix used in naming the clip (e.g., 001)
      ref_id (str): Unique ID in FCPXML
      offset (str): TimelineTime corresponding to the clip’s left edge
      duration (str): TimelineTime
  """
  seq: str
  ref_id: str
  offset: str
  duration: str


def cuts_to_clips(cuts: CutTimes, v: VideoAttr) -> list[Clip]:
  """
  Background:
    The clip’s [left and right] edges — `offset` and `offset+duration` — are in
    **timeline time**. In contrast, `start` is **video time**. For our purposes,
    `start=offset` because clips are always aligned with the video.

    Times must be integer fractions such as '150150/30000s'. Experimentally, the
    rounding rule is: `floor` when decimals are close to zero, `ceil` otherwise.

    FCP uses incremental reference IDs. `r1` and `r2` are reserved in our templates.
  """
  first_available_ref_id = 3  # constant
  seq_digits = len(str(count_scenes(cuts)))

  cut_frames = [int(s * v.fps + 0.9999) for s in cuts]  # ceil with threshold

  clips = []
  for i, frame in enumerate(cut_frames[:-1]):
    offset_ticks = frame * v.fps_denominator
    duration_ticks = (cut_frames[i + 1] - frame) * v.fps_denominator
    clips.append(Clip(
      seq=f'{i + 1:0{seq_digits}}',
      ref_id=f'r{i + first_available_ref_id}',
      offset=to_fcp_time(offset_ticks, v.fps_numerator),
      duration=to_fcp_time(duration_ticks, v.fps_numerator),
    ))
  return clips


def to_fcp_time(num, den):
  if num % den:
    return f'{num}/{den}s'
  return f'{int(num / den)}s'
