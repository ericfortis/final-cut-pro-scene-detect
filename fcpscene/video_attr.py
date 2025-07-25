import json
import subprocess
from pathlib import Path
from dataclasses import dataclass, fields, Field
from urllib.parse import quote
from collections.abc import Sequence

from .utils import format_seconds, clean_decimals
from .ffmpeg import ffprobe


# TODO FCP actually uses frameDuration="100/6000s", we 1/60, think about this

@dataclass
class FFProbe:
  width: int = 0
  height: int = 0

  duration: float = 0
  r_frame_rate: str = ''  # real base '60/1', '30000/1001'=29.97

  codec_name: str = ''
  codec_type: str = ''

  color_trc: str = ''
  colorspace: str = ''
  color_primaries: str = ''


class VideoAttr(FFProbe):
  def __init__(self, video):
    self._runtime_error = None

    self.path = Path(video)
    self.stem = self.path.stem

    self.parse(fields(FFProbe))
    if not self.error:
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
    if self.codec_type != 'video': return 'Not a video file'
    if self._runtime_error: return self._runtime_error
    if float(self.duration) <= 0: return 'Cannot process video with zero or unknown duration'
    return ''


  @property
  def summary(self) -> str:
    return '    '.join([
      f'{self.width}x{self.height}',
      f'{clean_decimals(f"{self.fps:.2f}")}fps',
      format_seconds(self.duration),
      self.pretty_codec_name,
    ])

  @property
  def pretty_codec_name(self):
    # ffmpeg -codecs | grep '^...V'
    return {
      'dnxhd': 'DNxHD',
      'dvvideo': 'DV (Digital Video)',
      'h264': 'H.264',
      'hevc': 'H.265',
      'jpeg2000': 'JPEG 2000',
      'mpeg4': 'MPEG-4 Part 2',
      'prores': 'ProRes',
      'qtrle': 'QuickTime RLE',
      'rawvideo': 'Uncompressed',
    }.get(self.codec_name, self.codec_name)

  @property
  def file_uri(self):
    return 'file://' + quote(str(self.path.resolve()))

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


  def parse(self, attrs: Sequence[Field]):
    attrs = [f.name for f in attrs]
    json_out = self.ffprobe(*attrs)
    for attr in attrs:
      setattr(self, attr, json_out.get(attr, ''))

  def ffprobe(self, *attrs) -> dict[str, str]:
    cmd = [
      ffprobe,
      '-hide_banner',
      '-select_streams', 'v:0',
      '-show_entries', f'stream={",".join(attrs)}',
      '-of', 'json',
      self.path
    ]
    try:
      out = subprocess.check_output(cmd, stderr=subprocess.PIPE).decode('utf-8')
      stream = json.loads(out).get('streams', [{}])[0]
      return {attr: stream.get(attr, '') for attr in attrs}
    except Exception as e:
      self._runtime_error = f'{e}'
    return {}
