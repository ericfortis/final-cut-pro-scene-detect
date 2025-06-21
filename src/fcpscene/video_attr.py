import subprocess


class VideoAttr:
  def __init__(self, video_path: str):
    self._runtime_error = ''
    self.video_path = video_path
    self.is_video = self.get('codec_type') == 'video'
    if self.is_video:
      self.width = int(self.get('width'))
      self.height = int(self.get('height'))
      self.duration = float(self.get('duration'))

      r_frame_rate = self.get('r_frame_rate')  # real base e.g. '60/1', or '30000/1001' = 29.97
      fps_numerator, fps_denominator = map(int, r_frame_rate.split('/'))
      self.fps_numerator = fps_numerator
      self.fps_denominator = fps_denominator
      self.fps = fps_numerator / fps_denominator

  def get_error(self) -> str:
    if self._runtime_error: return self._runtime_error
    if not self.is_video: return 'Invalid video file'
    if self.duration <= 0: return 'Cannot process video with zero or unknown duration'
    return ''

  def get(self, attr) -> str:
    cmd = [
      'ffprobe', '-hide_banner',
      '-v', 'error',
      '-select_streams', 'v:0',
      '-show_entries', f'stream={attr}',
      '-of', 'csv=p=0',
      self.video_path
    ]
    try:
      return subprocess.check_output(cmd, stderr=subprocess.PIPE).decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
      self._runtime_error = (e.stderr or b'').decode('utf-8', errors='replace').strip()
    except Exception as e:
      self._runtime_error = f'An unexpected error occurred during ffprobe execution: {e}'
    return ''
