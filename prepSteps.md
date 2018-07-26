# Steps for submitting to JOSS

[https://joss.theoj.org/about](https://joss.theoj.org/about)

* Software available in open repo (e.g. GitHub)
* Author short markdown paper:
	* title
	* summary - describe high-level functionality, and purpose of the software.
	* author names/affiliations
	* key references, including a link to the software archive
	* ~250-1000 words total
* Metadata file to include in repo


# Reviewer Guidelines

* Is there a OSI approved license?
* Documentation should be sufficieint to understand core functionality of the software under review. High-level overview of this documentation should be included in a README file. There should be:
	* Statement of need: what problem does the software solve? who is the target audience?
	* Installation instructions: clearly-stated list of dependencies. Ideally in a requirements.txt file
	* Example Usage: examples of how to use the software in real-world analysis problems
	* Are all functions documented properly?
	* Tests: automated test suite hooked up to external service like Travis-CI or similar. OR documented manual steps that can be followed to check the expected functionality of the software (e.g. sample input file to assert behavior)
	* Clear guidelines for 3rd parties wishing to: Contribute, Report Issues or problems, or Seek Support


# Heres the plan

## repo structure

Heres the structure we'll use for the repository:

```
├── LICENSE  
├── README.md  
├── testData  
│   ├── frame_timestamps.tsv
│   ├── gazeData_world.tsv
│   ├── worldCamera.mp4
│   └── referenceImage.jpg 
├── preprocessing
│   ├── rawData
│   ├── pl_preprocessing.py
│   ├── smi_preprocessing.py
│   └── tobii_preprocessing.py
└── processData.py

```

* `README.md`: include the all of the relevant overview and usage guidelines in this file

* `testData/`: This directory will contain an abbreviated version of *preprocessed* data that can easily and quickly be used to verify that the `processData.py` script is working properly
	* Will include `frame_timestamps.tsv`, `gazeData_world.tsv`, `worldCamera.mp4` preprocessed files, as well as `referenceImage.jpg` the reference image that `processData.py` will attempt to find in the image

* `preprocessing/`: This directory will contain preprocessing scripts customized for the 3 different manufacturers of mobile devices: Pupil Labs, SMI, and Tobii. Since we don't have great examples of short, raw data for each of these devices (plus the files would be way too big to include in the repo) we should talk about these scripts as bonuses that we are including (and maybe link to a zip with sample raw data from each manufacturer?)

* `processData.py`: Main script. Given inputs like whats found in `testData` you can fully map the gaze data to the reference image in each frame of the video. 

## Todo:

- Update all code documentation using Numpy Documentation standards and flake8 to confirm PEP8 standards. 
- Figure out proper dependencies, and make a requirements.txt file
- Make abbreviated version of the testData
- Make sure there's a correct license file
- Make a thorough README file that includes: overview, installation instructions, example usage, and clear guidelines for 3rd party contributions, issue reporting, or support. 

n