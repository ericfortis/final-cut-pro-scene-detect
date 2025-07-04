import json
import subprocess
from pathlib import Path
from dataclasses import dataclass, fields, Field
from urllib.parse import quote
from collections.abc import Sequence

from .time_utils import format_seconds, clean_decimals


@dataclass
class FFProbe:
  width: int = 0
  height: int = 0
  duration: float = 0
  r_frame_rate: str = ''  # real base '60/1', '30000/1001'=29.97
  codec_name: str = ''

  color_trc: str = ''
  colorspace: str = ''
  color_primaries: str = ''


class VideoAttr(FFProbe):
  def __init__(self, video: str):
    self._runtime_error = None

    self.path = video
    self.parse(fields(FFProbe))

    if not self.error:
      self.name = str(Path(video).name)
      self.stem = str(Path(video).stem)

      self.width = int(self.width)
      self.height = int(self.height)
      self.duration = float(self.duration)

      fps_numerator, fps_denominator = map(int, self.r_frame_rate.split('/'))
      self.fps_numerator = fps_numerator
      self.fps_denominator = fps_denominator
      self.fps = fps_numerator / fps_denominator
      self.duration_frames = self.duration * self.fps


  @property
  def error(self) -> str:
    if self._runtime_error: return self._runtime_error
    if float(self.duration) <= 0: return 'Cannot process video with zero or unknown duration'
    return ''

  @property
  def summary(self) -> str:
    return '   '.join([
      f'{self.width}x{self.height}',
      f'{clean_decimals(f'{self.fps:.2f}')}fps',
      self.codec_name,
      f'(Duration: {format_seconds(self.duration)})'
    ])

  @property
  def file_uri(self):
    return 'file://' + quote(str(Path(self.path).resolve()))

  @property
  def fcp_color_space(self) -> str:
    return {
      ('bt709', 'bt709', 'bt709'): '1-1-1',
      ('smpte170m', 'bt709', 'smpte170m'): '6-1-6',
      ('bt470bg', 'bt709', 'smpte170m'): '5-1-6',
      ('bt2020', 'bt709', 'bt2020nc'): '9-1-9',
      ('bt2020', 'smpte2084', 'bt2020nc'): '9-16-9',
      ('bt2020', 'arib-std-b67', 'bt2020nc'): '9-18-9',
    }.get((self.color_primaries, self.color_trc, self.colorspace), '1-1-1')


  def parse(self, _fields: Sequence[Field]):
    attrs = [f.name for f in _fields]
    json_out = self.ffprobe(*attrs)
    for attr in attrs:
      setattr(self, attr, json_out.get(attr, ''))

  def ffprobe(self, *attrs) -> dict[str, str]:
    cmd = [
      'ffprobe',
      '-v', 'error',
      '-select_streams', 'v:0',
      '-show_entries', f'stream={','.join(attrs)}',
      '-of', 'json',
      self.path
    ]
    try:
      out = subprocess.check_output(cmd, stderr=subprocess.PIPE).decode('utf-8')
      stream = json.loads(out).get('streams', [{}])[0]
      return {attr: stream.get(attr, '') for attr in attrs}
    except subprocess.CalledProcessError as e:
      self._runtime_error = (e.stderr or b'').decode('utf-8', errors='replace').strip()
    except Exception as e:
      self._runtime_error = f'Unexpected error while running ffprobe: {e}'
    return {}
