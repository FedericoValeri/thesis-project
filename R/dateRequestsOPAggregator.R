setwd("C:/Users/fede_/Desktop/Tesi/framework/R")

#Operational profile of Wikipedia
profile.filename <- "wikipedia-profile-de.csv"
project.count.data <- read.csv2(profile.filename)


#scale the load
max.num.users <-300
max.requests <- max(project.count.data$requests)
scale.factor <- max.num.users / max.requests
#print(paste("Maximum is", max.requests, "requests, scale factor is", scale.factor))
scaled.number.of.users <- scale.factor * project.count.data$requests

#set a number of load levels to plot the operational profile
num.load.levels <- 50

options(repr.plot.width=10, repr.plot.height=6)
num.users.hist <- hist(scaled.number.of.users, #single number giving the number of cells for the histogram
                       breaks = num.load.levels, #
                       col = "darkgray", border = "white",
                       xlab = "scaled number of users", main = "histogram of scaled number of users",
                       plot=T)

#accessFrequency viene calcolata sommando tutti gli accessCount e dividendo per ogni valore
num.users.hist$frequency<-num.users.hist$counts / sum(num.users.hist$counts)

#num.users.hist$breaks

frequencies.of.occurrence <-data.frame(
  scaled.number.of.users = num.users.hist$breaks,
  frequency.of.occurrence = c(0,num.users.hist$frequency)
)

aggregatedValuesWikipedia<-frequencies.of.occurrence

myOrderedSplitting <-300
aggregatedValuesWikipedia<-subset(aggregatedValuesWikipedia, aggregatedValuesWikipedia$scaled.number.of.users<=max(myOrderedSplitting))
scaled.number.of.users<-aggregatedValuesWikipedia$scaled.number.of.users
#accessCount<-aggregatedValuesWikipedia$accessCount

accessFrequency <- aggregatedValuesWikipedia$frequency.of.occurrence

colnames(aggregatedValuesWikipedia)<-c("Workload situation (number of users)", "frequency")
#this plots the operational profile as a line curve. Use it in combination of the num.load.levels. Uncomment this to plot the operational profile
#plot(aggregatedValuesWikipedia, type="b", bty="n")

#print(aggregatedValuesWikipedia)



#Create aggregated values (by myOrderedSplitting) of the user frequency from "operationalProfile" 
aggregateValues<-function(myOrderedSplitting, accessFrequency, scaledUsersLoad){
  if(length(myOrderedSplitting)==1){
    n<-myOrderedSplitting
    #this case happens only when a splitting parameter "n" is given. the experiemnts are run independently
    #genero il vettore degli indici dove gli utenti "scaled" sono divisibili per n (in questo caso, gli indici dove gli utenti sono 50,100,150 ecc...)
    byN<-which(scaledUsersLoad %% n == 0)
    #print(byN)
    binProb<-c()
    #costruisco il vettore delle probabilità aggregate dei bin
    for(i in 1:length(byN)){
      if(i==1){
        binProb[i]<-sum(accessFrequency[1:byN[i]])
      }else{
        binProb[i]<-sum(accessFrequency[(byN[i-1]+1): byN[i]], na.rm=TRUE)
      }
    }
    binProbRounded<-round(binProb, digits = 2)
    aggregatedValues<-matrix(c(scaledUsersLoad[byN], binProbRounded), ncol=2,nrow=length(binProbRounded), dimnames=list(c(1:length(binProbRounded)), c("Workload (number of users)", "Probability of occurence")))
    #print(scaledUsersLoad[byN])
  }else{
    #print(myOrderedSplitting)
    binProb<-c()
    
    for(i in 1:length(myOrderedSplitting)){
      if(i==1){
        binProb[i]<-sum(accessFrequency[1: which.min(abs(scaledUsersLoad - myOrderedSplitting[i]))])
      }else{
        binProb[i]<-sum(accessFrequency[(which.min(abs(scaledUsersLoad - myOrderedSplitting[i-1]))+1): which.min(abs(scaledUsersLoad - myOrderedSplitting[i]))])
      }
    }
    aggregatedValues<-matrix(c(myOrderedSplitting, binProb), ncol=2,nrow=length(binProb), dimnames=list(c(1:length(binProb)), c("Workload (number of users)", "Probability of occurence")))
  }
  return(aggregatedValues)
}

aggregatedValuesWikipedia<-aggregateValues(num.load.levels, accessFrequency, scaled.number.of.users)
#print(head(aggregatedValuesWikipedia))


############# SELECT MOST PROBABLE WORKLOADS ############# 

sorted<-sort(aggregatedValuesWikipedia[,2], decreasing = TRUE)
probabiltySumThreshold<-0.5
higherProbs<-c()
finalWorkloads<-c()
for (i in 1:length(sorted)) {
  if (sorted[1] + sorted[2] > probabiltySumThreshold) {
    higherProbs<-c(sorted[1], sorted[2])
  }
  else{
    higherProbs<-c(sorted[1], sorted[2], sorted[3])
  }
}

for (i in 1:length(higherProbs)) {
  # per ogni workload situation
  for (j in 1:length(aggregatedValuesWikipedia[,1])) {
    # se la corrispondente probabilità è uguale alle probabilità più alte
    if (aggregatedValuesWikipedia[,2][j] == higherProbs[i]) {
      finalWorkloads[i]<-aggregatedValuesWikipedia[,1][j]
    }
    
  }
}

print(finalWorkloads)
