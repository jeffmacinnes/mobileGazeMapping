"""
Format raw Tobii data.

Tested with Python 3.6, open CV 3.2

Since the data originates on a SD card (or temp directory somewhere), a new output directory
will be created for each recording. The output directory will be created within the output root path specified by the user, and named according to [mo-day-yr]/[hr-min-sec] of the original creation time.

The output directory will contain:
	- frame_timestamps.tsv: frame number and corresponding timestamps for each frame in video
	- worldCamera.mp4: the video from the point-of-view scene camera on the glasses
	- gazeData_world.tsv: gaze data, where all gaze coordinates are represented w/r/t the world camera
"""

# python 2/3 compatibility
from __future__ import division
from __future__ import print_function

import sys, os, shutil
import argparse
from datetime import datetime
from os.path import join
import json
import gzip
import cv2
import pandas as pd
import numpy as np


def preprocessData(inputDir, output_root):
	"""
	Run all preprocessing steps on tobii data
	"""
	### copy the raw data to the output directory
	print('Copying raw data...')
	newDataDir = copyTobiiRecording(inputDir, output_root)
	print('Input data copied to: {}'.format(newDataDir))

	#### prep the copied data...
	print('Prepping gaze data...')
	gazeWorld_df, frame_timestamps = formatGazeData(newDataDir)

	# write the gaze data (world camera coords) to a csv file
	gazeWorld_df.to_csv(join(newDataDir, 'gazeData_world.tsv'), sep='\t', index=False)

	### convert the frame_timestamps to dataframe
	frameNum = np.arange(1, frame_timestamps.shape[0]+1)
	frame_ts_df = pd.DataFrame({'frameNum':frameNum, 'timestamp':frame_timestamps})
	frame_ts_df.to_csv(join(newDataDir, 'frame_timestamps.tsv'), sep='\t', index=False)

	### compress movie
	print('Compressing movie file...')
	cmd_str = ' '.join(['ffmpeg', '-r 25', '-i', join(newDataDir, 'fullstream.mp4'), '-pix_fmt', 'yuv420p', join(newDataDir, 'worldCamera.mp4')])
	os.system(cmd_str)

	### cleanup
	for f in ['fullstream.mp4', 'livedata.json']:
		try:
			os.remove(join(newDataDir, f))
		except:
			pass


def copyTobiiRecording(input_dir, output_root):
	"""
	Copy the relevant files from the specified input dir to the specified output dir
	"""

	# read the data and creation time from the segment.json file
	with open(join(input_dir, 'segment.json')) as j:
		segData = json.loads(j.read())
	createDate = segData['seg_created']
	dt = datetime.strptime(createDate, "%Y-%m-%dT%H:%M:%S+0000")

	# create a new output directory based on creation date
	date_dir = dt.strftime('%Y_%m_%d')
	time_dir = dt.strftime('%H-%M-%S')
	if not os.path.isdir(join(output_root, date_dir, time_dir)):
		os.makedirs(join(output_root, date_dir, time_dir))
	outputDir = join(output_root, date_dir, time_dir)

	# Copy relevent files to new directory
	for f in ['livedata.json.gz', 'fullstream.mp4']:
		shutil.copyfile(join(input_dir, f), join(outputDir, f))

	# Unzip the gaze data file
	with gzip.open(join(outputDir, 'livedata.json.gz')) as zipFile:
		with open(join(outputDir, 'livedata.json'), 'wb') as unzippedFile:
			for line in zipFile:

				unzippedFile.write(line)
	os.remove(join(outputDir, 'livedata.json.gz'))

	# return the full path to the output dir
	return outputDir


def formatGazeData(input_dir):
	"""
	load livedata.json, write to csv
	format to get the gaze coordinates w/r/t world camera, and timestamps for every frame of video

	Returns:
		- formatted dataframe with cols for timestamp, frame_idx, and normalized gaze data X & Y
		- np array of frame timestamps
	"""

	# convert the json file to pandas dataframe
	raw_df = json_to_df(join(input_dir, 'livedata.json'))
	raw_df.to_csv(join(input_dir, 'gazeData_raw.tsv'), sep='\t')

	# drop any row that precedes the start of the video timestamps
	raw_df = raw_df[raw_df.vts_time >= raw_df.vts_time.min()]

	data_ts = raw_df.index.values / 1000		# convert data timestamps from microseconds to ms
	confidence = raw_df['confidence'].values
	norm_gazeX = raw_df['gaze_pos_x'].values
	norm_gazeY = raw_df['gaze_pos_y'].values
	vts = raw_df['vts_time'].values / 1000		# convert video timestamps from microseconds to ms

	# read video file, create array of frame timestamps
	frame_timestamps = getVidFrameTimestamps(join(input_dir, 'fullstream.mp4'))

	# use the frame timestamps to assign a frame number to each data point
	frame_idx = np.zeros(data_ts.shape[0])
	for i,thisVTS in enumerate(vts):

		# get the frame_timestamp index of where thisVTS would be inserted
		idx = np.searchsorted(frame_timestamps, thisVTS)
		if idx == 0: idx = 1

		# set the frame number based on this index value
		frame_idx[i] = idx-1

	# build the formatted dataframe
	gaze_df = pd.DataFrame({'timestamp':data_ts, 'confidence':confidence, 'frame_idx': frame_idx, 'norm_pos_x':norm_gazeX, 'norm_pos_y':norm_gazeY})

	# return the gaze data df and frame time stamps array
	colOrder = ['timestamp', 'frame_idx', 'confidence', 'norm_pos_x', 'norm_pos_y']
	return gaze_df[colOrder], frame_timestamps


def getVidFrameTimestamps(vid_file):
	"""
	Load the supplied video, return an array of frame timestamps
	"""
	OPENCV3 = (cv2.__version__.split('.')[0] == '3')		# get opencv version

	vid = cv2.VideoCapture(vid_file)

	# figure out the total number of frames in this video file
	if OPENCV3:
		totalFrames = vid.get(cv2.CAP_PROP_FRAME_COUNT)
	else:
		totalFrames = vid.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)

	frame_ts = np.zeros(int(totalFrames))

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

		else:
			break
	vid.release()		# close the video

	return frame_ts


def json_to_df(json_file):
	"""
	convert the livedata.json file to a pandas dataframe
	"""
	# dicts to store sync points
	vts_sync = {}			# RECORDED video timestamp sync
	df = pd.DataFrame()     # empty dataframe to write data to

	with open(json_file, 'rb') as j:

		# loop over all lines in json file, each line represents unique json object
		for line in j:
			entry = json.loads(line)

			### a number of different dictKeys are possible, respond accordingly
			if 'vts' in entry.keys(): # "vts" key signfies a video timestamp (first frame, first keyframe, and ~1/min afterwards)
				vts_sync[entry['ts']] = entry['vts']
				continue

			# if this json object contains "eye" data (e.g. pupil info)
			if 'eye' in entry.keys():
				which_eye = entry['eye'][:1]
				if 'pc' in entry.keys():
					df.loc[entry['ts'], which_eye + '_pup_cent_x'] = entry['pc'][0]
					df.loc[entry['ts'], which_eye + '_pup_cent_y'] = entry['pc'][1]
					df.loc[entry['ts'], which_eye + '_pup_cent_z'] = entry['pc'][2]
					df.loc[entry['ts'], which_eye + '_pup_cent_val'] = entry['s']
					df.loc[entry['ts'], 'confidence'] = int(entry['s'] == 0)
				elif 'pd' in entry.keys():
					df.loc[entry['ts'], which_eye + '_pup_diam'] = entry['pd']
					df.loc[entry['ts'], which_eye + '_pup_diam_val'] = entry['s']
					df.loc[entry['ts'], 'confidence'] = int(entry['s'] == 0)
				elif 'gd' in entry.keys():
					df.loc[entry['ts'], which_eye + '_gaze_dir_x'] = entry['gd'][0]
					df.loc[entry['ts'], which_eye + '_gaze_dir_y'] = entry['gd'][1]
					df.loc[entry['ts'], which_eye + '_gaze_dir_z'] = entry['gd'][2]
					df.loc[entry['ts'], which_eye + '_gaze_dir_val'] = entry['s']
					df.loc[entry['ts'], 'confidence'] = int(entry['s'] == 0)

			# otherwise it contains gaze position data
			else:
				if 'gp' in entry.keys():
					df.loc[entry['ts'], 'gaze_pos_x'] = entry['gp'][0]
					df.loc[entry['ts'], 'gaze_pos_y'] = entry['gp'][1]
					df.loc[entry['ts'], 'gaze_pos_val'] = entry['s']
					df.loc[entry['ts'], 'confidence'] = int(entry['s'] == 0)
				elif 'gp3' in entry.keys():
					df.loc[entry['ts'], '3d_gaze_pos_x'] = entry['gp3'][0]
					df.loc[entry['ts'], '3d_gaze_pos_y'] = entry['gp3'][1]
					df.loc[entry['ts'], '3d_gaze_pos_z'] = entry['gp3'][2]
					df.loc[entry['ts'], '3d_gaze_pos_val'] = entry['s']
					df.loc[entry['ts'], 'confidence'] = int(entry['s'] == 0)


		# set video timestamps column
		df['vts_time'] = np.array(df.index)	   # df.index is data timstamps
		df.ix[df.index < min(sorted(vts_sync.keys())), 'vts_time'] = np.nan		# set rows that occur before the first frame to nan

		# for each new vts sync package, reindex all of the rows above that timestamp
		for key in sorted(vts_sync.keys()):
			df.ix[df.index >= key, 'vts_time'] = np.array(df.index)[df.index >= key]   # necessary if there are more than 2 keys in the list (prior key changes need to be reset for higher vts syncs)
			df.ix[df.index >= key, 'vts_time'] = df.vts_time - key + vts_sync[key]

		# note: the vts column indicates, in microseconds, where this datapoint would occur in the video timeline
		# these do NOT correspond to the timestamps of when the videoframes were acquired. Need cv2 methods for that.

		# add seconds column
		df = df.reset_index()
		df['seconds'] = (df['index'] - df['index'][0]) / 1000000.0		# convert tobii ts (us) to seconds
		df = df.set_index('index', drop=True)

		# return the dataframe
		return df


if __name__ == '__main__':
	# parse arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('inputDir', help='path to the raw recording dir (e.g. SD card)')
	parser.add_argument('outputRoot', help='path to where output data copied and saved to')
	args = parser.parse_args()

	# Check if input directory is valid
	if not os.path.isdir(args.inputDir):
		print('Invalid input dir: {}'.format(args.inputDir))
		sys.exit()
	else:

		# run preprocessing on this data
		preprocessData(args.inputDir, args.outputRoot)
