import sys
import os
from textgrid.textgrid import TextGrid, IntervalTier
from collections import defaultdict

def merge_grids(tg1, tg2):
        """merge two TextGrids"""
        tgnew = TextGrid()
        tgnew.minTime = tg1.minTime
        tgnew.maxTime = tg1.maxTime+tg2.maxTime+0.01
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
                                merged_phone.add(interval.minTime+tg1.maxTime+0.01,
                                                 interval.maxTime+tg1.maxTime+0.01,
                                                 interval.mark)
                elif tier.name=='word':
                        for interval in tier:
                                merged_word.add(interval.minTime+tg1.maxTime+0.01,
                                                interval.maxTime+tg1.maxTime+0.01,
                                                interval.mark)
        tgnew.append(merged_phone)
        tgnew.append(merged_word)
        return tgnew

if __name__=='__main__':
        tgdir = sys.argv[1]
        merged_tgdir = sys.argv[2]
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
                tgnew = reduce(lambda x,y:merge_grids(x, y), tglists[basefile])
                tgnew.write(os.path.join(merged_tgdir, basefile+'.TextGrid'))
