from .video_attr import VideoAttr
from .stamps_to_clips import stamps_to_clips
from .detect_cuts import TimelineStamps


def to_fcpxml_compound_clips(stamps: TimelineStamps, v: VideoAttr) -> str:
  """
  Blades a timeline given cut times in seconds and
  wraps each clip into its own compound clip.

  Background:
    In Final Cut Pro, compound clips are needed to export segments as individual
    files. Likewise, to send them to Apple Compressor for batch processing.

    The catch is that that works only when compound clips are visible on the
    Browser Viewer. So for that we embed an Event called "fcpscene", which must
    exist in the FCP Library before importing the FCPXML.
  """

  clips = stamps_to_clips(stamps, v)

  xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.13">
  <resources>
    <format id="r1"
      width="{v.width}"
      height="{v.height}"
      colorSpace="{v.fcp_color_space}"
      frameDuration="{v.fps_denominator}/{v.fps_numerator}s"/>
    <asset id="r2" start="0s" format="r1">
      <media-rep kind="original-media" src="{v.file_uri}"/>
    </asset>'''

  for c in clips:
    xml += f'''
    <media id="{c.ref_id}" name="{v.stem}_{c.seq}">
      <sequence format="r1" tcStart="0s">
        <spine>
          <asset-clip ref="r2" offset="0s" start="{c.offset}" duration="{c.duration}"/>
        </spine>
      </sequence>
    </media>'''

  xml += f'''
  </resources>
  <library>
    <event name="fcpscene">
      <project name="{v.stem}">
        <sequence format="r1" tcStart="0s">
          <spine>'''

  for c in clips:
    xml += f'''
            <ref-clip ref="{c.ref_id}" offset="{c.offset}" duration="{c.duration}"/>'''

  xml += f'''
          </spine>
        </sequence>
      </project>
    </event>
  </library>
</fcpxml>
'''
  return xml
