import unittest
from fcpscene.time_utils import format_seconds


m = 60
h = 60 * m


class FormatSeconds(unittest.TestCase):
  def _test_no_decimals(self, seconds, expected):
    self.assertEqual(format_seconds(seconds, 0), expected)

  def _test_two_decimals(self, seconds, expected):
    self.assertEqual(format_seconds(seconds, 2), expected)


  def test_zero_no_decimals(self): self._test_no_decimals(0, '0s')

  def test_rounds_s_no_decimals(self): self._test_no_decimals(4.6, '5s')


  def test_zero(self): self._test_two_decimals(0, '0s')

  def test_rounds_s(self): self._test_two_decimals(1.209, '1.21s')

  def test_strips_trailing_zeroes(self): self._test_two_decimals(1.2000, '1.2s')

  def test_s(self): self._test_two_decimals(1, '1s')

  def test_m(self): self._test_two_decimals(m, '1m')

  def test_h(self): self._test_two_decimals(h, '1h')

  def test_m_s(self): self._test_two_decimals(m + 2, '1m2s')

  def test_h_m_s(self): self._test_two_decimals(h + 2 * m + 3, '1h2m3s')

  def test_days(self): self._test_two_decimals(25 * h, '25h')


if __name__ == '__main__':
  unittest.main()
