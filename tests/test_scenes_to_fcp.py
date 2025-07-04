import unittest
from pathlib import Path

from fcpscene import PROXY_WIDTH
from fcpscene.event_bus import EventBus
from fcpscene.video_attr import VideoAttr
from fcpscene.fcpxml_clips import fcpxml_clips
from fcpscene.detect_scene_cut_times import detect_scene_cut_times
from fcpscene.fcpxml_compound_clips import fcpxml_compound_clips

VIDEO_DIR_PLACEHOLDER = '__VIDEO_DIR_PLACEHOLDER__'


class FCPScene(unittest.TestCase):
  def setUp(self):
    self.fixtures = Path(__file__).resolve().parent / 'fixtures'

  def test_60fps(self): self._test_clips('60fps.mp4', '60fps.fcpxml')

  def test_2997fps(self): self._test_clips('2997 fps.mp4', '2997 fps.fcpxml')  # tests filename encoding too

  def test_60fps_compound(self): self._test_compound_clips('60fps.mp4', '60fps-compound.fcpxml')

  @staticmethod
  def _detect(v: VideoAttr):
    return detect_scene_cut_times(v.path, v.duration, EventBus(), sensitivity=85, proxy_width=PROXY_WIDTH)

  def _assert(self, xml, expected_fcpxml):
    self.assertEqual(
      xml.replace(str(self.fixtures), VIDEO_DIR_PLACEHOLDER),
      Path(self.fixtures / expected_fcpxml).read_text(encoding='utf-8')
    )

  def _test_clips(self, video_file, expected_fcpxml):
    v = VideoAttr(self.fixtures / video_file)
    self._assert(fcpxml_clips(self._detect(v), v), expected_fcpxml)

  def _test_compound_clips(self, video_file, expected_fcpxml):
    v = VideoAttr(self.fixtures / video_file)
    self._assert(fcpxml_compound_clips(self._detect(v), v, '12-30-25'), expected_fcpxml)


if __name__ == '__main__':
  unittest.main()
