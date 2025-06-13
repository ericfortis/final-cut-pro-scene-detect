class Fcpscene < Formula
  include Language::Python::Virtualenv

  desc "Final Cut Pro scene cut detector"
  homepage "https://github.com/ericfortis/final-cut-pro-scene-detect"
  url "https://github.com/ericfortis/final-cut-pro-scene-detect/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "ec94f424efd642f650256ee56e319e401aeaaf8287e277ea77df5f4597e4ab39"
  license "MIT"

  depends_on "python@3.11"
  depends_on "ffmpeg"

  def install
    virtualenv_install_with_resources
    bin.install_symlink libexec/"bin/fcpscene" => "fcpscene"
    bin.install "bin/fcpscene-gui"
  end

  test do
    system "#{bin}/fcpscene", "--help"
    assert_predicate bin/"fcpscene-gui", :exist?
  end
end
