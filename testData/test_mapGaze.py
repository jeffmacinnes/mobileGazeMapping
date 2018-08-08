import sys
import os
import shutil
from os.path import join


def test_mapGaze():
    testDataDir = os.path.dirname(os.path.abspath(__file__))

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
                             nFrames=5)

    # remove the test output dir
    shutil.rmtree(outputDir)
