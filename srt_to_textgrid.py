# -*- coding: utf-8 -*-
"""
@author: Michael

A utility for converting subtitles from .srt format, attainable from
media files such as captioned movies or YouTube videos, to .TextGrid format,
which is natively handled in accoustic analysis programs like Praat, FAVE,
and DARLA.

example command line call:
> python srt_to_textgrid.py example.srt
"""

import sys, re

def time_to_seconds(timestamp):
    '''converts a string denoting time in srt format into a string version
    of a number of seconds'''
    (h, m, s, ms) = tuple(map(float,re.findall(r"[\w']+", timestamp)))
    return "%0.15f" % ((h * 60 + m) * 60 + s + (ms/1000.0))

def clean(text):
    '''Gets rid of double quotes so they don't cause textgrid problems'''
    return(re.sub('"',"'",text))

def convert(srtfile):
    # Read in data from srt file
    f = open(srtfile, 'r')

    # Go through line by line, converting to (start, end, text) tuples.
    transcriptions = []

    srtlines = f.read().splitlines() 

    i = 0

    while i < len(srtlines) - 2:
        # Skip number line
        i+=1
        # Get time information, convert
        timestamps = srtlines[i]    
        start, end = time_to_seconds(timestamps[:12]), time_to_seconds(timestamps[17:])
        i+=1
        # Get transcription
        text = srtlines[i]
        i+=1
        # Get additional lines of transcription if any
        while srtlines[i]:          
            text += ' ' + srtlines[i]
            i+=1
        # Delete all blank lines
        while (i<len(srtlines) and not srtlines[i]):
            i+=1
        # Update transcriptions
        transcriptions.append((start,end,text))

    # Open output TextGrid file
    destination = srtfile[:-4] + ".TextGrid"
    f = open(destination, 'w')
    
    # Write header information to TextGrid file"
    f.write('File type = "ooTextFile"\n')
    f.write('Object class = "TextGrid"\n\n')
    f.write('xmin = 0 \n')
    f.write('xmax = ' + transcriptions[-1][1] + ' \n')    
    f.write('tiers? <exists> \nsize = 1 \nitem []: \n')
    f.write('    item [1]:\n')
    f.write('        class = "IntervalTier" \n')    
    f.write('        name = "sentence" \n') 
    f.write('        xmin = 0 \n') 
    f.write('        xmax = ' + transcriptions[-1][1] + ' \n') 
    f.write('        intervals: size = ' + str(len(transcriptions)) + ' \n')

    # Write content to TextGrid file
    i = 0
    for (start,end,text) in transcriptions:
        i += 1
        f.write('        intervals [' + str(i) + ']:\n')
        f.write('            xmin = ' + start + ' \n')
        f.write('            xmax = ' + end + ' \n')
        f.write('            text = "' + clean(text) + '" \n')

    f.close()

if __name__=='__main__':
    # Examine arguments from command line 
    args = sys.argv
    assert len(args) == 2, "Needs a srt file as an argument."
    convert(args[1])
