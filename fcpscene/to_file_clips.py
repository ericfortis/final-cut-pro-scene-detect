import subprocess

from .ffmpeg import ffmpeg
from .video_attr import VideoAttr
from .event_bus import EventBus
from .cuts_to_clips import cuts_to_file_clips
from .detect_scene_changes import CutTimes


def to_file_clips(cuts: CutTimes, v: VideoAttr, bus: EventBus):
  """Splits the original video into multiple files based on detected scenes"""
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
  n_clips = len(clips)

  vcodec = vcodec_for(v)
  try:
    for clip in clips:
      if is_stopped:
        break
      bus.emit_export_progress(clip.seq, n_clips)
      cmd = [
        ffmpeg,
        '-y',
        '-hide_banner',
        '-ss', str(clip.start),
        '-to', str(clip.end),
        '-i', str(v.path),
        *vcodec,
        '-avoid_negative_ts', 'make_non_negative',
        str(output_dir / f'{v.path.stem}_{clip.seq}{v.path.suffix}')
      ]
      process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      process.communicate()
      process = None

  except KeyboardInterrupt:
    if process:
      process.terminate()

  finally:
    bus.unsubscribe_stop()


def vcodec_for(v: VideoAttr) -> list[str]:
  if v.intraframe_coded:
    return ['-c:v', 'copy']

  # Re-encoding for accurate splits
  encoder, crf = {
    'h264': ('libx264', '18'),
    'hevc': ('libx265', '20'),
    'vp9': ('libvpx-vp9', '31'),
    'av1': ('libsvtav1', '30'),
  }.get(v.codec_name, ('libx264', '18'))
  return [
    '-c:v', encoder,
    '-crf', crf,
    '-preset', 'veryfast',
    '-pix_fmt', 'yuv420p'
  ]
