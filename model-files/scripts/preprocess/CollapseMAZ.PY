# Author: Justin Culp
# Date: 8/15/2017
#
# Description: This script takes an input csv containing records for MAZ to be collapsed based on a certain condition (see line 42, 43)
# Requires: Basic python 2.7.x, pandas
#

# Import modules
import os, csv, sys
import pandas as pd

# Variables: Input
inCsv = sys.argv[1] # "maz_data.csv"
print inCsv
cntyCode = int(sys.argv[2]) # 9
print cntyCode

# Variables: Output
outFolder = os.getcwd()

# Variables: Intermediate
aggFile = os.path.join(outFolder, "collapseRows.csv")
nonAggFile = os.path.join(outFolder, "nonCollapseRows.csv")

##------------------------------------------------------------------------------------------------------------
# Processing steps
# Open input file for reading
readFile = open(inCsv, 'r')
header = list(readFile.readline().strip().split(','))
##print header
reader = csv.reader(readFile, delimiter=',')
##next(reader)
# Open file to write non-collapse records
nonCollapseFile = open(nonAggFile, 'wb')
writer_1 = csv.writer(nonCollapseFile, delimiter=',')
writer_1.writerow(header)
# Open file to write collapse records
collapseFile = open(aggFile, 'wb')
writer_2 = csv.writer(collapseFile, delimiter=',')
writer_2.writerow(header)
# MAZ_ORIGINAL > (county_code-1) * 10000 & MAZ_ORIGINAL < (county_code * 10000)
# then the MAZ is in the selected county; if so, dont collapse
for row in reader:
    origMAZ = float(row[2])
##    print origMAZ
    if ((origMAZ> ((cntyCode-1)*100000)) and (origMAZ< (cntyCode*100000))):
        writer_1.writerow(row)
    else:
        writer_2.writerow(row)

# delete reader/writers and close files
del reader
del writer_1
del writer_2
readFile.close()
collapseFile.close()
nonCollapseFile.close()

## ----------------------------------------------------------------------------------------------------------
# Read aggregate file to pandas dataframe
df = pd.read_csv(aggFile, delimiter=',')
data = df.sort_values(by='TAZ', ascending=True)
##print data
header = list(data)
##print header

# define lists of column names based on operation type for filter
keyField = ["TAZ"]
other = ["MAZ", "MAZ_ORIGINAL", "TAZ_ORIGINAL", "mall_flag"]
avgAll = ["hparkcost", "numfreehrs", "dparkcost", "mparkcost"]
commObs = ["ech_dist", "hch_dist", "parkarea"]
nonObs = ["TotInt", "DUDen", "EmpDen", "PopDen", "RetEmpDen", "IntDenBin", "EmpDenBin", "DuDenBin"]
# Fill sumAll list with remaining fields
sumAll = []
for fieldName in header:
    if fieldName not in keyField and fieldName not in other and fieldName not in avgAll and fieldName not in commObs and fieldName not in nonObs:
        sumAll.append(fieldName)

# Create blank dataframe with "other" fields
keys = keyField + other
keyData = data.filter(keys)
##print keyData
keyDf = pd.DataFrame(keyData.groupby('TAZ').apply(lambda x:x.max()))
##print keyDf
# dataframe to sum
keySumAll = keyField + sumAll
sumData = data.filter(keySumAll)
sumDf = pd.DataFrame(sumData.groupby('TAZ')[sumAll].sum())
sumDf['TAZ'] = sumDf.index
##print sumDf
# dataframe to average
keyAvgAll = keyField + avgAll
avgData = data.filter(keyAvgAll)
avgDf = pd.DataFrame(avgData.groupby('TAZ')[avgAll].mean())
avgDf['TAZ'] = avgDf.index
##print avgDf
# datafram to grab most common
keyCommObs = keyField + commObs
comData = data.filter(keyCommObs)
comDf = pd.DataFrame(comData.groupby('TAZ')[commObs].max())
comDf['TAZ'] = comDf.index
##print comDf
# dataframe to return 0
keyNonObs = keyField + nonObs
nonData = data.filter(keyNonObs)
nonDf = pd.DataFrame(nonData.groupby('TAZ')[nonObs].max())
nonDf['TAZ'] = nonDf.index
##print nonDf

##------------------------------------------------------------------------------------------------------------
# Final formatting
collDf = pd.DataFrame(keyDf.merge(sumDf,on='TAZ', how='left').merge(avgDf, on='TAZ', how='left').merge(comDf, on='TAZ', how='left').merge(nonDf, on='TAZ', how='left'))
collDf['MAZ_ORIGINAL'] = ((collDf.TAZ_ORIGINAL/100000).astype(int)*100000 + (collDf.TAZ_ORIGINAL % 100000) +10000)
finalDf = collDf.reindex_axis(data.columns, axis = 1)
# Merge with non collapsed MAZ's
nonCollDf = pd.read_csv(nonAggFile, delimiter=',')
frames = [finalDf, nonCollDf]
outDf = pd.concat(frames)

outDf['MAZ_ORIGINAL'] = outDf.MAZ_ORIGINAL.astype(int)
outDf['TAZ_ORIGINAL'] = outDf.TAZ_ORIGINAL.astype(int)
outDf = outDf.sort_values(by='MAZ_ORIGINAL', ascending=True)

count = 1
for row in outDf.iterrows():
    count+=1
outDf['MAZ'] = (range(1, count, 1))
outDf['TAZ'] = 0
# Zero outfields to leave blank ('nonObs" fields)
for field in nonObs:
    outDf[field] = 0
##print final

# Create new output and delete intermediate files
outDf.to_csv(inCsv, sep=',', index=False)
os.remove(aggFile)
os.remove(nonAggFile)
print "*** Finished ***"




