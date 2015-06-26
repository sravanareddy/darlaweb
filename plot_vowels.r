args <-commandArgs(TRUE)
csvfile <- args[1]
tsvfile <- args[2]
plotfile <- args[3]
data <- read.csv(csvfile, header=T)

data <- subset(data, data$B1<300 & data$B2<300 & data$stress!=0)

mydata <- c()
mydata$speaker_id <- data$name
mydata$vowel_id <- data$vowel
mydata$context <- data$word
mydata$F1 <- data$F1
mydata$F2 <- data$F2
mydata$F3 <- data$F3
mydata$F1gl <- NA
mydata$F2gl <- NA
mydata$F3gl <- NA
mydata <- data.frame(mydata)

#Write file for user to use with NORM
names <- c("speaker", "vowel", "context", "F1", "F2", "F3", "gl.F1", "gl.F2", "gl.F3")
write.table(mydata, file = tsvfile, quote = FALSE, row.names=FALSE, col.names=names, sep="\t")

# Load Tyler Kendall's Vowels package:
library(vowels)

#Compute means, Lobanov-normalize if there are multiple speakers

numspeakers <- length(unique(mydata$speaker_id))
if(numspeakers > 1) {
  mydata$F1 <- data$F1_lobnorm
  mydata$F2 <- data$F2_lobnorm
  attr(mydata, "norm.method") <- "Lobanov"
  scaled.normed.vowels <- scalevowels(mydata)
  mean.vowels <- compute.means(scaled.normed.vowels, separate=TRUE)
  subt <- "Lobanov-normalized and scaled"
} else {
  mean.vowels <- compute.means(mydata, separate=FALSE)
  subt <- "Unnormalized"
}

pdf(file = paste(plotfile, sep=""));
vowelplot(mean.vowels,
          xlim=c(max(mean.vowels$F2)+20, min(mean.vowels$F2)-20),
          ylim=c(max(mean.vowels$F1)+20, min(mean.vowels$F1)-20),
          speaker=NA,
          leg="speakers",
          color="speakers",
          labels="vowels",
          title="Mean vowel space",
          subtitle=subt,
          size=NA)
dev.off()
