#!/bin/bash

taskname=$1
hmm=$2
task=$3

favedir='/home/darla/applications/FAVE/FAVE-extract'
stressdict='cmudict.forhtk.txt'

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
    export PYTHONPATH=/home/darla/applications/Prosodylab-Aligner
    /usr/bin/python3 -m aligner -r $hmm -d $stressdict -a $taskname.wavlab
    echo "aligned"
fi

#merge chunked textgrids (uploadsound, uploadboundtrans)
if [ $task == 'asr' ] || [ $task == 'boundalign' ] || [ $task == 'asredit' ]; then    
    python insert_sil_tg.py $taskname
    mkdir -p $taskname.tg
    chmod g+w $taskname.tg
    cp $taskname.wavlab/*.TextGrid $taskname.tg/
    python merge_grids.py $taskname
fi

if [ $task == 'txtalign' ]; then
    mkdir -p $taskname.mergedtg;
    cp $taskname.wavlab/*.TextGrid $taskname.mergedtg;
fi

zip -j $taskname.alignments.zip $taskname.mergedtg/*.TextGrid

#run FAVE-extract
mkdir -p $taskname.vowels
for filename in $(ls $taskname.mergedtg); do
    filename=${filename%.*};
    python $favedir/bin/extractFormants.py --means=$favedir/means.txt --covariances=$favedir/covs.txt --phoneset=$favedir/cmu_phoneset.txt --speaker=$taskname.speakers/converted_$filename.speaker $taskname.audio/converted_$filename.wav $taskname.mergedtg/$filename.TextGrid $taskname.vowels/$filename &> $taskname.errors;
done

#aggregate all the vowel files together
cat $taskname.vowels/*_formants.csv > $taskname.aggvowels_formants.csv
head -n1 $taskname.aggvowels_formants.csv > $taskname.aggvowels_formants.header
grep -v "name,sex" $taskname.aggvowels_formants.csv > $taskname.aggvowels_formants.body
cat $taskname.aggvowels_formants.header $taskname.aggvowels_formants.body > $taskname.aggvowels_formants.csv
rm $taskname.aggvowels_formants.header $taskname.aggvowels_formants.body

Rscript plot_vowels.r $taskname.aggvowels_formants.csv $taskname.fornorm.tsv $taskname.plot.pdf
