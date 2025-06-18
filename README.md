# Final Cut Pro Scene Detect

This program detects scene changes in videos and generates a Final Cut
Pro project file (FCPXML) with a timeline "bladed" at the scene changes.

For example, the timeline below has six clips (five cuts).

![](./README-example.jpg)


<br>

## Installation

1. Install [Homebrew](https://brew.sh)
2. In the Terminal app type:

```shell
brew tap ericfortis/fcpscene
brew install fcpscene
```


## Place your video in your `Home` or `Movies` directory
You video file should be in a directory Final Cut Pro can import from. By
default, your `Home` and `Movies` directories are allowed. **Otherwise**, you’ll
to need to **grant Full-Disk Access** to Final Cut Pro in order to import the
project. For example, if your video is in your _Desktop_, or _Documents_, or any
other TCC-protected folder, Final Cut Pro will crash when importing the `fcpxml` file.



## Running
In the Terminal, type:

```shell
fcpscene-gui
```

A 15-minute 4K video takes about 1 minute to run. You’ll see the found cut times
as it runs &mdash; if you hit "Stop and Save", you can save the Final Cut Pro
file with the cuts found so far.


![](README-gui.png)

### Importing into Final Cut Pro
Double-click the generated `.fcpxml` file to import it.

Or, import it from Final Cut Pro: File &rarr; Import &rarr; XML &rarr;  Select the generated `.fcpxml`

<br>



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

<br>

---


## License

[MIT](LICENSE) © 2025 Eric Fortis
