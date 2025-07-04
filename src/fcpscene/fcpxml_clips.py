from .video_attr import VideoAttr
from .cuts_to_clips import cuts_to_clips


def fcpxml_clips(cut_times: list[float], v: VideoAttr) -> str:
  clips = cuts_to_clips(cut_times, v)

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
    </asset>
  </resources>
  <library>
    <event>
      <project name="{v.stem}">
        <sequence format="r1" tcStart="0s">
          <spine>'''

  for c in clips:
    xml += f'''
            <asset-clip ref="r2" offset="{c.offset}" start="{c.offset}" duration="{c.duration}"/>'''

  xml += f'''
          </spine>
        </sequence>
      </project>
    </event>
  </library>
</fcpxml>
'''
  return xml
