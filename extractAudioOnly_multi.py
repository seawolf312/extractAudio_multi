from __future__ import division
import sys, glob, fnmatch
import os, re, json, argparse
import shutil, random
from multiprocessing import Pool, cpu_count
from subprocess import Popen, PIPE
import speech_recognition as sr
import soundfile as sf
import datetime
import xmltodict

import threading
import time

VID_EXT = ['.avi', '.mov', '.wmv', '.mp4', '.m4v']
NUM_CPU_USE = cpu_count() - 2
OUTPUT_PATH = "./wav_output_multi/"


###############################################################
# This method will delete all previous files and folders and
# create necessary files and folders. It will copy all dataset
# files into a single folder.
#
# start_dir: root folder of all the dataset files
def initialize_env():
    # Remove WAV Output folder 
    if os.path.exists(OUTPUT_PATH):
        shutil.rmtree(OUTPUT_PATH)
    # Create WAV Output folder
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH) 

###############################################################
# This method will convert video file to audio file
#
# vid_name: path name of video you would like to convert.
###############################################################

# Convert video file to audio file
def vidToAudio(vpath):
    vid_name = vpath[vpath.rfind('/')+1:]
    audio_path = OUTPUT_PATH + os.path.splitext(vid_name)[0] + '.wav'
    cmd = ['ffmpeg', '-i', vpath, '-ar', '16000', '-ac', '1', audio_path]
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=False)
    stdoutdata, stderrdata = proc.communicate()
#    print("Audio Path: " + audio_path + "   and vid_name: " + vid_name + "   and vpath: "+ vpath)

    return audio_path


###############################################################
# This method will check if the audio is only background noise
# or chatters without speech.
#
# audioPath: path name of audio you would like test.
###############################################################
def isEmptyAudio(audio_path):
    isEmpty = False
    if not os.path.exists(audio_path):
        print("Audio track was empty:" + audio_path)
        return isEmpty
    sfdata, samplerate = sf.read(audio_path)
    if (sfdata.max() < 0.2) and (abs(sfdata).mean() < 0.02):
        isEmpty = True
        return isEmpty
    cmd = ['ffmpeg', '-i', audio_path, '-acodec', 'mp3', '-ab', '64k', os.path.splitext(audio_path)[0] + '.mp3']
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=False)
    stdoutdata, stderrdata = proc.communicate()
    return isEmpty

def worker(vid):
    apath = vidToAudio(vid)
    print("Path is: " + apath)
    if isEmptyAudio(apath):
        os.remove(vid)

def startTime():
    # Save start time
    s_time = datetime.datetime.now()
    start_time = s_time.strftime("%Y-%m-%d %H:%M%p")

    return s_time


def stopTime(s_time):
    # Save finish time
    f_time = datetime.datetime.now()
    # Calculate process time
    dif_time = f_time - s_time
    extract_time = str( (dif_time.days * 24 * 60) + (dif_time.seconds / 60) )

    print("\nStart Time:   " + s_time.strftime("%Y-%m-%d %H:%M:%S%p"))
    print("Finish Time:  " + f_time.strftime("%Y-%m-%d %H:%M:%S%p"))
    print("Elapsed Time: " + extract_time)


start = startTime()

lock = threading.Lock()

initialize_env()

start_dir = sys.argv[1]
if not os.path.exists(start_dir):
    print('***WARNING*** - {:s} does not exist. Defaulting to {:s}'.format(start_dir,START_DIR))
    start_dir = START_DIR

video = []

for root, dirs, files in os.walk(start_dir):
    for file in files:
        for ext in VID_EXT:
            if file.lower().endswith(ext.lower()):
                video.append(os.path.join(root, file))


threads = []

for i in video:
    while True:
        if threading.activeCount() < NUM_CPU_USE:
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
            break

        elif threading.activeCount() == 0:
            break
        else:
            time.sleep(1)

while True:
#    print(threading.activeCount())
    if threading.activeCount() == 1:
        break
    time.sleep(1)


stopTime(start)
