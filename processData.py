"""
step 2: processing

This script assumes preprocessing has been done. If you haven't preprocessed the data (according to the manufacturer-specific preprocessing scripts), start there.

Once preprocessing is completed, this script can be used to loop through
every frame of the worldCamera.mp4 video, and try to map the gaze coordinates
from the world coordinate system, to the reference image

Output will contain:
	- world_gaze.mp4:		world video w/ gaze points overlaid
	- ref_gaze.mp4:		video of ref image w/ gaze points overlaid
	- ref2world_mapping.mp4 	video of reference image projected back into world video
	- gazeData_mapped.tsv:	gazeData mapped to both coordinate systems
"""

# python 2/3 compatibility
from __future__ import division
from __future__ import print_function

import os, sys
import shutil
import time
import argparse
import json
import numpy as np
import pandas as pd
from os.path import join
import cv2

OPENCV3 = (cv2.__version__.split('.')[0] == '3')
print("OPENCV version " + cv2.__version__)

def copyPreprocessing(preprocessedDir, condition):
	"""
	copy the data from the preprocessing dir to a new dir based on condition name
	"""
	outputDir = join('../data', condition)

	# create dir
	if not os.path.isdir(outputDir):
		os.makedirs(outputDir)

	# copy files
	for f in ['worldCamera.mp4', 'gazeData_world.tsv', 'frame_timestamps.tsv']:
		src = join(preprocessedDir, f)
		shutil.copy(src, outputDir)


def findMatches(img1_kp, img1_des, img2_kp, img2_des):
	"""
	Find the matches between the descriptors for two images
		Inputs: 	keypoints, descriptors each image
		Output: 	2D coords of quaifying matches on img1, 2D coords of qualifying matches on img2
	"""
	# Match settings
	min_match_count = 50
	min_good_matches = 4
	num_matches = 2
	FLANN_INDEX_KDTREE = 0
	distance_ratio = 0.5				# 0-1; lower values more conservative
	index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
	search_params = dict(checks=10)		# lower = faster, less accurate
	matcher = cv2.FlannBasedMatcher(index_params, search_params)

	# find all matches
	matches = matcher.knnMatch(img1_des, img2_des, k=num_matches)

	# filter out cases where the 2 matches (best guesses) are too close to each other
	goodMatches = []
	for m,n in matches:
		if m.distance < distance_ratio*n.distance:
			goodMatches.append(m)

	if len(goodMatches) > min_good_matches:
		img1_pts = np.float32([img1_kp[i.queryIdx].pt for i in goodMatches])
		img2_pts = np.float32([img2_kp[i.trainIdx].pt for i in goodMatches])

		return img1_pts, img2_pts

	else:
		return None, None


def mapCoords2D(coords, transform2D):
	"""
	Will map the supplied coords to a new coordinate system using the supplied transformation matrix
	"""
	coords = np.array(coords).reshape(-1,1,2)
	mappedCoords = cv2.perspectiveTransform(coords, transform2D)
	mappedCoords = np.round(mappedCoords.ravel())

	return mappedCoords[0], mappedCoords[1]


def projectImage2D(origFrame, transform2D, newImage):
	"""
	Will warp the new Imag according to the supplied transformation matrix and write into the original frame
	"""
	# warp the new image to the video frame
	warpedImage = cv2.warpPerspective(newImage, transform2D, origFrame.T.shape[1:])

	# mask and subtract new image from video frame
	warpedImage_bw = cv2.cvtColor(warpedImage, cv2.COLOR_BGR2GRAY)
	if warpedImage.shape[2] == 4:
		alpha = warpedImage[:,:,3]
		alpha[alpha == 255] = 1 			# create mask of non-transparent pixels
		warpedImage_bw =cv2.multiply(warpedImage_bw, alpha)

	ret, mask = cv2.threshold(warpedImage_bw, 10, 255, cv2.THRESH_BINARY)
	mask_inv = cv2.bitwise_not(mask)
	origFrame_bg = cv2.bitwise_and(origFrame, origFrame, mask=mask_inv)

	# mask the warped new image, and add to the masked background frame
	warpedImage_fg = cv2.bitwise_and(warpedImage[:,:,:3], warpedImage[:,:,:3], mask=mask)
	newFrame = cv2.add(origFrame_bg, warpedImage_fg)

	# return the warped new frame
	return newFrame


def processRecording(preprocessedDir, outputDir, referenceImage_path):
	"""
	Read preprocessed data from preprocessedDir, save all output in outputDir

	On each frame of worldCamera.mp4, look for the matches with the specified
	referenceImage

	If sufficient matches found, map the gaze data from the world camera
	video coordinate system to the reference image coordinate system
	"""

	### SetUp inputs/outputs
	# create dir
	if not os.path.isdir(outputDir):
		os.makedirs(outputDir)

	# copy the reference stim into the output dir
	shutil.copy(referenceImage_path, outputDir)

	# load gaze data
	gazeWorld_df = pd.read_table(join(preprocessedDir, 'gazeData_world.tsv'), sep='\t')

	### Load the reference image
	refImg = cv2.imread(join(outputDir, referenceImage_path.split('/')[-1]))
	refImgColor = refImg.copy()				# store a color copy of the image
	refImg = cv2.cvtColor(refImg, cv2.COLOR_BGR2GRAY)  # convert the original to grayscale

	### Prep the video data #######################################
	# load the video, get parameters
	vid = cv2.VideoCapture(join(preprocessedDir, 'worldCamera.mp4'))
	if OPENCV3:
		totalFrames = vid.get(cv2.CAP_PROP_FRAME_COUNT)
		vidSize = (int(vid.get(cv2.CAP_PROP_FRAME_WIDTH)), int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT)))
		fps = vid.get(cv2.CAP_PROP_FPS)
		vidCodec = cv2.VideoWriter_fourcc(*'mp4v')
		featureDetect = cv2.xfeatures2d.SIFT_create()
	else:
		totalFrames = vid.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)
		vidSize = (int(vid.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)), int(vid.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)))
		fps = vid.get(cv2.cv.CV_CAP_PROP_FPS)
		vidCodec = cv2.cv.CV_FOURCC(*'mp4v')
		featureDetect = cv2.SIFT()

	# world camera output video
	vidOut_world_fname = join(outputDir, 'world_gaze.m4v')
	vidOut_world = cv2.VideoWriter()
	vidOut_world.open(vidOut_world_fname, vidCodec, fps, vidSize, True)

	# reference image output video
	vidOut_ref_fname = join(outputDir, 'ref_gaze.m4v')
	vidOut_ref = cv2.VideoWriter()
	vidOut_ref.open(vidOut_ref_fname, vidCodec, fps, (refImg.shape[1], refImg.shape[0]), True)

	# ref2world mapping output video (useful for debugging)
	vidOut_ref2world_fname = join(outputDir, 'ref2world_mapping.m4v')
	vidOut_ref2world = cv2.VideoWriter()
	vidOut_ref2world.open(vidOut_ref2world_fname, vidCodec, fps, vidSize, True)

	### find keypoints, descriptors for the reference image
	refImg_kp, refImg_des = featureDetect.detectAndCompute(refImg, None)
	print('Reference Image: found {} keypoints'.format(len(refImg_kp)))

	### Loop over video frames #########################################################
	framesToUse = np.arange(0, 10000, 1)
	if totalFrames > framesToUse.max():
		framesToUse = framesToUse[framesToUse <= totalFrames]  	# make sure no attempts on nonexistent frames

	frameProcessing_startTime = time.time()
	frameCounter = 0

	# error debugging
	logFile = open(join(outputDir, 'processing_log.txt'), 'w')

	while vid.isOpened():
		# read the next frame of the video
		ret, frame = vid.read()

		# check if it's a valid frame
		if (ret==True) and (frameCounter in framesToUse):

			# make copy of the reference image (will be used to write a frame to the reference image output videos)
			ref_frame = refImgColor.copy()

			# process this frame
			processedFrame = processFrame(frame, frameCounter, refImg_kp, refImg_des, featureDetect)

			# if good match between reference image and this frame
			if processedFrame['foundGoodMatch']:

				# grab the gaze data (world coords) for this frame
				thisFrame_gazeData_world = gazeWorld_df.loc[gazeWorld_df['frame_idx'] == frameCounter]

				# project the reference image back into the video as a way to check for good mapping
				ref2world_frame = projectImage2D(processedFrame['origFrame'], processedFrame['ref2world'], refImgColor)

				# loop over all gaze data for this frame, translate to different coordinate systems
				for i, gazeRow in thisFrame_gazeData_world.iterrows():
					ts = gazeRow['timestamp']
					frameNum = frameCounter
					conf = gazeRow['confidence']

					# translate normalized gaze data to world pixel coords
					world_gazeX = gazeRow['norm_pos_x'] * processedFrame['frame_gray'].shape[1]
					world_gazeY = gazeRow['norm_pos_y'] * processedFrame['frame_gray'].shape[0]

					# covert from world to reference image pixel coordinates
					ref_gazeX, ref_gazeY = mapCoords2D((world_gazeX, world_gazeY), processedFrame['world2ref'])

					# create dict for this row
					thisRow_df = pd.DataFrame({'gaze_ts': ts, 'worldFrame': frameNum, 'confidence':conf,
							'world_gazeX': world_gazeX, 'world_gazeY': world_gazeY,
							'ref_gazeX': ref_gazeX, 'ref_gazeY': ref_gazeY}, index=[i])

					# append row to gazeMapped_df output
					if 'gazeMapped_df' in locals():
						gazeMapped_df = pd.concat([gazeMapped_df, thisRow_df])
					else:
						gazeMapped_df = thisRow_df

					### Draw gaze circles on frames
					if i == thisFrame_gazeData_world.index.max():
						dotColor = [96, 52, 234]			# pinkish/red
						dotSize = 12
					else:
						dotColor = [168, 231, 86]			# minty green
						dotSize = 8

					# error checking
					if ((int(ref_gazeX) > 800) | (int(ref_gazeX) < 0)):
						logFile.write('ref x exceeds width: {} on frame {} \n'.format(ref_gazeX, frameNum))
					if ((int(ref_gazeY) > 1200) | (int(ref_gazeY) < 0)):
						logFile.write('ref y exceeds height: {} on frame {} \n'.format(ref_gazeY, frameNum))

					cv2.circle(frame, (int(world_gazeX), int(world_gazeY)), dotSize, dotColor, -1)		# world frame
					cv2.circle(ref_frame, (int(ref_gazeX), int(ref_gazeY)),  dotSize, dotColor, -1)		# reference frame

			else:
				# if not a good match, just use the original frame for the ref2world
				ref2world_frame = processedFrame['origFrame']

			# write outputs to video
			vidOut_world.write(frame)
			vidOut_ref.write(ref_frame)
			vidOut_ref2world.write(ref2world_frame)

		# increment frame counter
		frameCounter += 1
		if frameCounter > np.max(framesToUse):
			# release all videos
			vid.release()
			vidOut_world.release()
			vidOut_ref.release()
			vidOut_ref2world.release()

			# write out gaze data
			try:
				colOrder = ['worldFrame', 'gaze_ts', 'confidence',
							'world_gazeX', 'world_gazeY', 'ref_gazeX', 'ref_gazeY']
				gazeMapped_df[colOrder].to_csv(join(outputDir, 'gazeData_mapped.tsv'), sep='\t', index=False, float_format='%.3f')
			except Exception as e:
				print(e)
				print('cound not write gazeData_mapped to csv')
				pass

			# close the logFile
			logFile.close()

	endTime = time.time()
	frameProcessing_time = endTime - frameProcessing_startTime
	print('Total time: %s seconds' % frameProcessing_time)
	print('Avg time/frame: %s seconds' % (frameProcessing_time/framesToUse.shape[0]) )



def processFrame(frame, frameNumber, ref_kp, ref_des, featureDetect):
	"""
	Process a single frame from the world camera
		- try to find match between frame and reference image
		- if success, return the mapping
	"""
	fr = {}		# create dict to store info for this frame

	# create copy of original frame
	origFrame = frame.copy()
	fr['origFrame'] = origFrame 		# store

	# convert to grayscale
	frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	fr['frame_gray'] = frame_gray

	# try to match the frame and the reference image
	try:
		frame_kp, frame_des = featureDetect.detectAndCompute(frame_gray, None)
		print('found {} features on frame {}'.format(len(frame_kp), frameNumber))

		if len(frame_kp) < 2:
			ref_matchPts = None
		else:
			ref_matchPts, frame_matchPts = findMatches(ref_kp, ref_des, frame_kp, frame_des)

		# check if matches were found
		try:
			numMatches = ref_matchPts.shape[0]

			# if sufficient number of matches....
			if numMatches > 10:
				print('found {} matches on frame {}'.format(numMatches, frameNumber))
				sufficientMatches = True
			else:
				print('Insufficient matches ({}} matches) on frame {}'.format(numMatches, frameNumber))
				sufficientMatches = False

		except:
			print ('no matches found on frame {}'.format(frameNumber))
			sufficientMatches = False
			pass

		fr['foundGoodMatch'] = sufficientMatches

		# figure out homographies between coordinate systems
		if sufficientMatches:
			ref2world_transform, mask = cv2.findHomography(ref_matchPts.reshape(-1,1,2), frame_matchPts.reshape(-1,1,2), cv2.RANSAC, 5.0)
			world2ref_transform = cv2.invert(ref2world_transform)

			fr['ref2world'] = ref2world_transform
			fr['world2ref'] = world2ref_transform[1]

	except:
		fr['foundGoodMatch'] = False

	# return the processed frame
	return fr



if __name__ == '__main__':

	# parse arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('preprocessedDir', help='path to preprocessed data dir')
	parser.add_argument('outputDir', help='path to where you want output saved')
	parser.add_argument('referenceImage', help='path to reference image')
	args = parser.parse_args()

	## error checking
	if not os.path.isdir(args.preprocessedDir):
		print('{} is not a valid preprocessed data dir').format(args.preprocessedDir)
	else:
		## process the recording
		print('processing the recording...')
		print('Output saved in: {}').format(args.outputDir)
		processRecording(args.preprocessedDir, args.outputDir, args.referenceImage)
