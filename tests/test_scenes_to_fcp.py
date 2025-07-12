import unittest
from pathlib import Path

from fcpscene import PROXY_WIDTH, MIN_SCENE_SECS
from fcpscene.event_bus import EventBus
from fcpscene.video_attr import VideoAttr
from fcpscene.to_csv_clips import to_csv_clips
from fcpscene.to_fcpxml_clips import to_fcpxml_clips
from fcpscene.to_fcpxml_markers import to_fcpxml_markers
from fcpscene.to_fcpxml_compound_clips import to_fcpxml_compound_clips
from fcpscene.detect_cuts import detect_cuts

VIDEO_DIR_PLACEHOLDER = '__VIDEO_DIR_PLACEHOLDER__'


class FCPScene(unittest.TestCase):
  def setUp(self):
    self.fixtures = Path(__file__).resolve().parent / 'fixtures'

  def test_60fps(self): self._clips('60fps.mp4', '60fps-clips.fcpxml')

  def test_2997fps_and_filename_encoding(self): self._clips('2997 fps.mp4', '2997 fps.fcpxml')

  def test_60fps_compound(self): self._compound_clips('60fps.mp4', '60fps-compound-clips.fcpxml')

  def test_60fps_markers(self): self._markers('60fps.mp4', '60fps-markers.fcpxml')

  def test_60fps_csv(self): self._csv('60fps.mp4', '60fps.csv')

  def _clips(self, video, expected):
    stamps, v = self._detect(video)
    self._assert(to_fcpxml_clips(stamps, v), expected)

  def _compound_clips(self, video, expected):
    stamps, v = self._detect(video)
    self._assert(to_fcpxml_compound_clips(stamps, v), expected)

  def _markers(self, video, expected):
    stamps, v = self._detect(video)
    self._assert(to_fcpxml_markers(stamps, v), expected)

  def _csv(self, video, expected):
    stamps, v = self._detect(video)
    self._assert(to_csv_clips(stamps), expected)


  def _assert(self, actual, expected):
    self.assertEqual(
      actual.replace(str(self.fixtures), VIDEO_DIR_PLACEHOLDER),
      Path(self.fixtures / expected).read_text(encoding='utf-8'))

  def _detect(self, video):
    v = VideoAttr(self.fixtures / video)
    stamps = detect_cuts(v, EventBus(), sensitivity=85, proxy_width=PROXY_WIDTH, min_scene_secs=MIN_SCENE_SECS)
    return stamps, v


if __name__ == '__main__':
  unittest.main()
