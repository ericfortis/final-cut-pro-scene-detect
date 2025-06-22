# Final Cut Pro Scene Detector (fcpscene)

This program detects scene changes in videos and generates a Final Cut Pro
project file (FCPXML) with a timeline "bladed" at the scene changes. For
example, the timeline below has six clips (five cuts).

![](./README-example.jpg)


## Alternative Tools

#### Davinci Resolve Studio
In Davinci Resolve Studio, the paid version, you can run scene detection and export to Final Cut Pro.

#### Different Approach
Instead of cutting the timeline, there are many tools for splitting the video into small videos.

<details>
<summary><b>Kdenlive</b> (for programmers)</summary>

**Caveats**: There are many 1-frame off cuts due to rounding errors. Especially in non-integer frame rates such as 29.97
- Drop the video into the Project Bin &rarr; Right-click &rarr; Clip Jobs &rarr; Automatic Scene Split
- Expand the video on the Project Bin &rarr; Select all sequences &rarr; Drop them to the timeline
- File &rarr; OpenTimelineIO Export
- Convert the `.otio` to `.fcpxml` with [this Python adapter](https://github.com/OpenTimelineIO/otio-fcpx-xml-adapter)
</details>

<br>

## Installation

1. Install [Homebrew](https://brew.sh)
2. In the Terminal app type:

```shell
brew tap ericfortis/fcpscene
brew install fcpscene
```

That will install two programs. They do the same thing.
- `fcpscene-gui` graphical user interface
- `fcpscene` command-line (for batch processing)


## Place your video in your 📂`Home` or 📂`Movies` directory
You video file should be in a directory Final Cut Pro can access &mdash; your
📂`Home` and 📂`Movies` directories are allowed by default. **Otherwise, grant
Full-Disk Access** to Final Cut Pro. If not, Final Cut will crash when importing
the project. For example, that will happen if your video is in your ⚠️
_Desktop_, ⚠️ _Documents_, or any other TCC-protected folder, regardless of
where the `.fcpxml` file is.



## Running
In the Terminal, launch the program by typing:

```shell
fcpscene-gui
```
![](README-gui.png)

A 15-minute 4K 60fps video takes about 1 minute to run on a 14-core M4. You’ll
see the found cut times as it runs &mdash; if you hit "Stop and Save", a Final
Cut Pro project file with the cuts found so far will be saved 💾.

The sensitivity should be around 65 to 90%. Start with 85% and increase it if
it’s missing cuts. By the way, 1-frame cuts are ignored regardless of the
percent. Also, the sensitivity doesn’t affect speed.


### Importing into Final Cut Pro
Two options:

- Double-click the generated `.fcpxml` file.
- Or, from Final Cut Pro, File &rarr; Import &rarr; XML &rarr;  Select the generated `.fcpxml`

You can delete the `.fcpxml` afterward.

<br>



<details>
<summary><strong>How to run the command-line program?</strong></summary>

## Running the command-line</h2>

```shell
fcpscene ~/Movies/my-video.mp4
```

That example generates an `~/Movies/my-video.fcpxml` project.

Tip: If you don’t want to type the video file path, just drag the
file into the Terminal — it will paste the path for you.


### Options
#### Output filename
Default: `<video-dir>/<video-name>.fcpxml` (i.e., in the same directory the video is in)

```shell
fcpscene my-video.mp4 --output my-project.fcpxml
```

#### Sensitivity
Range: 0-100, Default: **85**

This value sets the frame difference percentage used to detect scene changes.

```shell
fcpscene --sensitivity 70 my-video.mp4
```

#### Proxy Width
Default: **320**

Lower values speed up analysis. This sets the temporary width
used to scale down the video during processing. It does **not**
modify your original video, and the proxy version is never saved.

```shell
fcpscene --proxy-width 240 my-video.mp4
```

### Tip: Batch Processing

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

Also, keep your computer in a well ventilated area. `fcpscene` uses `ffmpeg`
behind the scenes, which will 🔥 max out your CPU cores.

</details>

<br>


## Final Cut Pro Tips

<details>
<summary><b>Joining Clips</b></summary>
In iMovie there’s (Cmd+J), but in Final Cut we don’t _join_ clips, we _delete_ cuts.

1. Pick the Trim Tool (T)
2. Select both edges by clicking between two clips
3. Hit **Delete**

Alternatively, you can drag those two edges until they touch the adjacent clip.

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

## License

[MIT](LICENSE) © 2025 Eric Fortis
