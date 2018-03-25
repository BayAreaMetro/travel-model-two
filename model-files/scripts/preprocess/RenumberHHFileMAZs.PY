# Author: Joel Freedman
# Date: 9/8/2017
#
# Description: This script takes an input csv containing household records, and renumbers MAZs outside the 
# selected county according to the taz that the household is in.
# Requires: Basic python 2.7.x, pandas
#

# Import modules
import os, csv, sys
import pandas as pd
from shutil import copyfile

# Variables: Input
inHHs = sys.argv[1] # "households.csv"
inMAZs = sys.argv[2] # "maz_data.csv"

print inHHs
print inMAZs

cntyCode = int(sys.argv[3]) # 9
print cntyCode

# Open MAZ file for reading
readFile = open(inMAZs, 'r')
header = list(readFile.readline().strip().split(','))

# Find columns
seqMazColumn = header.index('MAZ')
seqTazColumn = header.index('TAZ')

# Create file reader
reader = csv.reader(readFile, delimiter=',')

seqTazToMazMap = {} #Note: map will contain junk for TAZs in select county, because these have not been collapsed

for row in reader:
    seqMaz = int(row[seqMazColumn])
    seqTaz = int(row[seqTazColumn])
    seqTazToMazMap[seqTaz] = seqMaz

del reader
readFile.close()

# Variables: Output
outFolder = os.getcwd()

# Variables: Intermediate
outFile = os.path.join(outFolder, "households.temp.csv")

##------------------------------------------------------------------------------------------------------------
# Processing steps

# Read land-use data file, and create mapping between sequential MAZ and sequential TAZ


# Open input file for reading
readFile = open(inHHs, 'r')

# Read header
header = list(readFile.readline().strip().split(','))

# Create file reader
reader = csv.reader(readFile, delimiter=',')

# Open file to write collapse records
collapseFile = open(outFile, 'wb')
writer = csv.writer(collapseFile, delimiter=',')
writer.writerow(header)

# Find columns
mazColumn = header.index('maz')
tazColumn = header.index('taz')

# MAZ_ORIGINAL > (county_code-1) * 10000 & MAZ_ORIGINAL < (county_code * 10000)
# then the MAZ is in the selected county; if so, dont collapse
for row in reader:
    origMAZ = float(row[mazColumn])
    if ((origMAZ> ((cntyCode-1)*100000)) and (origMAZ< (cntyCode*100000))):
        writer.writerow(row)
    else:
		TAZ = float(row[tazColumn])
		newMAZ = seqTazToMazMap[TAZ]
		row[mazColumn] = newMAZ
		writer.writerow(row)

# delete reader/writers and close files
del reader
del writer
readFile.close()
collapseFile.close()

copyfile(outFile, inHHs)
os.remove(outFile)

print "*** Finished ***"




