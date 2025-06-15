# Final Cut Pro Scene Detect

This program detects scene changes in videos and generates a Final Cut
Pro project file (FCPXML) with a timeline "bladed" at the scene changes.

For example, the timeline below has six clips (five cuts).

![](./README-example.jpg)


<br>

## Installation

### Requires `ffmpeg`

1. First, install [Homebrew](https://brew.sh). Then, in the Terminal type:

```shell
brew tap ericfortis/fcpscene
brew install fcpscene
```

## Running
In the Terminal app, type:

```shell
fcpscene-gui
```

![](README-gui.png)

### Importing into Final Cut Pro
Double-click the generated `.fcpxml` file to import it.

Or, import it from Final Cut Pro: File &rarr; Import &rarr; XML &rarr;  Select the generated `.fcpxml`

<br>
---



## Or, Run the CLI

```shell
fcpscene ~/Desktop/my-video.mp4
```

In that example, an `~/Desktop/my-video.fcpxml` project will
be created. That is, in the same directory the video is in.

Tip: If you don’t want to type file paths, just drag the
file into the Terminal — it will paste the path for you.



### Options

#### Sensitivity
Range: 0-100, Default: **85**

This value sets the frame difference percentage used to detect scene changes.

```shell
python3 scenes_to_fcp.py --sensitivity 70 my-video.mp4
```

#### Proxy Width
Default: **320**

Lower values speed up analysis. This sets the temporary width
used to scale down the video during processing. It does **not**
modify your original video, and the proxy version is never saved.

```shell
python3 scenes_to_fcp.py --proxy-width 240 my-video.mp4
```

## License

[MIT](LICENSE) © 2025 Eric Fortis
