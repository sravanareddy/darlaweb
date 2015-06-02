"""Convert Sphinx hyp file to .lab file needed by ProsodyLab"""

import sys
import os

if __name__=='__main__':
    hyps = open(sys.argv[1]).readlines()
    labdir = sys.argv[2]
    
    for hypline in hyps:
        hypline = hypline.split()
        filename = hypline[-2][1:]  #remove leading (
        o = open(os.path.join(labdir, filename+'.lab'), 'w')
        o.write(' '.join(hypline[:-2]).replace("'", "\\'")+'\n')
        o.close()
