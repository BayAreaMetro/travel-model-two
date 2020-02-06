# Author: Joel Freedman
# Date: 9/11/2017
#
# Description: This script takes input network and maz files and writes
# out an MAZ density file for CT-RAMP.
#
# Inputs:
#   hwy\maz_nodes.csv: A file with fields N, X, Y, one record per MAZ. Non-Sequential node numbers.
#   hwy\intersection_nodes.csv: A file with fields X and Y, one record per 3+ leg intersection. 
#   landuse\maz_data.csv: A file with fields MAZ,MAZ_ORIGINAL,emp_total,HH,POP,ACRES,ret_reg,ret_loc.
#
# Outputs:
#   landuse\maz_density.csv: An MAZ file with fields:
#       MAZ             Sequential MAZ 
#       MAZ_ORIGINAL    Non-sequential MAZ
#       TotInt          Total intersections within 1/2 mile of MAZ
#       EmpDen          Employment per acre within 1/2 mile of MAZ
#       RetDen          Retail employment per acre within 1/2 mile of MAZ
#       DUDen           Households per acre within 1/2 mile of MAZ
#       PopDen          Population per acre within 1/2 mile of MAZ
#       intDenBin       Intersection density bin (1 through 3 where 3 is the highest)
#       empDenBin       Employment density bin (1 through 3 where 3 is the highest)
#       duDenBin        Houseold density bin (1 through 3 where 3 is the highest)
#   landuse\maz_data_withDensity.csv: landuse\maz_data.csv joined with landuse\maz_density.csv on MAZ_ORIGINAL
#   
# Requires: Basic python 2.7.x, pandas
#

# Import modules
import os, csv, datetime, sys, math
import pandas as pd, numpy as np
from shutil import copyfile

# Variables: Input
inMazNodes          = "hwy\maz_nodes.csv"
inIntersectionNodes = "hwy\intersection_nodes.csv"
inMazData           = "landuse\maz_data.csv"
outDensityData      = "landuse\maz_density.csv"
outMazData          = "landuse\maz_data_withDensity.csv"
start_time          = datetime.datetime.now()

print inMazNodes
print inIntersectionNodes
print inMazData
print outDensityData

# Open intersection file as pandas table
intersections = pd.read_csv(inIntersectionNodes)
print("Read {} intersections from {}".format(len(intersections), inIntersectionNodes))

# add columns to intersections dataframe
intersections['maz_x'] = 0
intersections['maz_y'] = 0
intersections['distance'] = 0
intersections['count'] = 0

# Open maz node file
readMazNodeFile = open(inMazNodes, 'r')

# Create file reader
reader = csv.DictReader(readMazNodeFile)

# iterate through file and store count of intersections within 1/2 mile of XY coordinates
max_dist_fact = 0.5 # 1/2 mile radius from centroid
max_dist = 5280 * max_dist_fact

max_dist_popempden = 5280 * 5 # 5 miles radius to approximate a zip code (note: avg zip code size in US is 90 sq mi)

int_cnt = []
maz_x = []
maz_y = []
maz_nonseq = []

n = 0
for row in reader:
    maz_n = int(row['MAZ_ORIGINAL'])
    x = float(row['MAZ_X'])
    y = float(row['MAZ_Y'])
    maz_x.append(x)
    maz_y.append(y)
    maz_nonseq.append(maz_n)
    
    intersections['maz_x'] = x
    intersections['maz_y'] = y
    intersections['count'] = 0
    
    intersections['distance'] = intersections.eval("((X-maz_x)**2 + (Y-maz_y)**2)**0.5")    
    int_cnt.append(len(intersections[intersections.distance <= max_dist]))
    if((n % 1000) == 0):
        print "Counting Intersections for MAZ ", maz_n, " : ", int_cnt[n] 
    n = n + 1
     
readMazNodeFile.close()

# read in maz data as pandas dataframe
mazData = pd.read_csv(inMazData)

# create dataset and pandas dataframe of maz xy and intersection count
interDataSet = list(zip(maz_nonseq, maz_x, maz_y, int_cnt))
mazIntersections = pd.DataFrame(data=interDataSet,columns=['MAZ_ORIGINAL', 'MAZ_X','MAZ_Y','INTER_CNT'])

# merge the maz xys with the maz data 
mazData = pd.merge(mazData,mazIntersections,how='inner',on='MAZ_ORIGINAL')
mazData['dest_x'] = 0
mazData['dest_y'] = 0
mazData['distance'] = 0
mazData.sort_values(by='MAZ')

# get the xy columns and node numbers for iterating
maz_x_seq = mazData['MAZ_X'].tolist()
maz_y_seq = mazData['MAZ_Y'].tolist()
maz_seqn = mazData['MAZ'].tolist()
maz_nonseqn = mazData['MAZ_ORIGINAL'].tolist()

# create writer
writeMazDensityFile = open(outDensityData, "wb")
writer = csv.writer(writeMazDensityFile, delimiter=',')
outHeader = ["MAZ_ORIGINAL","TotInt","EmpDen","RetEmpDen","DUDen","PopDen","IntDenBin","EmpDenBin","DuDenBin","PopEmpDenPerMi"]
writer.writerow(outHeader)

# iterate through MAZs and calculate density terms
i = 0
while i < len(maz_seqn):
    origSeqMaz = maz_seqn[i]
    origNonSeqMaz = maz_nonseqn[i]
    interCount = int_cnt[i]
    totEmp=0
    totRet=0
    totHH=0
    totPop=0
    totAcres=0
    empDen=0
    retDen=0
    duDen=0
    popDen=0
    intDenBin = 0
    empDenBin = 0
    duDenBin = 0

    #added for TNC\Taxi wait times
    totPopWaitTime = 0
    totEmpWaitTime = 0
    totAcreWaitTime = 0    
    popEmpWaitTimeDen = 0
    
    mazData['dest_x'] = maz_x_seq[i]
    mazData['dest_y'] = maz_y_seq[i]

    if((i ==0) or (i % 100) == 0):
        print "Calculating Density Variables for MAZ ", origNonSeqMaz
 
     
    #sum the variables for all mazs within the max distance
    mazData['distance'] = mazData.eval("((MAZ_X - dest_x)**2 + (MAZ_Y-dest_y)**2)**0.5")    
    totEmp = mazData.loc[mazData['distance'] < max_dist, 'emp_total'].sum()
    totRet = mazData.loc[mazData['distance'] < max_dist, 'ret_loc'].sum() + mazData.loc[mazData['distance'] < max_dist, 'ret_reg'].sum()
    totHH = mazData.loc[mazData['distance'] < max_dist, 'HH'].sum()
    totPop = mazData.loc[mazData['distance'] < max_dist, 'POP'].sum()
    totAcres = mazData.loc[mazData['distance'] < max_dist, 'ACRES'].sum()
    
    # TNC\Taxi wait time density fields
    totPopWaitTime = mazData.loc[mazData['distance'] < max_dist_popempden, 'POP'].sum()
    totEmpWaitTime = mazData.loc[mazData['distance'] < max_dist_popempden, 'emp_total'].sum()
    totAcreWaitTime = mazData.loc[mazData['distance'] < max_dist_popempden, 'ACRES'].sum()
    
    # calculate density variables
    if(totAcres>0):
        empDen = totEmp/totAcres
        retDen = totRet/totAcres
        duDen = totHH/totAcres
        popDen = totPop/totAcres

    if(totAcreWaitTime>0):
        popEmpWaitTimeDen = (totPopWaitTime + totEmpWaitTime)/(totAcreWaitTime * 0.0015625)
    
    # calculate bins based on sandag bin ranges
    if (interCount < 80):
        intDenBin=1
    elif (interCount < 130):
        intDenBin=2
    else:
        intDenBin=3
		
    if (empDen < 10):
        empDenBin=1
    elif (empDen < 30):
        empDenBin=2
    else:
        empDenBin=3
		
    if (duDen < 5):
        duDenBin=1
    elif (duDen < 10):
        duDenBin=2
    else:
        duDenBin=3
    
    i = i + 1
 
    
    #write out results to csv file
    outList = [origNonSeqMaz,interCount,empDen,retDen,duDen,popDen,intDenBin,empDenBin,duDenBin,popEmpWaitTimeDen]
    writer.writerow(outList)

writeMazDensityFile.close()

# read the data back in as a pandas table
densityData = pd.read_csv(outDensityData)   

# merge with maz data
mazData = pd.merge(mazData,densityData,how='inner',on='MAZ_ORIGINAL')

# drop unnecessary fields
mazData.drop('INTER_CNT', axis=1, inplace=True)
mazData.drop('dest_x', axis=1, inplace=True)
mazData.drop('dest_y', axis=1, inplace=True)
mazData.drop('distance', axis=1, inplace=True)

# write the data back out
mazData.to_csv(outMazData, index=False)

end_time = datetime.datetime.now()
duration = end_time - start_time

print "*** Finished in {} minutes ***".format(duration.total_seconds()/60.0)
