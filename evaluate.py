from __future__ import division
"""Aligns two files and measures word and phoneme error rate"""

import os
import scipy

class Alignment:
    def __init__(self, phone):
        self.phone = phone #phone-level?
        if self.phone:
            self.consclasses = {'K': ['stop', 'velar', 'unvoiced'],
                            'G': ['stop', 'velar', 'voiced'],
                            'NG': ['nasal', 'velar', 'voiced'],
                            'CH': ['fricative', 'palatal', 'unvoiced'],
                            'JH': ['fricative', 'palatal', 'voiced'],
                            'T': ['stop', 'palatal', 'unvoiced'],
                            'D': ['stop', 'palatal', 'voiced'],
                            'N': ['nasal', 'palatal', 'voiced'],
                            'TH': ['fricative', 'dental', 'unvoiced'],
                            'DH': ['fricative', 'dental', 'voiced'],
                            'S': ['sibilant', 'dental', 'unvoiced'],
                            'SH': ['sibilant', 'palatal', 'unvoiced'],
                            'Z':['sibilant', 'palatal', 'voiced'],
                            'ZH': ['sibilant', 'palatal', 'voiced'],
                            'P': ['stop', 'labial', 'unvoiced'],
                            'B': ['stop', 'labial', 'voiced'],
                            'M': ['nasal', 'labial', 'voiced'],
                            'F': ['fricative', 'labial', 'unvoiced'],
                            'V': ['fricative', 'labial', 'voiced'],
                            'R': ['approx', 'palatal', 'voiced'],
                            'L': ['approx', 'dental', 'voiced'],
                            'W': ['approx', 'labial', 'voiced'],
                            'Y': ['approx', 'palatal', 'unvoiced'],
                            'HH': ['approx', 'velar', 'unvoiced']}
    def is_vowel(self, a):
        if a[0] in 'aeiouAEIOU':
            return True
        return False

    def is_stressed(self, a):
        if a.endswith('1'):
            return True
        return False
    
    def get_phone_subcost(self, a, b):
        if a==b:
            return 0
        if a in self.consclasses and b in self.consclasses:
            return sum(map(lambda i: 1-int(self.consclasses[a][i]==self.consclasses[b][i]), 
                           range(3)))
        if self.is_vowel(a) and self.is_vowel(b):
            return 1
        return 4  #vowel and consonant

    def get_inscost(self):
        return 2

    def get_delcost(self):
        return 2
    
    def get_subcost(self, a, b):
        if a==b:
            return 0
        return 1

    def align(self, ref, hyp):
        reflen = len(ref)
        hyplen = len(hyp)
        dpscore = scipy.zeros((hyplen+1, 
                               reflen+1))
        dppoint = scipy.zeros((hyplen+1,
                               reflen+1))
        for i in range(hyplen):
            dpscore[i+1, 0] = dpscore[i, 0] + self.get_inscost()
            dppoint[i+1, 0] = -1  #code for up
        for i in range(reflen):
            dpscore[0, i+1] = dpscore[0, i] + self.get_delcost()
            dppoint[0, i+1] = 1  #code for left
        for ri, r in enumerate(ref):
            for hi, h in enumerate(hyp):
                up = dpscore[hi, ri+1] + self.get_inscost()
                left = dpscore[hi+1, ri] + self.get_delcost()
                if self.phone:
                    diag = dpscore[hi, ri] + self.get_phone_subcost(r, h)
                else:
                    diag = dpscore[hi, ri] + self.get_subcost(r, h)
                mincost = min(up, left, diag)
                dpscore[hi+1, ri+1] = mincost
                if up==mincost:
                    dppoint[hi+1, ri+1] = -1
                elif left==mincost:
                    dppoint[hi+1, ri+1] = 1
                else:
                    dppoint[hi+1, ri+1] = 0 #code for diagonal
        
        #extract alignment
        self.alref = []
        self.alhyp = []
        rpos = reflen
        hpos = hyplen
        while rpos>0 and hpos>0:
            if dppoint[hpos, rpos] == -1:
                self.alhyp.append(hyp[hpos-1].upper())
                self.alref.append('***')
                hpos -= 1
            elif dppoint[hpos, rpos] == 1:
                self.alref.append(ref[rpos-1].upper())
                self.alhyp.append('***')
                rpos -= 1
            elif dppoint[hpos, rpos] == 0:
                r = ref[rpos-1]
                h = hyp[hpos-1]
                if r!=h:
                    self.alref.append(r.upper())
                    self.alhyp.append(h.upper())
                else:
                    self.alref.append(r)
                    self.alhyp.append(h)
                rpos -= 1
                hpos -= 1
        return self.alref[::-1], self.alhyp[::-1]

    def count_errors(self):
        counts = {}
        counts['cor'] = len(filter(lambda (r, h): r==h, zip(self.alref, self.alhyp)))
        counts['sub']= len(filter(lambda (r, h): r.isupper() and h.isupper(), zip(self.alref, self.alhyp)))
        counts['ins'] = len(filter(lambda (r, h): r=='***' and h.isupper(), zip(self.alref, self.alhyp)))
        counts['del'] = len(filter(lambda (r, h): r.isupper() and h=='***', zip(self.alref, self.alhyp)))
        #also count vowel and stressed vowel if phone-level
        if self.phone:
            vowels = filter(lambda (r, h):
                            self.is_vowel(r) or self.is_vowel(h),
                            zip(self.alref, self.alhyp))
            svowels = filter(lambda (r, h):
                            self.is_stressed(r) or self.is_stressed(h),
                            zip(self.alref, self.alhyp))
            counts['vowrate'] = len(filter(lambda (r, h): (r.isupper() or h.isupper()), vowels))/len(vowels)
            counts['svowrate'] = len(filter(lambda (r, h): (r.isupper() or h.isupper()), svowels))/len(svowels)
        return counts


def run_evaluation(datadir, taskname):
    basename = os.path.join(datadir, taskname)
    cmudict = map(lambda x:x.split(),
                  open('cmudict.forhtk.txt').readlines())
    cmudict = dict(map(lambda x:(x[0].replace("\\'", "'"), x[1:]), cmudict))

    reflines = map(lambda line: line.split(),
                   open(basename+'.ref').readlines())
    hyplines = map(lambda line: line.split(),
                   open(basename+'.hyp').readlines())
    for refwords, hypwords in zip(reflines, hyplines):
        model = Alignment(phone=False)
        alref, alhyp = model.align(refwords, hypwords)
        errors = model.count_errors()

        retstring = '<span class="note">REF:</span> '+render_praline(alref)
        retstring += '<span class="note">HYP:</span> '+render_praline(alhyp)

        numrefwords = len(refwords)
        retstring+='<span class="note">WORD ERROR RATE: </span>{0:.2f}% '.format((errors['sub']+errors['del']+errors['ins'])*100/numrefwords)
        retstring+='({0} correct, {1} substituted, {2} deleted, {3} inserted words)<p>'.format(errors['cor'],
                                                                                         errors['sub'],
                                                                                         errors['del'],
                                                                                         errors['ins'])

        refphones = map(lambda word: cmudict[word], refwords)
        refphones = [phone.lower() for pron in refphones for phone in pron]
        hypphones = map(lambda word: cmudict[word], hypwords)
        hypphones = [phone.lower() for pron in hypphones for phone in pron]
        model = Alignment(phone=True)
        alref, alhyp = model.align(refphones, hypphones)
        errors = model.count_errors()

        retstring += '<span class="note">REF:</span> '+render_praline(alref)
        retstring += '<span class="note">HYP:</span> '+render_praline(alhyp)

        retstring+='<span class="note">VOWEL ERROR RATE: </span>{0:.2f}%<br>'.format(errors['vowrate']*100)
        retstring+='<span class="note">STRESSED VOWEL ERROR RATE: </span>{0:.2f}%<br>'.format(errors['svowrate']*100)

        numrefphones = len(refphones)
        retstring+='<span class="note">PHONEME ERROR RATE: </span>{0:.2f}% '.format((errors['sub']+errors['del']+errors['ins'])*100/numrefwords)
        retstring+='({0} correct, {1} substituted, {2} deleted, {3} inserted phones)<p>'.format(errors['cor'],
                                                                                         errors['sub'],
                                                                                         errors['del'],
                                                                                         errors['ins'])

    return retstring
    
def render_praline(line):
    """Render aligned ref or hyp line in HTML"""
    retstring = ''
    for word in line:
        if word.isupper() or word=='***':
            retstring+='<span class="error">'+word+'</span> '
        else:
            retstring+=word+' '
    retstring+='<br>'
    return retstring

