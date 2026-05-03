import unittest
from shutil import rmtree
from pathlib import Path
from typing import Tuple

from fcpscene import PROXY_WIDTH, MIN_SCENE_SECS
from fcpscene.event_bus import EventBus
from fcpscene.video_attr import VideoAttr
from fcpscene.to_csv_clips import to_csv_clips
from fcpscene.to_fcpxml_clips import to_fcpxml_clips
from fcpscene.to_fcpxml_markers import to_fcpxml_markers
from fcpscene.to_fcpxml_compound_clips import to_fcpxml_compound_clips
from fcpscene.detect_scene_changes import detect_scene_changes, CutTimes
from fcpscene.to_file_clips import to_file_clips
from fcpscene.cuts_to_clips import cuts_to_file_clips

VIDEO_DIR_PLACEHOLDER = '__VIDEO_DIR_PLACEHOLDER__'


class FCPScene(unittest.TestCase):
  def setUp(self):
    self.fixtures = Path(__file__).resolve().parent / 'fixtures'

  def test_60fps(self): self._clips('60fps.mp4', '60fps-clips.fcpxml')

  def test_2997fps_and_filename_encoding(self): self._clips('2997 fps.mp4', '2997 fps.fcpxml')

  def test_60fps_compound(self): self._compound_clips('60fps.mp4', '60fps-compound-clips.fcpxml')

  def test_60fps_markers(self): self._markers('60fps.mp4', '60fps-markers.fcpxml')

  def test_60fps_csv(self): self._csv('60fps.mp4', '60fps.csv')

  def test_to_file_clips(self):
    cuts, v = self._detect('60fps_prores.mov')
    file_clips = cuts_to_file_clips(cuts)

    output_dir = v.path.parent / v.path.stem
    if output_dir.exists():
      rmtree(output_dir)

    to_file_clips(cuts, v, EventBus())
    exported = sorted(output_dir.glob(f'*{v.path.suffix}'))
    self.assertEqual(len(exported), len(file_clips), f'Expected {len(file_clips)} clips')

    for f in exported:
      clip = VideoAttr(f)
      self.assertAlmostEqual(clip.duration, 5, delta=0.1)

    rmtree(output_dir)


  def _clips(self, video, expected):
    cuts, v = self._detect(video)
    self._assert(to_fcpxml_clips(cuts, v), expected)

  def _compound_clips(self, video, expected):
    cuts, v = self._detect(video)
    self._assert(to_fcpxml_compound_clips(cuts, v), expected)

  def _markers(self, video, expected):
    cuts, v = self._detect(video)
    self._assert(to_fcpxml_markers(cuts, v), expected)

  def _csv(self, video, expected):
    cuts, v = self._detect(video)
    self._assert(to_csv_clips(cuts), expected)


  def _assert(self, actual, expected):
    self.assertEqual(
      actual.replace(str(self.fixtures), VIDEO_DIR_PLACEHOLDER),
      Path(self.fixtures / expected).read_text(encoding='utf-8'))

  def _detect(self, video) -> Tuple[CutTimes, VideoAttr]:
    v = VideoAttr(self.fixtures / video)
    cuts = detect_scene_changes(v, EventBus(), sensitivity=85, proxy_width=PROXY_WIDTH, min_scene_secs=MIN_SCENE_SECS)
    return cuts, v


if __name__ == '__main__':
  unittest.main()
