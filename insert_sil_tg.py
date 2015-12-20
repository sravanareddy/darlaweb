"""Check whether any TextGrids were not created by aligner, and create ones with sil"""

import sys
import os
from textgrid.textgrid import TextGrid, IntervalTier

if __name__=='__main__':
    taskname = sys.argv[1]
    wvdir = taskname+'.wavlab'
    for filename in os.listdir(wvdir):
        if filename.endswith('lab'):
            basename = filename[:-4]
            if not os.path.exists(os.path.join(wvdir, basename+'.TextGrid')):
                basefile, splitnum = basename.rsplit('.split', 1)
                chunk = open(taskname+'.chunks').readlines()[int(splitnum)-1].split()
                tg = TextGrid()
                tg.minTime = 0
                tg.maxTime = float(chunk[1])-float(chunk[0])
                phone = IntervalTier('phone')
                phone.add(tg.minTime, tg.maxTime, 'sil')
                word = IntervalTier('word')
                word.add(tg.minTime, tg.maxTime, 'sil')
                tg.append(phone)
                tg.append(word)
                tg.write(os.path.join(wvdir, basename+'.TextGrid'))
