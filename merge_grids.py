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
        
        tglists = defaultdict(list)
        os.system('mkdir -p '+merged_tgdir)
        os.system('chmod g+w '+merged_tgdir)

        list_of_tgs = sorted(filter(lambda x: x.endswith('TextGrid'), os.listdir(tgdir)))  #puts splits in correct order
        for filename in list_of_tgs:
                if filename.endswith('TextGrid'):
                        tg = TextGrid()
                        tg.read(os.path.join(tgdir, filename))
                        basefile = filename.rsplit('.split', 1)[0]
                        tglists[basefile].append(tg)
                        
        for basefile in tglists:
                chunks = map(lambda line: line.split(), open(taskname+basefile+'.chunks').readlines())
                for i in range(len(tglists[basefile])):
                        tglists[basefile][i].minTime = float(chunks[i][0])
                        tglists[basefile][i].maxTime = float(chunks[i][1])
                tgnew = reduce(lambda x,y:merge_grids(x, y), tglists[basefile])
                tgnew.write(os.path.join(merged_tgdir, basefile+'.TextGrid'))
