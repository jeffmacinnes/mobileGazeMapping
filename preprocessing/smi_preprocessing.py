"""
Format raw SMI data.

Tested with Python 3.6, open CV 3.2

The output directory will contain:
	- worldCamera.mp4: the video from the point-of-view scene camera on the glasses
	- frame_timestamps.tsv: table of timestamps for each frame in the world
	- gazeData_world.tsv: gaze data, where all gaze coordinates are represented w/r/t the world camera
"""

# python 2/3 compatibility
from __future__ import division
from __future__ import print_function

import sys, os, shutil
import argparse
from datetime import datetime
from os.path import join
import numpy as np
import pandas as pd
import cv2

OPENCV3 = (cv2.__version__.split('.')[0] == '3')
print("OPENCV version " + cv2.__version__)

def preprocessData(inputDir, sessionNum, output_root):
	"""
	Run all preprocessing steps for SMI data
	"""
	### create output directory
	print('Copying raw data...')
	newDataDir = copySMI_recording(inputDir, sessionNum, output_root)
	print('Input data copied to: {}'.format(newDataDir))

	### Format the gaze data
	print('Prepping the gaze data...')
	gazeWorld_df, frame_timestamps = formatGazeData(newDataDir)
	gazeWorld_df.to_csv(join(newDataDir, 'gazeData_world.tsv'), sep='\t', index=False, float_format='%.3f')

	### convert the frame_timestamps to dataframe
	print('Formatting timestamps...')
	frameNum = np.arange(1, frame_timestamps.shape[0]+1)
	frame_ts_df = pd.DataFrame({'frameNum':frameNum, 'timestamp':frame_timestamps})
	frame_ts_df.to_csv(join(newDataDir, 'frame_timestamps.tsv'), sep='\t', index=False, float_format='%.3f')

	### convert movie from avi to mp4
	print('Converting movie file...')
	convertSMImovie(newDataDir)

	### compress movie
	print('Compressing movie file...')
	cmd_str = ' '.join(['ffmpeg', '-i', join(newDataDir, 'SMI_worldCamera.mp4'), '-pix_fmt', 'yuv420p', join(newDataDir, 'worldCamera.mp4')])
	os.system(cmd_str)

	### clean up
	for f in ['SMI_worldCamera.avi', 'SMI_worldCamera.mp4', 'SMI_raw.txt']:
		try:
			os.remove(join(newDataDir, f))
		except:
			pass


def copySMI_recording(inputDir, sessionNum, output_root):
	"""
	The SMI data is timestamped according to when it was exported, not when it was
	recorded. If you export multiple sessions at once, they have the same timestamp.
	Thus, instead of saving each session with a directory structure like the Tobii and PL data (i.e. data/time), the SMI data will get saved with a structure like
	<num-num>/<sessionNum>, where num-num is the id that gets assigned in the SMI software. This way, subsequent analyses steps can still access these directories as though they followed the same naming conventions as the Tobii and PL glasses
	"""

	date_dir = os.path.split(inputDir)[-1]		# last field of the input dir path
	time_dir = str(sessionNum).zfill(3)			# session number filled to 3 places

	# create the output directory:
	outputDir = join(output_root, date_dir, time_dir)
	if not os.path.isdir(outputDir):
		os.makedirs(outputDir)

	# copy the relevant data to the new directory
	for f in os.listdir(inputDir):
		# movie file
		if ('-' + str(sessionNum) + '-') in f:
			shutil.copy(join(inputDir, f), join(outputDir, 'SMI_worldCamera.avi'))

		# data file
		if ('_' + str(sessionNum).zfill(3) + '_') in f:
			shutil.copy(join(inputDir, f), join(outputDir, 'SMI_raw.txt'))
	return outputDir

def formatGazeData(input_dir):
	"""
	load the raw SMI gaze data.
	Convert timestamps from microseconds, to ms
	normalize gaze coordinates to frame size
	reformat frame column
	set confidence based on event info
	"""

	# open the raw gaze data as dataframe
	raw_df = pd.read_table(join(input_dir, 'SMI_raw.txt'))

	# convert timestamps from microseconds to ms
	ts = raw_df['Time']/1000

	### normalize gaze coords to frame size
	# get vid size
	vid = cv2.VideoCapture(join(input_dir, 'SMI_worldCamera.avi'))
	if OPENCV3:
		vidSize = (int(vid.get(cv2.CAP_PROP_FRAME_WIDTH)), int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT)))
	else:
		vidSize = (int(vid.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)), int(vid.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)))
	vid.release()

	# normalize gaze position
	norm_pos_x = raw_df['B POR X [px]'] / vidSize[0]
	norm_pos_y = raw_df['B POR Y [px]'] / vidSize[1]

	### reformat frame index column
	frameIndices = np.zeros(shape=raw_df.shape[0])

	# starting values
	frameCounter = 0
	prevLabel = raw_df.Frame.iloc[0]

	# loop over all frames
	for i,frame in enumerate(raw_df.Frame):
		# if this frame lable is different than the previous one, update the frame counter
		if frame != prevLabel:
			frameCounter += 1

		# assign the frameCounter value on this frame to the frame_indices array
		frameIndices[i] = frameCounter

		# update the previous frame label var
		prevLabel = frame

	# create a Series object of the frame indices
	frame_idx = pd.Series(frameIndices.astype(int), name='frame_idx')

	### Set confidence based on event labels
	conf = np.zeros(shape=raw_df.shape[0])
	for i,eventLabel in enumerate(raw_df['B Event Info']):
		if eventLabel == 'Blink':
			conf[i] = 0
		else:
			conf[i] = 1

	### build the dataframe
	gaze_df = pd.DataFrame({'timestamp': ts, 'frame_idx':frame_idx,
							'norm_pos_x': norm_pos_x, 'norm_pos_y':norm_pos_y,
							'confidence':conf})
	colOrder = ['timestamp', 'frame_idx', 'confidence', 'norm_pos_x', 'norm_pos_y']

	### Figure out the frame timestamps
	frame_timestamps = getVidFrameTimestamps(join(input_dir, 'SMI_worldCamera.avi'))

	return gaze_df[colOrder], frame_timestamps


def getVidFrameTimestamps(vid_file):
	"""
	Load the supplied video, return an array of frame timestamps
	"""
	vid = cv2.VideoCapture(vid_file)

	# figure out the total number of frames in this video file
	if OPENCV3:
		totalFrames = vid.get(cv2.CAP_PROP_FRAME_COUNT)
	else:
		totalFrames = vid.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)
	frame_ts = np.zeros(int(totalFrames))
	print(totalFrames)

	# loop through all video frames
	frameCounter = 0
	while vid.isOpened():
		# read the next frame
		ret, frame = vid.read()

		# check if its valid:
		if ret == True:
			if OPENCV3:
				thisFrameTS = vid.get(cv2.CAP_PROP_POS_MSEC)
			else:
				thisFrameTS = vid.get(cv2.cv.CV_CAP_PROP_POS_MSEC)

			# write this frame's ts to the array
			frame_ts[frameCounter] = thisFrameTS

			# increment frame counter
			frameCounter += 1
			print(frameCounter, end=',')
		else:
			break
	vid.release()		# close the video

	return frame_ts


def convertSMImovie(input_dir):
	"""
	Convert the move from AVI to mp4
	"""
	vid = cv2.VideoCapture(join(input_dir, 'SMI_worldCamera.avi'))
	if OPENCV3:
		fps = vid.get(cv2.CAP_PROP_FPS)
		vidCodec = cv2.VideoWriter_fourcc(*'mp4v')
		vidSize = (int(vid.get(cv2.CAP_PROP_FRAME_WIDTH)), int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT)))
		totalFrames = vid.get(cv2.CAP_PROP_FRAME_COUNT)
	else:
		fps = vid.get(cv2.cv.CV_CAP_PROP_FPS)
		vidCodec = cv2.cv.CV_FOURCC(*'mp4v')
		vidSize = (int(vid.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)), int(vid.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)))
		totalFrames = vid.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)

	# set up output video
	vidOut_world_fname = join(input_dir, 'SMI_worldCamera.mp4')
	vidOut_world = cv2.VideoWriter()
	vidOut_world.open(vidOut_world_fname, vidCodec, fps, vidSize, True)

	while vid.isOpened():
		# read the next frame of video
		ret, frame = vid.read()
		if ret == True:
			vidOut_world.write(frame)
		else:
			break
	# close videos
	vid.release()
	vidOut_world.release()


if __name__ == '__main__':
	# parse arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('inputDir', help='path to the raw SMI recording dir')
	parser.add_argument('sessionNum', help='session number of SMI data')
	parser.add_argument('outputDir', help='output directory root. Raw data will be written to recording specific dirs within this directory')
	args = parser.parse_args()

	# check if input directory is valid
	if not os.path.isdir(args.inputDir):
		print('Invalid input dir: {}'.format(args.inputDir))
		sys.exit()
	else:

		# run preprocessing on this data
		preprocessData(args.inputDir, args.sessionNum, args.outputDir)
