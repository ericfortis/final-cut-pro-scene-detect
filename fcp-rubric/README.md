# Final Cut Pro XML Export Rubric

These are the projects used for reversing the export format.
These projects were manually cut in FCP and exported to XML.

Their source videos are in `tests/fixtures/`, which are the ones we test against.


## FCPXML Reference
https://developer.apple.com/documentation/professional-video-applications/fcpxml-reference


## Notes
- `media-rep.src` could be relative or absolute with `file://`
- `format.name` must be a predefined preset. We use a dummy one because we use
  attributes that override it (width, height, frameDuration)
- When determining the cut times we `ceil` the frame number. Otherwise, cuts will be 1-frame behind
- Many tags and attributes are optional, so we let FCP compute them
