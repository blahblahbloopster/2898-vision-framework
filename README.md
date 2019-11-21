# How To Use

##### tl;dr:
Too bad, read it anyways

##### Vocabulary in opencv and this document:
**contour** - specially formatted list of points, precisely how it must be formatted depends on
the state of the moon for all I know

**solvepnp** - a function that finds your perspective from the target screen coordinates and it's
real-world dimensions

**distortion** / camera matrix - distortion is kinda how the view is lensed, and the camera matrix
describes this distortion and lets you correct for it

**EasyContour** - a class I made that makes contour handling a lot easier.  You initialize it with
a contour in any format, and then you can tell it to format it in the standard opencv way or
any other way using the format method.

**array** - a numpy array, usually has a specific datatype specified by
```
np.array(list, dtype=np.blah)
```
#### How this framework works:
There is a multistage pipeline that has 4 stages: Getting the image, processing the image,
and filtering/solving
The reason for the pipeline is so that it can entirely utilize multiple CPU cores, very
important when working on a pi.
You just need to modify the last stage, filtering/solving.
What you need to do is get some test footage, make a system for filtering out other contours,
and corner identification.  You also need to fill in the real-world dimensions of the target,
as well as calibrate the camera.  Finally, you will want to benchmark it ON YOUR TARGET SYSTEM.
You do this by running it like so:
```
python3 main.py --benchmark
```
It will loop the input video 20 times. (currently only recordings are supported for benchmarking)
Different systems have different CPUs, GPUs (can affect results when opencv is compiled
for CUDA), and RAM.  Benchmarking it on your computer and optimizing there is a good idea,
but make sure to check it on your target platform.

**How to do that**:
Getting some test footage is relatively straightforward, just make a target and film it.
However, it is very important to choose the right (or at least consistent) camera settings.
Write them down!

To calibrate the camera, print out a chessboard and take pictures of it with the camera.
Then use an internet script to get the camera matrix and distortion.  Keep these in a variable
somewhere.

Alright, so now the tricky part: corner detection.  The way to do this is to try to find a
point that is consistently at the top, bottom, or one of the sides, like the diagram below:

<!-- language: lang-none -->
       -> /**--_ <-
         /     /
        /     /
       /     /
    -> **--_/ <-

See how the top point will always be at the top?  This lets you easily find the contours with
a simple maximum function, like so:
```
max(list_of_points, key=lambda a: a[1])
```
What this does is it finds the point with the maximum y value.  This will find the top point.
(the coordinate system in opencv starts at the bottom left corner)  You can make similar code
to find the other sides.  If necessary, you can rotate all the points to find the corner and
then rotate the corner points back, but this is both computationally expensive and hard to do.

Contour filtering prevents your code from looking at a person in the stands and recognizing
them as a target.  How you should do this is loop over your list of contours and add them
to a new list (or not) based on some criteria.  These criteria can include:
size
aspect ratio
position
number of points
area
perimeter
area/perimeter ratio
and so on.  These are also important for when your robot sees multiple targets at once.

Contour pairing is for when the game has targets in pairs, like the 2019 season:

<!-- language: lang-none -->
        /*-_            _-*\
       /   /            \   \
      /   /              \   \
      *-_/                \_-*
Now there's two targets you have to keep track of!  How I did this for 2019 is I had a list
of all the contours.  It would go through, and find the closest contour to each one.  Then,
it would go through those, and find if they matched.
if the robot saw this, it would do the following:
<!-- language: lang-none -->
        /*/     \*\              /*/
       /_/       \_\            /_/

1. find closest

<!-- language: lang-none -->
     /*/---->\*\<-------------/*/
    /_/<------\_\            /_/

2. check if they match
<!-- language: lang-none -->
     /*/---->\*\<-------------/*/
    /_/<------\_\            /_/
       matches          doesn't match
   (goes both ways)   (only goes one way)

The paired ones would be stored together, and the extraneous contour would be removed.