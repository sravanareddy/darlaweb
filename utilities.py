#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Creates intermediate argument files, does basic audio processing and conversion.
"""

import argparse
import os
import ntpath
import string
import random
import subprocess
import shlex
import re
import sys
import json
from collections import defaultdict
from textgrid.textgrid import TextGrid
from datetime import datetime

from textclean import process_usertext

# ERROR = 0

class CustomException(Exception):
    pass

def read_textupload(data):
    try:
        return data.decode('utf-8-sig')
    except UnicodeDecodeError:
        try:
            return data.decode('utf-16')
        except UnicodeDecodeError:
            try:
                return data.decode('latin-1')
            except:
                pass
    return

def parse_web_params(source):
    post_list = source.split("&")
    parameters = {}
    for form_input in post_list:
        split = form_input.split("=")
        parameters[split[0]] = split[1]
    return parameters

def read_prdict(dictfile):
    spam = map(lambda line: line.split(), open(dictfile).readlines())
    return dict(map(lambda line: (line[0], line[1:]), spam))

def read_filepaths():
    return json.load(open('filepaths.json'))

def g2p(taskdir, transwords, cmudictfile):
    """Predict pronunciations of words not in dictionary and add"""
    cmudict = read_prdict(cmudictfile)
    oov = filter(lambda word: word not in cmudict, set(transwords))
    if len(oov)>0:
        with open(os.path.join(taskdir, 'oov'), 'w') as o:
            o.write('\n'.join(oov)+'\n')
        os.system('g2p/g2p.py --model g2p/model-6 --apply '+os.path.join(taskdir, 'oov') +' > ' + os.path.join(taskdir, 'oovprons'))
        newdict = {}
        for line in open(os.path.join(taskdir, 'oovprons')):
            line = line.split()
            if len(line)<2:
                continue
            newdict[line[0]] = line[1:]
        os.remove(os.path.join(taskdir, 'oov'))
        os.remove(os.path.join(taskdir, 'oovprons'))

        for word in newdict:
            cmudict[word] = newdict[word]

    # write dictionary of words in this transcrip
    with open(os.path.join(taskdir, 'pron.dict'), 'w') as o:
        for word in transwords:
            o.write(word+'  '+' '.join(cmudict[word])+'\n')
    return

def get_basename(filename):
    basename = ntpath.basename(filename.replace('\\','/').replace(' ', '_').replace('(', '').replace(')', '').replace('&', 'and'))
    basename, extension = os.path.splitext(basename)
    return basename, extension.lower()

def randomname(fnamelen):
    timenow = datetime.now()
    fname = '_'.join(map(str, [timenow.year,
                               timenow.month,
                               timenow.day,
                               timenow.hour]))+'_'
    for _ in range(fnamelen):
        fname+=random.choice(string.letters)
    return fname

def store_mturk(datadir):
    taskname = randomname(5)
    loc = os.path.join(datadir, taskname+'.mturk')
    if os.path.exists(loc): #check if taskname exists
        store_mturk(loc) #make a new taskname
    else:
        os.mkdir(loc)
        os.system('chgrp www-data '+loc)
        return taskname, loc

def make_task(datadir):
    try:
        taskname = randomname(5)
        if os.path.exists(taskname): #check if taskname exists
            make_task(datadir) #make a new taskname
        else:
            taskdir = os.path.join(datadir, taskname)
            os.mkdir(taskdir)
            os.system('chgrp www-data '+taskdir)
            return taskname, taskdir, ""
    except OSError:
        error_message = "Could not start a job."
        return None, None, error_message

def write_transcript(datadir, taskname, reffilecontent, hypfilecontent, cmudictfile):
    """Write reference and hypothesis files for evaluation, g2p for OOVs"""
    punct = '!"#$%&\()*+,-./:;<=>?@[\\]^_`{|}~' #same as string.punct but no '
    reffilecontent = filter(lambda c: c not in punct, process_usertext(reffilecontent)).splitlines()
    reffilecontent = filter(lambda line: line!='', reffilecontent)
    hypfilecontent = filter(lambda c: c not in punct, process_usertext(hypfilecontent)).splitlines()
    hypfilecontent = filter(lambda line: line!='', hypfilecontent)
    numreflines = len(reffilecontent)
    numhyplines = len(hypfilecontent)
    allwords = set()   #for g2p
    if numreflines==numhyplines:
        o = open(os.path.join(datadir, taskname+'.ref'), 'w')
        for li, line in enumerate(reffilecontent):
            words = map(lambda word: word.replace("'", "\\'"), line.split())
            o.write(' '.join(words)+'\n')
            allwords.update(words)
        o.close()
        o = open(os.path.join(datadir, taskname+'.hyp'), 'w')
        for li, line in enumerate(hypfilecontent):
            words = map(lambda word: word.replace("'", "\\'"), line.split())
            o.write(' '.join(words)+'\n')
            allwords.update(words)
        o.close()

    g2p(os.path.join(datadir, taskname), allwords, cmudictfile)  #OOVs

    return numreflines, numhyplines


def write_textgrid(datadir, taskname, filename, tgfilecontent):
    #TODO: validate TextGrid
    os.system('mkdir -p '+os.path.join(datadir, taskname+'.mergedtg'))
    o = open(os.path.join(datadir, taskname+'.mergedtg', filename+'.TextGrid'), 'w')
    o.write(tgfilecontent)
    o.close()

def write_chunks(chunks, filepath):
    o = open(filepath, 'w')
    for chunk in chunks:
        o.write('{0} {1}\n'.format(chunk[0], chunk[1]))
    o.close()

def process_audio(taskdir, filename, extension, filecontent, dochunk):

    if filecontent:
        with open(os.path.join(taskdir, filename+extension), 'w') as o:
            o.write(filecontent)

    else:
        return None, None, "The uploaded file is empty. Try again."

    if extension == '.mp3':
        sys.stdout.write('converting mp3 to wav {0}'.format(os.path.join(taskdir, filename+extension)))  #TODO: try and except here
        #os.system("mpg123 "+"-w "+os.path.join(audiodir, filename+'.wav')+' '+os.path.join(audiodir, filename+extension))
        audio = subprocess.Popen(shlex.split("mpg123 "+"-w "+os.path.join(taskdir, filename+'.wav')+' '+os.path.join(taskdir, filename+extension)), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        audio.wait()

        extension = '.wav'

    #split and convert frequency
    filesize, chunks, soxerror = sox_conversion(filename+extension, taskdir, dochunk)
    return filesize, chunks, soxerror

def write_speaker_info(speakerfile, name, sex):
    with open(speakerfile, 'w') as o:
        name = name.strip().replace(',', '')
        if name == '':
            name = 'speakername'  # defaults
        o.write('--name='+name+'\n--sex='+sex+'\n')

def sox_info(filename, audiodir):
    args = "sox --i "+os.path.join(audiodir, filename)
    sox = subprocess.Popen(shlex.split(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return [sox.wait(), sox]

def sox_conversion(filename, taskdir, dochunk=None):
    sample_rate = 0
    file_size = 0.0
    [retval, sox] = sox_info(filename, taskdir)

    if retval != 0:
        error_message = 'Could not process your audio file. Please check that the file is valid and not blank.'
        return file_size, 0, error_message

    for line in sox.stdout.readlines():
        if "File Size" in line:
            line = line.split(':')
            num_bytes = line[1]

        if "Sample Rate" in line:
            line = line.split(':')
            sample_rate = int(line[1].strip())

        if "Duration" in line:
            m = re.search("(=\s)(.*)(\ssamples)", line)
            file_size = float(m.group(2))
            file_size = file_size / sample_rate #gets duration, in seconds of the file.
            file_size /= 60.0 # gets in minutes.l

    #converts wav file to 16000kHz sampling rate
    if sample_rate >= 16000:
        ratecode = '16k'
        sample_rate = 16000

    else:
        error_message = "Sample rate not high enough. Please upload files with minimum 16kHz sample rate."
        # return sample_rate, "sample rate not high enough"
        # raise CustomException("sample rate not high enough")
        return file_size, 0, error_message
        #TODO: actually make it work instead of break. Note: this is also a way to catch non-sound files that have been (maliciously?) uploaded using a .wav extension.

    #convert to 16-bit, signed, little endian as well as downsample
    conv = subprocess.Popen(['sox', os.path.join(taskdir, filename), '-r', ratecode, '-b', '16', '-e', 'signed', '-L', os.path.join(taskdir, 'audio.wav'), 'channels', '1'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    retval = conv.wait()

    if retval != 0:
        error_message = 'Could not downsample file'
        return file_size, 0, error_message

    #split into chunks as specified. TODO: split on silence
    chunks = []
    if dochunk:
        if not os.path.isdir(os.path.join(taskdir, 'splits')):  #need this for multiple files
            os.mkdir(os.path.join(taskdir, 'splits'))

        chunks = map(lambda i: (i, i+dochunk), range(0, int(file_size*60), dochunk))

        conv = subprocess.Popen(['sox', os.path.join(taskdir, 'audio.wav'), os.path.join(taskdir, 'splits', 'split.wav'), 'trim', '0', str(dochunk), ':', 'newfile', ':', 'restart'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        retval = conv.wait()
        if retval != 0:
            error_message = 'Could not split audio file into chunks.'
            return file_size, chunks, error_message
        if file_size*60-chunks[-1][-1]>0:
            convrm = subprocess.Popen(['rm', os.path.join(taskdir, 'splits', 'split{0:03d}.wav'.format(len(chunks)))])
            convrm.wait()

    return file_size, chunks, ""

def gen_argfiles(taskdir, task, filename, duration, email, delstopwords='Y', maxbandwidth='10000000000', delunstressedvowels='Y'):
    acoustic_dir = 'acoustic_dir'
    """create ctl files if applicable"""
    if task=='asr' or task == 'azure':
        filelist = map(lambda x: x[:-4],
                          filter(lambda x: x.endswith('.wav'),
                                 os.listdir(os.path.join(taskdir, 'splits'))))
        numfiles = len(filelist)

        o = open(os.path.join(taskdir, 'ctl'), 'w')
        o.write('\n'.join(filelist))
        o.write('\n')
        o.close()

        """feature extraction"""
        options = {'di': os.path.join(taskdir, 'splits'),
                   'do': os.path.join(taskdir, 'mfc'),
                   'ei': 'wav',
                   'eo': 'mfc',
                   'mswav': 'yes',
                   'raw': 'no',
                   'remove_noise': 'no',  #change?
                   'remove_silence': 'no',
                   'whichchan': '0',
                   'samprate': '16000',
                   'lowerf': '130',    #starting from here, echo the acoustic model
                   'feat': '1s_c_d_dd',
                   'transform': 'dct',
                   'lifter': '22',
                   'agc': 'none',
                   'cmn': 'current',
                   'varnorm': 'no',
                   'cmninit': '40'}
        options.update({'nfilt': '25',
                            'upperf': '6800'})

        o = open(os.path.join(taskdir, 'featurize_args'), 'w')
        options['c'] = os.path.join(taskdir, 'ctl')
        o.write('\n'.join(map(lambda (k, v): '-'+k+' '+v,
                              options.items())))
        o.close()

        os.system('mkdir -p '+os.path.join(taskdir, 'mfc'))
        os.system('chmod g+w '+os.path.join(taskdir, 'mfc'))

        """recognition"""
        options = {}
        hmm = os.path.join(acoustic_dir, 'sphinx-16')
        options.update({'nfilt': '25',
                        'upperf': '6800'})
        options.update({'cepdir': os.path.join(taskdir, 'mfc'),
                        'cepext': '.mfc',
                        'dict': 'cmudict.nostress.txt',
                        'fdict': os.path.join(hmm, 'noisedict'),
                        'hmm': hmm,
                        'lm': 'lm_dir/en-us.lm.dmp',
                        'lw': '7',
                        'samprate': '16000',
                        'bestpath': 'no',
                        'lowerf': '130',    #starting from here, echo the acoustic model
                        'feat': '1s_c_d_dd',
                        'transform': 'dct',
                        'lifter': '22',
                        'agc': 'none',
                        'cmn': 'current',
                        'varnorm': 'no',
                        'cmninit': '40'})

        o = open(os.path.join(taskdir, 'recognize_args'), 'w')
        options.update({'ctl': os.path.join(taskdir, 'ctl'),
                        'hyp': os.path.join(taskdir, 'hyp'),
                        'hypseg': os.path.join(taskdir, 'hypseg')})
        o.write('\n'.join(map(lambda (k, v): '-'+k+' '+v,
                          options.items())))
        o.close()

    """Align and extract"""
    alext_args = {'email': email,
                  'filename': filename,
                  'duration': duration,
                  'tasktype': task,
                  'delstopwords': delstopwords,
                  'maxbandwidth': maxbandwidth,
                  'delunstressedvowels': delunstressedvowels}
    with open(os.path.join(taskdir, 'alext_args.json'), 'w') as o:
        json.dump(alext_args, o)
    return
