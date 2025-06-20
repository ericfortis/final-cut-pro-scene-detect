import unittest
from pathlib import Path

from fcpscene.event_bus import EventBus
from fcpscene.scenes_to_fcp import scenes_to_fcp

VIDEO_DIR_PLACEHOLDER = '__VIDEO_DIR_PLACEHOLDER__'


class FCPScene(unittest.TestCase):
  def _test(self, video_file, expected_fcpxml):
    fixtures = Path(__file__).resolve().parent / 'fixtures'
    actual = (scenes_to_fcp(fixtures / video_file, EventBus(), sensitivity=85)
              .replace(str(fixtures), VIDEO_DIR_PLACEHOLDER))
    self.assertEqual(
      actual,
      Path(fixtures / expected_fcpxml).read_text(encoding='utf-8'))

  def test_60fps(self): self._test('60 fps.mp4', '60fps.fcpxml') # tests filename encoding too

  def test_2997fps(self): self._test('2997fps.mp4', '2997fps.fcpxml')


if __name__ == '__main__':
  unittest.main()
