import unittest
from pathlib import Path
from fcpscene.video_attr import VideoAttr


class VideoAttributes(unittest.TestCase):
  def setUp(self):
    self.fixtures = Path(__file__).resolve().parent / 'fixtures'
    self.v = VideoAttr(self.fixtures / '60fps.mp4')

  def test_name(self):
    self.assertEqual(self.v.name, '60fps')

  def test_summary(self):
    self.assertEqual(self.v.summary, '1920x1080    60fps    30s    H.264')

  def test_colorspace(self):
    self.assertEqual(self.v.fcp_color_space, '1-1-1')

  def test_is_not_intraframe(self):
    self.assertFalse(self.v.intraframe_coded)

  def test_prores_is_intraframe(self):
    v = VideoAttr(self.fixtures / '60fps_prores.mov')
    self.assertTrue(v.intraframe_coded)

if __name__ == '__main__':
  unittest.main()
