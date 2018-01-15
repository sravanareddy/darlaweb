import sys
import os
from textgrid.textgrid import TextGrid, IntervalTier
from collections import defaultdict

def fliptiers(infile, outfile):
    """flip second and first tiers"""
    tg = TextGrid()
    tg.read(infile)
    phonetier = tg.tiers.pop()
    tg.tiers.insert(0, phonetier)
    tg.write(outfile)

if __name__=='__main__':
    fliptiers(sys.argv[1], sys.argv[2])
