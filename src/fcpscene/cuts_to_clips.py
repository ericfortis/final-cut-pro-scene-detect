from dataclasses import dataclass

from .video_attr import VideoAttr


@dataclass
class FCPClip:
  seq: str
  ref_id: str
  offset: str
  duration: str


def cuts_to_clips(cut_times: list[float], v: VideoAttr) -> list[FCPClip]:
  cut_times.append(v.duration)

  ref_ids_start_at = 3
  seq_digits = len(str(len(cut_times)))

  clips = []
  prev_frame = 0
  for i, cut_secs in enumerate(cut_times):
    frame = int(cut_secs * v.fps + 0.9999)  # ceil with threshold
    if frame - prev_frame <= 1:  # ignore 1-frame cuts
      continue
    offset_ticks = prev_frame * v.fps_denominator
    duration_ticks = (frame - prev_frame) * v.fps_denominator
    clips.append(FCPClip(
      seq=f'{i + 1:0{seq_digits}}',
      ref_id=f'r{i + ref_ids_start_at}',
      offset=to_fcp_time(offset_ticks, v.fps_numerator),
      duration=to_fcp_time(duration_ticks, v.fps_numerator),
    ))
    prev_frame = frame
  return clips


def to_fcp_time(num, den):
  if num % den:
    return f'{num}/{den}s'
  return f'{int(num / den)}s'
