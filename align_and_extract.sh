#!/bin/bash

taskdir=$1
task=$2
delstopwords=$3
maxbandwidth=$4
delunstressedvowels=$5

dot="$(cd "$(dirname "$0")"; pwd)"
favedir=$dot'/FAVE-extract'

stopwords=$dot'/stopwords.txt'

#get alignments
mkdir -p $taskdir/tmp
if [ $task == 'asr' ] || [ $task == 'boundalign' ] || [ $task == 'txtalign' ] ; then
    $dot'/montreal-forced-aligner/bin/mfa_align' $taskdir $taskdir'/pron.dict' english $taskdir'/aligned' -t . -j 2 -i -s 1
fi

#run FAVE-extract
python $favedir/bin/extractFormants.py \
    --means=$favedir/means.txt \
    --covariances=$favedir/covs.txt \
    --phoneset=$favedir/cmu_phoneset.txt \
    --speaker=$taskdir'/speaker' \
    --removeStopWords=$delstopwords \
    --onlyMeasureStressed=$delunstressedvowels \
    --stopWordsFile=$stopwords \
    --maxBandwidth=$maxbandwidth \
    $taskdir'/audio.wav' $taskdir'/aligned/audio.TextGrid' $taskdir'/aggvowels' &> $taskdir'/fave_errors.log';

#plot
Rscript plot_vowels.r $taskdir'/aggvowels_formants.csv' $taskdir'/fornorm.tsv' $taskdir'/plot.pdf'
