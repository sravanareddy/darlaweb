"""Convert Sphinx hyp or txt file to .TextGrid file needed by Montreal Forced Aligner"""

import sys
import os
import json
import string
from textgrid import TextGrid, IntervalTier
from textclean import process_usertext
from utilities import g2p

def asrjob_mfa(taskdir):
    hyps = open(os.path.join(taskdir, 'hyp')).readlines()
    hyps = map(lambda line: line.split()[:-1], hyps)
    hyps.sort(key=lambda line: int(line[-1][len('(split'):]))
    chunks = open(os.path.join(taskdir, 'chunks')).readlines()
    words = set()
    tg = TextGrid()
    tier = IntervalTier('sentence')
    for hypline, chunk in zip(hyps, chunks):
        chunk = map(int, chunk.split())
        text = map(lambda word: word.strip(string.punctuation), hypline[:-1])
        tier.add(chunk[0], chunk[1], ' '.join(text))  #.replace("'", "\\'"))
        words.update(set(text))
    tg.append(tier)
    tg.write(os.path.join(taskdir, 'audio.TextGrid'))
    #make dictionary for OOVs
    g2p(taskdir, words, 'cmudict.stress.txt')


def txtalignjob_mfa(taskdir):
    txtfilecontent = open(os.path.join(taskdir, 'transcript.txt')).read()
    tg = TextGrid()
    tier = IntervalTier('sentence')
    words = map(lambda word: word.strip(string.punctuation),
                    process_usertext(txtfilecontent.lower()).split())
    with open(os.path.join(taskdir, 'alext_args.json')) as f:
        duration = json.load(f)['duration']*60
    tier.add(0, duration, ' '.join(words))
    tg.append(tier)
    tg.write(os.path.join(taskdir, 'audio.TextGrid'))
    #make dictionary for OOVs
    g2p(taskdir, set(words), 'cmudict.stress.txt')

def extract_trans_from_tg(tgfile, outfile):
    """extract transcript from TextGrid"""
    with open(outfile, 'w') as o:
        tg = TextGrid()
        tg.read(tgfile)
        o.write(' '.join(map(lambda interval: interval.mark, tg.tiers[0])))
