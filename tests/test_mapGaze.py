import sys
import os
import shutil
from os.path import join

import numpy as np
import cv2

testDataDir = os.path.dirname(os.path.abspath(__file__))

def test_mapGaze():
    # root dir to import mapgaze
    mapGazeDir = os.path.dirname(testDataDir)
    sys.path.insert(0, mapGazeDir)
    import mapGaze

    # inputs for test
    gazeData = join(testDataDir, 'gazeData_world.tsv')
    worldCameraVid = join(testDataDir, 'worldCamera.mp4')
    referenceImage = join(testDataDir, 'referenceImage.jpg')
    outputDir = join(testDataDir, 'test_output')
    nFrames = 5  # only test on small number of frames from testData sample

    # run test data through map gaze
    mapGaze.processRecording(gazeData=gazeData,
                             worldCameraVid=worldCameraVid,
                             referenceImage=referenceImage,
                             outputDir=outputDir,
                             nFrames=nFrames)

def test_outputFiles():
    """ confirm that all of the expected output files get created """

    expectedFiles = ['gazeData_mapped.tsv', 'mapGazeLog.log', 'ref_gaze.m4v', 'ref2world_mapping.m4v', 'referenceImage.jpg', 'world_gaze.m4v']

    for f in expectedFiles:
        assert os.path.exists(join(testDataDir, 'test_output', f))

def test_mappedGaze():
    """ confirm the that output mapped gaze data is what it is supposed to be """
    # expected values
    worldGazeX = np.array([978.816, 979.968, 981.312, 939.264, 877.248, 849.408,
        840.192, 837.312, 835.776, 834.624])
    worldGazeY = np.array([57.132, 57.564, 58.32, 87.696, 119.448, 130.788,
        135.864, 139.536, 140.076, 137.592])
    refGazeX = np.array([1032., 1034., 1033., 977., 893., 857., 842., 838.,
         833., 832.])
    refGazeY = np.array([165., 166., 165., 203., 242., 257., 260., 264., 263., 261.])

    # read in the mapped gaze output file
    outputData = np.genfromtxt(join(testDataDir, 'test_output/gazeData_mapped.tsv'), skip_header=1)

    # confirm worldGaze data matches expectations
    np.testing.assert_equal(outputData[:,3], worldGazeX)
    np.testing.assert_equal(outputData[:,4], worldGazeY)

    # confirm reference gaze data matches expectations
    np.testing.assert_equal(outputData[:,5], refGazeX)
    np.testing.assert_equal(outputData[:,6], refGazeY)

def test_outputVids():
    """ confirm that the output vids are valid vid files with the appropriate dims """
    outputDir = join(testDataDir, 'test_output')

    # check ref_gaze.m4v
    vid = cv2.VideoCapture(join(outputDir, 'ref_gaze.m4v'))
    vidSize = (int(vid.get(cv2.CAP_PROP_FRAME_WIDTH)),
               int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    assert vidSize == (1366, 1478)

    # check ref2world_mapping.m4v
    vid = cv2.VideoCapture(join(outputDir, 'ref2world_mapping.m4v'))
    vidSize = (int(vid.get(cv2.CAP_PROP_FRAME_WIDTH)),
               int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    assert vidSize == (1920, 1080)

    # check world_gaze.m4v
    vid = cv2.VideoCapture(join(outputDir, 'world_gaze.m4v'))
    vidSize = (int(vid.get(cv2.CAP_PROP_FRAME_WIDTH)),
               int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    assert vidSize == (1920, 1080)


def test_removeTestOutput():
    """ remove the output files from the tests """
    #remove the test output dir
    shutil.rmtree(join(testDataDir, 'test_output'))
