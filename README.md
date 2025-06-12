# Final Cut Pro Scene Detect

This program detects scene changes in videos and generates a Final Cut
Pro project file (FCPXML) with a timeline "bladed" at the scene changes.

For example, the timeline below has six clips (five cuts).

![](./README-example.jpg)



## Installation

### Requires `ffmpeg`

1. First, install [Homebrew](https://brew.sh). Then, in the Terminal type:

```shell
brew install ffmpeg
```

2. Download [scenes_to_fcp.py](https://raw.githubusercontent.com/ericfortis/final-cut-pro-scene-detect/refs/heads/main/scenes_to_fcp.py) from this repository.


## Running

In the Terminal app, type the following (adjust the file paths).

```shell
python3 ~/Downloads/scenes_to_fcp.py ~/Desktop/my-video.mp4
```

In that example, an `~/Desktop/my-video.fcpxml` project will
be created. That is, in the same directory the video is in.

Tip: If you don’t want to type file paths, just drag the
file into the Terminal — it will paste the path for you.



## Importing into Final Cut Pro
You can double-click the `.fcpxml` file to import it.

Or, import it from Final Cut Pro:

File &rarr; Import &rarr; XML &rarr;  Select the generated `.fcpxml`


## Options

### Threshold
Range: 0-100, Default: **15**

Lower values are more sensitive. This value sets the minimum
frame difference percentage used to detect scene changes.

```shell
python3 scene_to_fcp.py --threshold 30 my-video.mp4
```

### Proxy Width
Default: **320**

Lower values speed up analysis. This sets the temporary width
used to scale down the video during processing. It does **not**
modify your original video, and the proxy version is never saved.

```shell
python3 scene_to_fcp.py --proxy-width 240 my-video.mp4
```
