import sys
import os
from textgrid.textgrid import TextGrid, IntervalTier
from collections import defaultdict

def merge_grids(tg1, tg2):
        """merge tg2 into tg1"""
        gap = tg2.minTime - tg1.maxTime
        if gap > 0:  
            tg1.tiers[0].add(tg1.maxTime, tg2.minTime, 'sil')
            tg1.tiers[1].add(tg1.maxTime, tg2.minTime, 'sil')
        for tier in tg2.tiers:
                if tier.name=='phone':
                        for interval in tier:
                                tg1.tiers[0].add(interval.minTime+tg2.minTime,
                                                 interval.maxTime+tg2.minTime,
                                                 interval.mark)
                elif tier.name=='word':
                        for interval in tier:
                                tg1.tiers[1].add(interval.minTime+tg2.minTime,
                                                interval.maxTime+tg2.minTime,
                                                interval.mark)
        tg1.maxTime = tg2.maxTime
        
def tgFromFile(filename):
        tg = TextGrid()
        tg.read(filename)
        return tg

if __name__=='__main__':
        taskname = sys.argv[1]
        tgdir = taskname+'.wavlab'

        tglist = []
        
        tgfilelist = sorted(map(lambda x: os.path.join(tgdir, x),
                            filter(lambda x: x.endswith('TextGrid'), 
                                   os.listdir(tgdir))))  #puts splits in correct order
        
        tglist = map(tgFromFile, tgfilelist)   # load textgrids
        
        chunks = map(lambda line: map(float, line.split()), open(taskname+'.chunks').readlines())
        # insert sil textgrids to fill holes in chunk list
        for tg, tgfile, chunk in zip(tglist, tgfilelist, chunks):
            tg.minTime = chunk[0]
            tg.maxTime = chunk[1]
            
        accum = TextGrid('All', 0, 0)
        accum.append(IntervalTier('phone'))
        accum.append(IntervalTier('word'))
        for tg in tglist:
                merge_grids(accum, tg)
        accum.write(taskname+'.merged.TextGrid')
