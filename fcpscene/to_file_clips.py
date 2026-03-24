import subprocess

from .ffmpeg import ffmpeg
from .video_attr import VideoAttr
from .event_bus import EventBus
from .cuts_to_clips import cuts_to_file_clips
from .detect_scene_changes import CutTimes


def to_file_clips(
  cuts: CutTimes,
  v: VideoAttr,
  bus: EventBus
):
  """Splits the original video into multiple files based on detected scenes.

  Args:
      cuts: List of cut timestamps.
      v: Video attributes of the original video.
      bus: EventBus for cancelling on stop signal.
  """
  output_dir = v.path.parent / v.path.stem
  output_dir.mkdir(parents=True, exist_ok=True)

  is_stopped = False
  process = None

  def on_stop():
    nonlocal is_stopped
    is_stopped = True
    if process:
      process.terminate()

  bus.subscribe_stop(on_stop)

  clips = cuts_to_file_clips(cuts)

  try:
    for clip in clips:
      if is_stopped:
        break
      cmd = [
        ffmpeg,
        '-y',
        '-hide_banner',
        '-ss', str(clip.start),
        '-to', str(clip.end),
        '-i', str(v.path),
        '-c', 'copy',
        '-avoid_negative_ts', 'make_non_negative',
        str(output_dir / f'{v.path.stem}_{clip.seq}{v.path.suffix}')
      ]
      process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      process.wait()
      process = None

  except KeyboardInterrupt:
    if process:
      process.terminate()

  finally:
    bus.unsubscribe_stop()
