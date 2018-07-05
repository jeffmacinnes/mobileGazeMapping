# Automated Dynamic Gaze Mapping Pipeline

A guide to using the analysis pipeline tools contained within this directory. These tools allow you to map gaze data from an egocentric coordinate frame (i.e. the coordinate system of the outward facing point-of-view camera on a wearable eye-tracker) to a fixed reference coordinate system (i.e. the coordinate system of a reference image found somewhere in the scene). 

Different manufacturers of wearable eye-trackers use different data formats. In order to make this pipeline generalizable across devices, it has been split up into 2 stages: **Preprocessing** and **Processing**. The preprocessing stage converts the data into a common format. As such, there is a unique preprocessing script for each of the supported manufacturers: Pupil Labs, SMI, and Tobii. The Processing stage takes the converted video and runs all subsequent gaze mapping steps on each frame of the recording. Each of these stages is explained in greater detail below.

The different eye-trackers also use different terminology. For the sake of sanity, here are some relevant terms and definitions used throughout this guide:

#### Relevant Terms:

* **World Camera**: The outward facing video camera attached to the eye-tracking glasses that records the participant's point-of-view. 
* **World Camera Coordinate System**: The 2D coordinate system of each frame from the world camera. Units are pixels and the origin is in the top-left
* **Reference Image**: The high quality, 2D, digital representation of the target stimulus in the environment that the participant is looking at. 
* **Reference Image Coordinate System**: The 2D coordinate system of the reference image. Units are pixels and the origin is in the top-left. 

---

## 1. Preprocessing

There are manufacturer-specific preprocessing scripts and instructions. In all cases, the output from preprocessing will be stored in a designated directory and contain the following files:

1. worldCamera.mp4: the video from the point-of-view scene camera on the glasses
2. frame_timestamps.tsv: table of timestamps for each frame in the world
3. gazeData_world.tsv: gaze data, where all gaze coordinates are represented w/r/t the world camera

#### Pupil Labs
*methods developed using Pupil Labs 120Hz Binocular wearable eye-tracker*

Data is recorded using Pupil software. The raw output from a recording session is saved in an directory specified within the software.

```
pl_preprocessing.py

usage: 
	python pl_preprocessing.py inputDir outputDir

required arguments:
	inputDir: path to where raw recording data is saved
	outputDir: path to where you want the preprocessed data saved to 
```

The input directory you specify should be the directory where Pupil software saves the raw recording. The output directory you specify is actually just the first part of the eventual output path. The preprocessing script will read the date and time of the raw data, and create two nested directories within the specified output directory. So, for example, if you you specify an output directory as:

```this/is/my/output/directory```

the preprocessed data will be written into a folder according to the data/time like:

```this/is/my/output/directory/[mo-day-yr]/[hr-min-sec]```

#### SMI
*methods developed using SMI ETG 2.6 Glasses*

Data is recorded to the miniSD card in the ETG. The first step is to remove the miniSD card and extract the data using the SMI BeGaze software. Once the miniSD card is plugged into a computer, launch the BeGaze software and drag the desired experiment data folder from the SD card into BeGaze. Once all runs have imported, choose `Export > Legacy: Export raw data to file` from the file menu. Check the following options in the export menu:

* Channels: L & R
* Binocular: Gaze Position
* Messages
* Frame Counter
* Event Info
 

The gaze data will be exported as a single text file per run. Create a new directory named like #-## (can be arbitrary numbers, just can't match existing directory...this is because we don't use the timestamp/date directory structure like we can with the other manufacturers). Copy all of the exported text files into this directory.

Go back to the SD card, copy the AVI movie recordings corresponding to each run, and paste them into the #-## directory you just created. 

```
smi_preprocessing.py

usage:
	python smi_preprocessing.py inputDir sessionNum outputDir
	
required arguments:
	inputDir: path the directory containing AVI movie recordings and exported text files
	sessionNum: session number of the SMI data (aka run number)
	outputDir: path to where you want the preprocessed data saved to
```

The preprocessed SMI data will be written the output directory you specify. The output directory you specify is actually just the first part of the eventual output path. The preprocessing script will read the ##-# and session number of the raw data, and create two nested directories within the specified output directory.

So, for example, if you you specify an output directory as:

```this/is/my/output/directory```

the preprocessed data will be written into a folder according to the the input directories like:

```this/is/my/output/directory/[##-#]/[sessionNumber]```

This allows us to approximate the same output directory structure that is used with the Tobii and Pupil Labs eye-trackers. 

#### Tobii
*methods developed using Tobii Pro Glasses 2*

Data is recorded to the SD card in the Tobii recorder. The first step is to insert the SD card into a computer and find the appropriate data recording directory. Because of the nested directory structure and seemingly random alphanumeric strings Tobii uses to name the directories, it may be easiest to sort the directories on the SD card according to Date Modified. Find the subdirectory in the "recordings" directory that corresponds to your session, and copy this subdirectory to somewhere accessible on your computer. This is your raw input directory for the next step. (Alternatively, you can point the preprocessing script to raw input directory on the SD card itself)

```
tobii_preprocessing.py

usage:
	python tobii_preprocessing.py inputDir outputDir
	
required arguments:
	inputDir: path to the raw data directory
	outputDir: path to where you want the preprocessed data saved to
```

The output directory you specify is actually just the first part of the eventual output path. The preprocessing script will read the date and time of the raw data, and create two nested directories within the specified output directory. So, for example, if you you specify an output directory as:

```this/is/my/output/directory```

the preprocessed data will be written into a folder according to the data/time like:

```this/is/my/output/directory/[mo-day-yr]/[hr-min-sec]```


## 2. Processing

After **preprocessing** has completed, confirm you have a directory that contains the following files (regardless of which preprocessing script you used):

1. worldCamera.mp4: the video from the point-of-view scene camera on the glasses
2. frame_timestamps.tsv: table of timestamps for each frame in the world
3. gazeData_world.tsv: gaze data, where all gaze coordinates are represented w/r/t the world camera


Next, you can run the **processing** script. This script will loop through every frame of the worldCamera.mp4 video. For each frame, it will attempt to find matching features with a supplied reference image. If a sufficient number of matches are found, it will create a transformation to map between the frame and reference image. That transformation will then be used to map the gaze data corresponding to that frame to the reference image coordinate sytems

```
processsData.py

usage:
	python processsData.py preprocessedDir outputDir referenceImage
	
required arguments:
	preprocessedDir: path to directory containing preprocessed data
	outputDir: path to where you want the processed data saved to
	referenceImage: path to reference image
``` 
Afterwards you will find the following files in the specified output directory:


1. world_gaze.m4v - world camera with gaze overlaid
2. ref_gaze.m4v - reference image with mapped gaze overlaid
3. ref2world_mapping.m4v - video showing the reference image projected into the world camera video. useful for debugging, since it shows how well the mapping worked on each frame
4. gazeData_mapped.tsv - text file with the gaze data expressed in both coordinate systems: world camera and reference image


