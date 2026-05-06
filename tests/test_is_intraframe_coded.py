import unittest
from pathlib import Path
from fcpscene.video_attr import VideoAttr


class IsIntraFrameCoded(unittest.TestCase):
  def setUp(self):
    self.fixtures = Path(__file__).resolve().parent / 'fixtures'

  def test_60fps_mp4_is_not_intra(self):
    v = VideoAttr(self.fixtures / '60fps.mp4')
    self.assertFalse(v.intraframe_coded)

  def test_60fps_prores_is_intra(self):
    v = VideoAttr(self.fixtures / '60fps_prores.mov')
    self.assertTrue(v.intraframe_coded)


if __name__ == '__main__':
  unittest.main()
