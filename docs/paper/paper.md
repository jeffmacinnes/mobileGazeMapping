---
title: 'Mobile Gaze Mapping: A Python package for mapping mobile gaze data to a fixed target stimulus'
tags:
  - Python
  - openCV
  - computer vision
  - eye tracking
  - mobile eye tracking
authors:
  - name: Jeff J MacInnes
    affiliation: "1, 2" # (Multiple affiliations must be quoted)
  - name: Shariq Iqbal
    affiliation: 3
  - name: John Pearson
    affiliation: 2
  - name: Elizabeth N. Johnson
    affiliation: "2, 4"
affiliations:
 - name: Institute for Learning and Brain Sciences, University of Washington, Seattle, WA
   index: 1
 - name: Center for Cognitive Neuroscience, Duke University, Durham, NC
   index: 2
 - name: University of Southern California, Los Angeles, CA
   index: 3
 - name: Wharton Neuroscience Initiative, University of Pennsylvania, Philadelphia, PA
   index: 4

date: 3 August 2018
bibliography: paper.bib
---


# Summary
Mobile eye-trackers allow for measures like gaze position to be recorded under naturalistic conditions where an individual is free to move around. Gaze position is typically recorded relative to an outward facing camera attached to the eye-tracker and approximating the point-of-view of the individual wearing the device. As such, gaze position is recorded relative to the individual's position and orientation, which changes as the participant moves. Since gaze position is recorded without any reference to fixed objects in the environment, this poses a challenge for studying how an individual views a particular stimulus over time. 

This toolkit addresses this challenge by automatically identifying the target stimulus on every frame of the recording and mapping the gaze positions to a fixed representation of the stimulus. 

It does this by identifying matching keypoints between the reference stimulus and each frame of the video. Keypoints are obtained using the Scale Invariant Feature Transform algorithm (SIFT)[@Lowe2004], and matches between keypoints are found using the Fast Approximate Nearest Neighbor search algorithm (FLANN)[@visapp09], both implemented in OpenCV[@opencv_library]. (We note that while use of the SIFT algorithm is free for non-commercial, research, and educational purposes, all commercial applications require a purchased license.) 

Once matching keypoints have been identified, we determine the 2D linear transformation that maps keypoints from the video frame to key points on the reference image. Once determined, this same transformation is applied to the gaze position sample corresponding to the given video frame, resulting in gaze position being expressed in terms of the pixel coordinate system of the reference image. 

For a more detailed overview of this process, and the results of using this toolkit to compare gaze accuracy and precision across 3 popular models of mobile eye-trackers, please see [@MacInnes299925]

# Acknowledgments
This work was supported by Duke University’s Bass
Connections - Brain & Society, and the Big Data to Knowledge Initiative (K01-ES-025442)
awarded to JP. 


# References
