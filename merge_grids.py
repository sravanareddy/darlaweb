import sys
import os
from textgrid.textgrid import TextGrid, IntervalTier
from collections import defaultdict

def merge_grids(tg1, tg2):
        """merge two TextGrids"""
        tgnew = TextGrid()
        tgnew.minTime = tg1.minTime
        tgnew.maxTime = tg2.maxTime
        merged_phone = IntervalTier('phone')
        merged_word = IntervalTier('word')
        for tier in tg1.tiers:
                if tier.name=='phone':
                        for interval in tier:
                                merged_phone.add(interval.minTime, interval.maxTime, interval.mark)
                elif tier.name=='word':
                        for interval in tier:
                                merged_word.add(interval.minTime, interval.maxTime, interval.mark)
        if tg2.minTime - tg1.maxTime > 0:
            merged_phone.add((tg1.maxTime, tg2.minTime, 'sil'))
            merged_word.add((tg1.maxTime, tg2.minTime, 'sil'))
        for tier in tg2.tiers:
                if tier.name=='phone':
                        for interval in tier:
                                merged_phone.add(interval.minTime+tg1.maxTime,
                                                 interval.maxTime+tg1.maxTime,
                                                 interval.mark)
                elif tier.name=='word':
                        for interval in tier:
                                merged_word.add(interval.minTime+tg1.maxTime,
                                                interval.maxTime+tg1.maxTime,
                                                interval.mark)
        tgnew.append(merged_phone)
        tgnew.append(merged_word)
        return tgnew

if __name__=='__main__':
        taskname = sys.argv[1]
        tgdir = taskname+'.tg'
        merged_tgdir = taskname+'.mergedtg'

        tglist = []
        os.system('mkdir -p '+merged_tgdir)
        os.system('chmod g+w '+merged_tgdir)

        tglist = sorted(filter(lambda x: x.endswith('TextGrid'), os.listdir(tgdir)))  #puts splits in correct order
        tglist = map(TextGrid, tglist)   # load textgrids

        chunks = map(lambda line: map(float, line.split()), open(taskname+'.chunks').readlines())
        # insert sil textgrids to fill holes in chunk list
        for tg, chunk in zip(tglist, chunks):
            tg.minTime = chunk[0]
            tg.maxTime = chunk[1]

        tgnew = reduce(merge_grids, tglist)
        tgnew.write(os.path.join(merged_tgdir, basefile+'.TextGrid'))
