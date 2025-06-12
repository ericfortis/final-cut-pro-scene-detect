import unittest
from pathlib import Path
from scenes_to_fcp import scenes_to_fcp


class TestFCPXMLGeneration(unittest.TestCase):
  def test_fcpxml_fixtures(self):
    test_cases = [
      ('fixtures/60fps.mov', 'fixtures/60fps.fcpxml'),
      ('fixtures/2997fps.mov', 'fixtures/2997fps.fcpxml'),
    ]
    for input_file, expected_file in test_cases:
      with self.subTest(input=input_file):
        self.assertEqual(
          scenes_to_fcp(input_file),
          Path(expected_file).read_text(encoding='utf-8'))

if __name__ == '__main__':
  unittest.main()
