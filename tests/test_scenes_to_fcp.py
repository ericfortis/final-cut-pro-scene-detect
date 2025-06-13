import unittest
from pathlib import Path

from fcpscene.event_bus import EventBus
from fcpscene.scenes_to_fcp import scenes_to_fcp


class FCPScene(unittest.TestCase):
  def _test(self, video_file, expected_fcpxml):
    fixtures = Path(__file__).parent / 'fixtures'
    self.assertEqual(
      scenes_to_fcp(fixtures / video_file, EventBus(), sensitivity=85),
      Path(fixtures / expected_fcpxml).read_text(encoding='utf-8'))

  def test_60fps(self): self._test('60fps.mp4', '60fps.fcpxml')

  def test_2997fps(self): self._test('2997fps.mp4', '2997fps.fcpxml')


if __name__ == '__main__':
  unittest.main()
