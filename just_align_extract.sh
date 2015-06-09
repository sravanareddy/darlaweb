#!/bin/bash

taskname=$1
hmm=$2

scriptdir='/home/sravana/webpy_sandbox'
favedir='/home/sravana/applications/FAVE/FAVE-extract'

stressdict='/home/sravana/prdicts/cmudict.forhtk.txt'

#get Viterbi phone alignment
for f in $taskname.wavlab/*.lab;
do
  basename=${f##*/}
  basename=${basename%.lab}
  echo $basename
  ln -sf $taskname.audio/converted_$basename.wav $taskname.wavlab/$basename.wav
done

export PYTHONPATH=/home/sravana/applications/Prosodylab-Aligner
/usr/bin/python3 -m aligner -r $hmm -d $stressdict -a $taskname.wavlab &> tmp
pwd >> tmp
echo $hmm >> tmp
echo $stressdict >> tmp
echo $taskname.wavlab >> tmp
echo $USER >> tmp
mkdir -p $taskname.mergedtg
chmod g+w $taskname.mergedtg
cp $taskname.wavlab/*.TextGrid $taskname.mergedtg/

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

Rscript $scriptdir/plot_vowels.r $taskname.aggvowels_formants.csv $taskname.fornorm.tsv $taskname.plot.pdf
