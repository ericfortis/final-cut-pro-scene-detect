# Final Cut Pro XML Export Rubric

These are the projects used for reversing the export format.
These projects were manually cut in FCP and exported to XML.

Their source videos are in `tests/fixtures/`, which are the ones we test against.


## FCPXML Reference
https://developer.apple.com/documentation/professional-video-applications/fcpxml-reference


## Notes
- `media-rep.src` could be relative or absolute with `file://`
- Many tags and attributes are optional, so we let FCP compute them
- When determining the cut times we `ceil` the frame number. Otherwise, cuts will be 1-frame behind


The clip’s `[left and right]` edges, `offset` and `offset+duration`, are in timeline times.
On the other hand, `start` is in video time. For our purposes, `offset=start`.

## Event Name

If the event doesn't exist, the user will have to Clip => Reference New Parent
Clip in order to make them available on the Browser Viewer, (or 1-by-1
Right-Click => Reveal in Browser). The point of this tool is exporting all
compound clips as individual clips, so if they don't show up in the Browser they
can't be batch exported. Also, when creating a New Library, a new event is added
with the date (e.g. 7-4-25), so we default to that.
