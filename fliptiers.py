import sys
import os
from textgrid.textgrid import TextGrid, IntervalTier
from collections import defaultdict

def fliptiers(infile, outfile):
    """arrange tiers so phone is 0 and word is 1"""
    tg = TextGrid()
    tg.read(infile)
    phonetier = [tier for tier in tg.tiers if 'phone' in tier.name][0]
    wordtier = [tier for tier in tg.tiers if 'word' in tier.name][0]
    tg.tiers = [phonetier, wordtier]
    tg.write(outfile)

if __name__=='__main__':
    fliptiers(sys.argv[1], sys.argv[2])
