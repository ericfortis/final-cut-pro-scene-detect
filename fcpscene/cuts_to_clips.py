from dataclasses import dataclass

from .video_attr import VideoAttr
from .detect_scene_changes import CutTimes, count_scenes


@dataclass
class FcpClip:
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


@dataclass
class FileClip:
  """Describes a generic file-based clip

  Attributes:
      seq: Suffix used in naming the clip (e.g., 001)
      start: Start time in seconds
      end: End time in seconds
  """
  seq: str
  start: float
  end: float


def cuts_to_fcp_clips(cuts: CutTimes, v: VideoAttr) -> list[FcpClip]:
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
    clips.append(FcpClip(
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



def cuts_to_file_clips(cuts: CutTimes) -> list[FileClip]:
  seq_digits = len(str(count_scenes(cuts)))
  clips = []
  for i, (start, end) in enumerate(zip(cuts, cuts[1:])):
    clips.append(FileClip(
      seq=f'{i + 1:0{seq_digits}}',
      start=start,
      end=end
    ))
  return clips
