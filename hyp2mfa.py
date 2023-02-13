"""Convert Sphinx hyp or txt file to .TextGrid file needed by Montreal Forced Aligner"""

import sys
import os
import json
import string
from textgrid import TextGrid, IntervalTier
from textclean import process_usertext
from utilities import g2p
from mail import send_unicode_warning_email


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


def azurejob_mfa(taskdir):
    hyps = open(os.path.join(taskdir, 'hyp')).readlines()
    hyps = [line.strip().split() for line in hyps]
    chunks = open(os.path.join(taskdir, 'chunks')).readlines()
    words = set()
    tg = TextGrid()
    tier = IntervalTier('sentence')
    for hypline, chunk in zip(hyps, chunks):
        chunk = map(int, chunk.split())
        text = map(lambda word: word.strip(string.punctuation), hypline)
        tier.add(chunk[0], chunk[1], ' '.join(text))  #.replace("'", "\\'"))
        words.update(set(text))
    tg.append(tier)
    tg.write(os.path.join(taskdir, 'audio.TextGrid'))
    #make dictionary for OOVs
    g2p(taskdir, words, 'cmudict.stress.txt')


def txtjob_mfa(taskdir):
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

def validate_char(char):
    if ord(char) >= 128:
        return False
    # if char == '&':
    #     return False
    return True

def boundjob_mfa(taskdir, clean_text=True):
    alext_args = json.load(open(os.path.join(taskdir, 'alext_args.json')))

    """process text in boundaries file"""
    tg = TextGrid()
    tg.read(os.path.join(taskdir, 'raw.TextGrid'))
    
    tg.tiers[0].name = 'sentence'
    sentences = [tier for tier in reversed(tg.tiers) if tier.name == 'sentence']
    if not sentences:
        tg.tiers[0].name = 'sentence'
        sentences = [tier for tier in tg.tiers if tier.name == 'sentence']

    words = set()
    newtg = TextGrid(tg.name, tg.minTime, tg.maxTime)

    unicode_warning_msg = ''
    for sentence in sentences:
        newtier = IntervalTier(sentence.name, sentence.minTime, sentence.maxTime)
        for segment_interval in sentence:
            if clean_text:
                segment_text = process_usertext(segment_interval.mark.lower())
            else:
                segment_text = segment_interval.mark.lower()
            for char in segment_text:
                if not validate_char(char):
                    unicode_warning_msg += '\n- Between time interval ' + str(float(segment_interval.minTime)) + 's and ' + str(float(segment_interval.maxTime)) + 's, in the following text: "' + ''.join([c if validate_char(c) else 'X' for c in segment_text ]).strip() + '", there is a character with unicode value ' + repr(hex(ord(char))) + ' which will not be processed by DARLA. (Invalid characters are marked with X.)'
            segment_text = ''.join([c if validate_char(c) else '' for c in segment_text ])
            newtier.add(segment_interval.minTime, segment_interval.maxTime, segment_text)
            words.update(set(segment_text.split()))

        newtg.append(newtier)

    if unicode_warning_msg:
        send_unicode_warning_email(alext_args['email'], alext_args['filename'], unicode_warning_msg + '\n')

    newtg.write(os.path.join(taskdir, 'audio.TextGrid'))
    #make dictionary for OOVs
    g2p(taskdir, set(words), 'cmudict.stress.txt')
