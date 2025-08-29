# fcpscene

## Final Cut Pro Scene Detector

This program finds scene changes in videos and generates a Final Cut Pro
project with cuts at those scene changes, using either compound or normal clips.

![](README-gui.png)

That example processed a video with five cuts, so the timeline has six compound
clips.

![](./README-example.png)


## Motivation
I wanted to increase the frame rate of old videos using Final Cut’s Optical Flow
(Machine Learning) interpolation and I faced two main problems. First, it messes
up scene changes by adding a transition — even if they are bladed. Second,
it needs hundreds of gigabytes of disk space.

<details>
<summary>Third minor problem</summary>

Changing frame rate in FCP messes up clip boundaries, but that’s solvable
pre-encoding in ProRes. By the way, FCP doesn’t support changing frame rate, but
we can create a new project with the desired frame rate and paste the old
project timeline there. </details>

To solve those problems we need to send individual clips to Apple
Compressor, and let it process the frame rate change and interpolation. But how?

First, we’d have to tediously cut the timeline, and then manually wrap each
clip in its own compound clip so we can batch send them to Compressor.

`fcpscene` automates that process.


## Before Installing
I haven’t confirmed it myself, but DaVinci Resolve Studio (the paid version) may
be a viable alternative.


## Installation
`fcpscene` is installed via Homebrew.

1. Install [Homebrew](https://brew.sh)
2. In the Terminal app type:

```shell
brew tap ericfortis/fcpscene
brew install fcpscene
```

Launch it by typing:
```shell
fcpscene --gui
```

Optionally, install the **fcpscene.app** droplet.

<img src="fcpscene.app/icon.svg" width="60"/>

In Finder (not in the Terminal), Go &rarr; **Go to Folder** and type **/opt/homebrew/opt/fcpscene/**

Then move **fcpscene.app** to your Applications folder.



## Before Running

### 1. Create an event called "fcpscene" in your Library

<details>
<summary>Details</summary>
This is only needed for compound clips. Without that event you won’t see them in
FCP Browser View, which is where you need to select them for batch sending to
Compressor.

Otherwise, you have two options:
1. Load the project again. The first load creates the **fcpscene** event.
2. Or, **Select All** compound clips in the timeline, and **Clip** &rarr;
   **Reference New Parent Clip**. But that appends the word "copy" to their
   names.
</details>


### 2. Place your video in your 📂`Home` or 📂`Movies` directory
<details>
<summary>Details</summary>
Your video file should be in a directory Final Cut Pro can access &mdash; your
📂Home and 📂Movies directories are allowed by default. Otherwise, grant
Full-Disk Access to Final Cut Pro — without it, Final Cut will crash when
importing the project. For example, that will happen if your video is in your
⚠️Desktop, ⚠️Documents, or any other TCC-protected folder, regardless of where
the .fcpxml file is.
</details>


## Running
The **fcpscene.app** is a droplet, which means you can drag a video file onto it,
or right-click the video file and select **Open With** &rarr; **fcpscene.app**

A 15-minute 4K 60fps video takes about a minute to run on a 14-core M4. You’ll
see the detected cut times as it runs — if you hit "Stop", you can still export
a Final Cut Pro project file with the cuts found so far.

The **Sensitivity** should be around 65 to 90%. Start with 85% and increase it
if it’s missing cuts. Pair it with **Min Scene Seconds** so you can have a high
sensitivity while ignoring false positives. Those options have no effect on the
processing speed.

You can delete the exported `.fcpxml` after the project is loaded in Final Cut.

<br>

## Command-Line Program

The `fcpscene` command line program has more features than the GUI app. Also,
it’s convenient for batch processing videos.

<details>
<summary>Details</summary>

## Usage Example

```shell
fcpscene ~/Movies/my-video.mp4
```

That example generates an `~/Movies/my-video.fcpxml` project.

Tip: If you don’t want to type the video file path, just drag the
file into the Terminal — it will paste the path for you.

<br/>

### Options

For the full list of options, type: `fcpscene --help`

<br/>

#### Output Filename
Default: `<video-dir>/<video-name>.fcpxml` (i.e., in the same directory the video is in)

```shell
fcpscene my-video.mp4 --output my-project.fcpxml
```

<br/>

#### Sensitivity
Range: 0-100, Default: **88**

This value sets the frame difference percentage used to detect scene changes.

```shell
fcpscene --sensitivity 70 my-video.mp4
```

<br/>

#### Min Scene Seconds
Default: **0.6**

Ignores scene changes that are shorter than the value. This is handy for having
a high-sensitivity while avoiding false-positives.

```shell
fcpscene --min-scene-seconds 2 my-video.mp4
```

<br/>

#### Proxy Width
Default: **320**

Lower values speed up analysis. This sets the temporary width used to scale down
the video during processing (without modifying the original file).

```shell
fcpscene --proxy-width 240 my-video.mp4
```

<br/>

#### Mode
Choices:
- **clips**: Normal clips (default)
- **compound-clips**: Wraps each clip in its own compound clip
- **markers**: Only add markers
- **count**: Print scene changes count (no file is saved)
- **list**: Print scene changes times (no file is saved)

```shell
fcpscene --mode markers my-video.mp4
```

<br/>

#### Quiet
Do not print video summary and progress.

```shell
fcpscene --quiet my-video.mp4
```

<br/>

### Batch Processing

<br/>

#### Generating FCPXML

In the Terminal, you can type a snippet like this to run `fcpscene` on all the
`.mp4` videos in your 📂`~/Movies` directory excluding subdirectories.

```shell
cd ~/Movies
for vid in *.mp4; do
  caffeinate fcpscene "$vid"
done
```

Typing `caffeinate` is optional. It’s a macOS built-in program that prevents the
computer from sleeping while it’s running a task.

Also, keep your computer in a well-ventilated area. `fcpscene` uses `ffmpeg`
under the hood, which will max out your CPU cores 🔥.

<br/>

#### Counting cuts
I use this command to check if there are stray frames in single-scene files. For
example, when retiming with Machine Learning in Compressor, some end up with a
random frame. So with this script I can print videos with cuts and their count.

```shell
cd ~/Movies/video_foo
for f in *.mov; do
  n_cuts=$(fcpscene --quiet --min-scene-seconds 0 --mode count "$f")
  if [[ $n_cuts != 0 ]]; then
    echo "$f" "$n_cuts"
  fi
done
```

Example output:
```sh
video_foo_018.mov 1
video_foo_064.mov 2
video_foo_073.mov 2
```

<br/>


#### Listing cuts
Same as above but printing cut times

```shell
cd ~/Movies/video_foo
for f in *.mov; do
  cuts=$(fcpscene -q -mss 0 --mode list "$f")
  if [[ $cuts ]]; then
    echo "$f" "$cuts"
  fi
done
```
```sh
video_foo_018.mov 0.0166667
video_foo_064.mov 0.866667 2.066667
video_foo_073.mov 0.866667 2.066667
```

</details>

<br>


## Final Cut Pro Tips

<details>
<summary><strong>Batch Export Compound Clips</strong></summary>

1. Select the all the **Compound Clips** you want to export.
![](README-tip-fcp-batch-export-1.png)

2. **File** &rarr; **Share N Clips**
![](README-tip-fcp-batch-export-2.png)
</details>

<br/>


<details>
<summary><b>Joining Clips</b></summary>
In iMovie there’s (Cmd+J), but in Final Cut we don’t _join_ clips, we _delete_ cuts.

1. Pick the Trim Tool (T)
2. Select both edges by clicking between two clips
3. Hit **Delete**

Alternatively, you can drag each clip edge until it touches the adjacent one to
remove the cut.

![](README-tip-fcp-join-clips.png)
</details>

<br/>


<details>
<summary><b>Batch Clip Rename</b></summary>

1. Select the clips you want to rename
2. Window &rarr; Show in Workspace &rarr; Inspector (Cmd+4)
3. Go to the ⓘ Info Inspector Tab (Ctrl+Tab)
4. Type a name

![](README-tip-fcp-batch-rename.png)
</details>


<br>

## Alternative Tools

#### Davinci Resolve Studio
In Davinci Resolve Studio, the paid version, you can run scene detection and export to Final Cut Pro.

#### Different Approach
Instead of cutting the timeline, there are many tools for splitting the video into small videos.

<details>
<summary><b>Kdenlive</b> (for programmers)</summary>

**Caveats**: There are many 1-frame-off cuts due to rounding errors. Especially with non-integer frame rates such as 29.97
- Drop the video into the Project Bin &rarr; Right-click &rarr; Clip Jobs &rarr; Automatic Scene Split
- Expand the video on the Project Bin &rarr; Select all sequences &rarr; Drop them to the timeline
- File &rarr; OpenTimelineIO Export
- Convert the `.otio` to `.fcpxml` with [this Python adapter](https://github.com/OpenTimelineIO/otio-fcpx-xml-adapter)
</details>


<br>

## Acknowledgments
- [FFmpeg](https://ffmpeg.org/) for detecting scene changes
- [tkinter](https://docs.python.org/3/library/tkinter.html) for the GUI
- [Python](https://www.python.org/) programming language
- [AppleScript](https://developer.apple.com/library/archive/documentation/AppleScript/Conceptual/) programming language
- [Homebrew](https://brew.sh/) for distribution


## License

[MIT](LICENSE) © 2025 Eric Fortis
