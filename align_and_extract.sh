#!/bin/bash

taskname=$1
hmm=$2
task=$3
delstopwords=$4
maxbandwidth=$5
appdir=$6

dot="$(cd "$(dirname "$0")"; pwd)"
favedir=$dot'/FAVE-extract'

stressdict='cmudict.forhtk.txt'
stopwords=$dot'/stopwords.txt'

#convert ASR hypotheses to PL aligner .lab files
if [ $task == 'asr' ]; then
    mkdir -p $taskname.wavlab;
    python hyp2lab.py $taskname.hyp $taskname.wavlab
fi

#prepare Viterbi phone alignment of each chunk with audio (uploadsound and uploadboundtrans)
if [ $task == 'asr' ] || [ $task == 'boundalign' ]; then
  for f in $taskname.wavlab/*.lab;
    do
  basename=${f##*/};
  basename=${basename%.lab};
  ln -sf $taskname.audio/splits/$basename.wav $taskname.wavlab/;
    done
fi

#prepare Viterbi phone alignment of whole file (uploadtxttrans)
if [ $task == 'txtalign' ]; then
    for f in $taskname.wavlab/*.lab;
      do
	basename=${f##*/}
	basename=${basename%.lab}
	ln -sf $taskname.audio/converted_$basename.wav $taskname.wavlab/$basename.wav;
    done
fi

#get alignments (uploadsound, uploadboundtrans, uploadtxttrans, asredit)
if [ $task == 'asr' ] || [ $task == 'boundalign' ] || [ $task == 'txtalign' ] || [ $task == 'asredit' ]; then
    export PYTHONPATH=$appdir/'Prosodylab-Aligner'
    python3 -m aligner -r $hmm -d $stressdict -a $taskname.wavlab &>> aligner.log
    echo
fi

#merge chunked textgrids (uploadsound, uploadboundtrans)
if [ $task == 'asr' ] || [ $task == 'boundalign' ] || [ $task == 'asredit' ]; then
    python insert_sil_tg.py $taskname
    python merge_grids.py $taskname
fi

if [ $task == 'txtalign' ] ; then
    cp $taskname.wavlab/*.TextGrid $taskname.merged.TextGrid;
fi

if [ $task == 'extract' ] ; then
    cp $taskname.mergedtg/*.TextGrid $taskname.merged.TextGrid;
fi

#run FAVE-extract
python $favedir/bin/extractFormants.py \
    --means=$favedir/means.txt \
    --covariances=$favedir/covs.txt \
    --phoneset=$favedir/cmu_phoneset.txt \
    --speaker=$taskname.speaker \
    --removeStopWords=$delstopwords \
    --stopWordsFile=$stopwords \
    --maxBandwidth=$maxbandwidth \
    $taskname.audio/converted_*.wav $taskname.merged.TextGrid $taskname.aggvowels &> $taskname.errors;

#plot
Rscript plot_vowels.r $taskname.aggvowels_formants.csv $taskname.fornorm.tsv $taskname.plot.pdf
