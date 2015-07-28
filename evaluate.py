"""Runs and parses sclite output"""

import os
import subprocess
import shlex

def run_sclite(datadir, taskname):
    basename = os.path.join(datadir, taskname)
    sclite = subprocess.Popen(shlex.split('sclite -r '+basename+'.ref -h '+basename+'.hyp -i rm -o pralign sum'),
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.STDOUT)
    retval = sclite.wait()
    if retval==0:
        retstring = ''
        pra = open(basename+'.hyp.pra').readlines()[10:]
        for line in pra:
            line = line.strip().split()
            if len(line)==0:
                continue
            if line[0] == 'id:':
                retstring+='<span class="note">Utterance ID:</span> '+line[1].strip('()').split('-')[-1]+'<br>'
            if line[0] == 'Scores:':
                c, s, d, i = map(int, line[-4:])
            if line[0] == 'REF:':
                numrefwords = len(line)-1
                retstring+=render_praline(line)
            if line[0] == 'HYP:':
                retstring+=render_praline(line)
                retstring+='<span class="note">WORD ERROR RATE: </span>{0:.2f}% '.format((s+d+i)*100/numrefwords)
                retstring+='({0} correct, {1} substituted, {2} deleted, {3} inserted)<p>'.format(c, s, d, i)

        return retstring
    else:
        return "There was an error comparing your files."

def render_praline(line):
    """Render sclite pralign ref or hyp line in HTML"""
    retstring='<span class="note">'+line[0]+' </span>'
    for word in line[1:]:
        if word.isupper() or word=='***':
            retstring+='<span class="error">'+word+'</span> '
        else:
            retstring+=word+' '
    retstring+='<br>'
    return retstring
