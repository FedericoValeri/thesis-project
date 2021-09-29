setwd("C:/Users/fede_/Desktop/Tesi/framework/R")

# Operational profile from APM tool here. Streaming video application. Returns AccessCount and scaled.number.of.users
max.num.users <- 300
operationalProfile <- read.csv("OperationalProfileData.csv", header = TRUE, sep = ",")[, 1:2]

usersLoad <- operationalProfile[, 1]
accessCount <- operationalProfile[, 2]

# scale the load
max.requests <- max(usersLoad)
scale.factor <- max.num.users / max.requests
#print(paste("Maximum is", max.requests, "requests, scale factor is", scale.factor))

scaled.number.of.users <- scale.factor * usersLoad
newSet <- data.frame(scaled.number.of.users, accessCount)
newSet <- subset(newSet, newSet$scaled.number.of.users <= max(max.num.users))
scaled.number.of.users <- newSet$scaled.number.of.users
accessCount <- newSet$accessCount
# accessCountFrequency viene calcolata sommando tutti gli accessCount e dividendo per ogni valore
accessCountFrequency <- accessCount / sum(accessCount)
newSet$frequency <- accessCountFrequency
colnames(newSet) <- c("Workload situation (number of users)", "count", "frequency")
#plot(newSet[, c(1, 3)], type = "b", bty = "n")



# Create aggregated values (by myOrderedSplitting) of the user frequency from "operationalProfile"
aggregateValues <- function(myOrderedSplitting, accessCount, scaledUsersLoad) {
  accessFrequency <- accessCount / sum(accessCount)
  if (length(myOrderedSplitting) == 1) {
    n <- myOrderedSplitting
    # this case happens only when a splitting parameter "n" is given. the experiemnts are run independently
    # genero il vettore degli indici dove gli utenti "scaled" sono divisibili per n (in questo caso, gli indici dove gli utenti sono 50,100,150 ecc...)
    byN <- which(scaledUsersLoad %% n == 0)
    #print(byN)
    binProb <- c()
    # costruisco il vettore delle probabilità aggregate degìi bin
    for (i in 1:length(byN)) {
      if (i == 1) {
        binProb[i] <- sum(accessFrequency[1:byN[i]])
      } else {
        binProb[i] <- sum(accessFrequency[(byN[i - 1] + 1):byN[i]])
      }
    }
    aggregatedValues <- matrix(c(scaledUsersLoad[byN], binProb), ncol = 2, nrow = length(binProb), dimnames = list(c(1:length(binProb)), c("Workload (number of users)", "Probability")))
    #print(scaledUsersLoad[byN])
  } else {
    print(myOrderedSplitting)
    binProb <- c()

    for (i in 1:length(myOrderedSplitting)) {
      if (i == 1) {
        binProb[i] <- sum(accessFrequency[1:which.min(abs(scaledUsersLoad - myOrderedSplitting[i]))])
      } else {
        binProb[i] <- sum(accessFrequency[(which.min(abs(scaledUsersLoad - myOrderedSplitting[i - 1])) + 1):which.min(abs(scaledUsersLoad - myOrderedSplitting[i]))])
      }
    }
    aggregatedValues <- matrix(c(myOrderedSplitting, binProb), ncol = 2, nrow = length(binProb), dimnames = list(c(1:length(binProb)), c("Workload (number of users)", "Domain metric per workload")))
  }
  return(aggregatedValues)
}

aggregatedValuesVSA <- aggregateValues(50, accessCount, scaled.number.of.users)
print(head(aggregatedValuesVSA))



# plot(aggregatedValuesVSA, xlim = c(aggregatedValuesVSA[1, 1], aggregatedValuesVSA[nrow(aggregatedValuesVSA), 1]), ylim = c(0, max(aggregatedValuesVSA[, 2]) + 0.05), cex.lab = 1.3)
# polygon(c(min(aggregatedValuesVSA[, 1]), aggregatedValuesVSA[, 1], max(aggregatedValuesVSA[, 1])), c(0, aggregatedValuesVSA[, 2], 0), col = adjustcolor("darkblue", alpha.f = 0.2), lty = 1, lwd = 3, border = "darkblue")
# color <- cm.colors(nrow(unique(usedSettings[, 3:5])))
# color_transparent <- adjustcolor(color, alpha.f = 0.2)
