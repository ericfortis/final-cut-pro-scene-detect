from dataclasses import dataclass

from .video_attr import VideoAttr
from .detect_scene_cuts import CutTimes


@dataclass
class FCPClip:
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


def cuts_to_clips(cuts: CutTimes, v: VideoAttr) -> list[FCPClip]:
  """
  Background:
    The clip’s [left and right] edges — `offset` and `offset+duration` — are in
    **timeline time**. In contrast, `start` is **video time**. For our purposes,
    `start=offset` because clips are always aligned with the video.

    Times must be integer fractions such as '150150/30000s'. Experimentally, the
    rounding rule is: `floor` when decimals are close to zero, `ceil` otherwise.

    FCP uses incremental reference IDs. `r1` and `r2` are reserved in our templates.
  """
  first_available_ref_id = 3 # constant

  cuts.append(v.duration)
  seq_digits = len(str(len(cuts)))

  clips = []
  prev_frame = 0
  for i, cut_secs in enumerate(cuts):
    frame = int(cut_secs * v.fps + 0.9999)  # ceil with threshold
    if frame - prev_frame <= 1:  # ignore 1-frame cuts
      continue
    offset_ticks = prev_frame * v.fps_denominator
    duration_ticks = (frame - prev_frame) * v.fps_denominator
    clips.append(FCPClip(
      seq=f'{i + 1:0{seq_digits}}',
      ref_id=f'r{i + first_available_ref_id}',
      offset=to_fcp_time(offset_ticks, v.fps_numerator),
      duration=to_fcp_time(duration_ticks, v.fps_numerator),
    ))
    prev_frame = frame
  return clips


def to_fcp_time(num, den):
  if num % den:
    return f'{num}/{den}s'
  return f'{int(num / den)}s'
