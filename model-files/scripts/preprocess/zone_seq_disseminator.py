"""
    zone_seq_disseminator.py base_dir 

    inputs: base_dir - the directory the model is running in (directory with INPUTS, hwy, etc.)

    This script builds all of the CTRAMP files that use zone numbers in them. It is necessary to
    script this because the zone numbers that CTRAMP uses must be sequential and my change with
    any given model run (primarily because TAPs may change). See zone_seq_net_build.job for more
    details about this process and its necessity.
    
    This script first reads in the zone sequence correspondence, and builds mappings from/to the
    (CUBE) network zone numbers to the (CTRAMP) sequential zone numbers. This file is:
   
        mtc_final_netwok_zone_seq.csv
        
    Then this script builds a number of output files, replacing the existing one, only with updated/added
    sequential numbers:
    
        taz_data.csv - the taz data file; the sequential numbers are listed under TAZ, and the original zone
                       numbers under TAZ_ORIGINAL
        maz_data.csv - the maz data file; the sequential numbers are listed under MAZ, and the original zone
                       numbers under MAZ_ORIGINAL
        ParkLocationAlts.csv - park location alternatives; basically a list of mazs built from maz_data.csv
        DestinationChoiceAlternatives - destination choice alternatives; basically a list of mazs and
                                        corresponding tazs built from maz_data.csv
        SoaTazDistAlternatives - taz alternatives; basically a list of tazs
        ParkLocationSampleAlts - park location sample alts; basically a list of mazs
        
    crf 11/2013

"""
import sys,os

base_dir = sys.argv[1]
zone_seq_mapping_file = os.path.join(base_dir,'hwy/mtc_final_network_zone_seq.csv')
taz_data_file = os.path.join(base_dir,'landuse/taz_data.csv') # TAZ,TAZ_ORIGINAL,AVGTTS,DIST,PCTDETOUR,TERMINALTIME
maz_data_file = os.path.join(base_dir,'landuse/maz_data.csv') # MAZ,TAZ,MAZ_ORIGINAL,TAZ_ORIGINAL,HH,POP,emp_self,emp_ag,emp_const_non_bldg_prod,emp_const_non_bldg_office,emp_utilities_prod,emp_utilities_office,emp_const_bldg_prod,emp_const_bldg_office,emp_mfg_prod,emp_mfg_office,emp_whsle_whs,emp_trans,emp_retail,emp_prof_bus_svcs,emp_prof_bus_svcs_bldg_maint,emp_pvt_ed_k12,emp_pvt_ed_post_k12_oth,emp_health,emp_personal_svcs_office,emp_amusement,emp_hotel,emp_restaurant_bar,emp_personal_svcs_retail,emp_religious,emp_pvt_hh,emp_state_local_gov_ent,emp_scrap_other,emp_fed_non_mil,emp_fed_mil,emp_state_local_gov_blue,emp_state_local_gov_white,emp_public_ed,emp_own_occ_dwell_mgmt,emp_fed_gov_accts,emp_st_lcl_gov_accts,emp_cap_accts,emp_total,collegeEnroll,otherCollegeEnroll,AdultSchEnrl,EnrollGradeKto8,EnrollGrade9to12,PrivateEnrollGradeKto8,ech_dist,hch_dist,parkarea,hstallsoth,hstallssam,hparkcost,numfreehrs,dstallsoth,dstallssam,dparkcost,mstallsoth,mstallssam,mparkcost,TotInt,DUDen,EmpDen,PopDen,RetEmpDen,IntDenBin,EmpDenBin,DuDenBin,ACRES,beachAcres,mall_flag
# the following isn't needed because it is dealt with in a different script
#tap_data_file = os.path.join(base_dir,'trn/tap_data.csv') # tap,tap_original,lotid,taz,capacity
model_files_dir = os.path.join(base_dir,'CTRAMP/model')

park_location_alts = os.path.join(model_files_dir,'ParkLocationAlts.csv') # a,mgra,parkarea
dc_alts = os.path.join(model_files_dir,'DestinationChoiceAlternatives.csv')  # a,mgra,dest (a,mgra,taz)
soa_dist_alts = os.path.join(model_files_dir,'SoaTazDistAlternatives.csv')  # a,dest (a,taz)
parking_soa_alts = os.path.join(model_files_dir,'ParkLocationSampleAlts.csv')  # a,mgra

#read zone number correspondence and build mappings
seq_mapping = {}
tazseq_mapping = {}
mazseq_mapping = {}
tapseq_mapping = {}
extseq_mapping = {}
for line in open(zone_seq_mapping_file):
    data = map(int,line.strip().split(','))
    if data[1] > 0:
        seq_mapping[data[0]] = data[1]
        tazseq_mapping[data[1]] = data[0]
    if data[2] > 0:
        seq_mapping[data[0]] = data[2]
        mazseq_mapping[data[2]] = data[0]
    if data[3] > 0:
        seq_mapping[data[0]] = data[3]
        tapseq_mapping[data[3]] = data[0]
    if data[4] > 0:
        seq_mapping[data[0]] = data[4]
        extseq_mapping[data[4]] = data[0]

#this function copies a file in place, but replaces one column based on the sequence lookup value 
# forig is the file
# source is a dictionary of [original_zone_column:sequential_zone_column]
# collect_data and collect_data_column are used to collect data
# collect_data is a list of columns to collect data for
# collect_data_column is the key to use for the collected data
# this method returns a dictionary: {collect_data_column:[collected_data]}
def map_data(forig,source,collect_data=[],collect_data_column=None):
    cdata = {}
    ftemp = forig + '.temp'
    f = open(ftemp,'wb')
    first = True
    source_index = {}
    cd_index = {}
    for line in open(forig):
        line = line.strip()
        if len(line) == 0:
            continue
        line = line.split(',')
        if first:
            for s in source:
                source_index[line.index(s)] = line.index(source[s])
            for c in collect_data:
                cd_index[c] = line.index(c)
            if collect_data_column is not None:
                collect_data_column = line.index(collect_data_column)
            first = False
        else:
            for s in source_index:
                line[source_index[s]] = str(seq_mapping[int(line[s])])
            if collect_data_column is not None:
                id = int(line[collect_data_column])
                cd = {}
                for c in cd_index:
                    cd[c] = line[cd_index[c]]
                cdata[id] = cd
        f.write(','.join(line) + os.linesep)
    f.close()
    if os.path.exists(forig):
        os.remove(forig)
    os.rename(ftemp,forig)
    return cdata

#create the taz/maz data files
map_data(taz_data_file,{'TAZ_ORIGINAL' : 'TAZ'})
cdata = map_data(maz_data_file,{'MAZ_ORIGINAL' : 'MAZ','TAZ_ORIGINAL' : 'TAZ'},['TAZ','parkarea'],'MAZ')
#map_data(tap_data_file,{'tap_original' : 'tap'})

#create a sorted list of mazs and tazs
mazs = list(mazseq_mapping.keys())
mazs.sort()
tazs = list(tazseq_mapping.keys())
tazs.sort()

#create parking alternatives file, using park area collected from maz file
f = open(park_location_alts,'wb')
f.write('a,mgra,parkarea' + os.linesep)
counter = 1
for maz in mazs:
    f.write(','.join([str(counter),str(maz),cdata[maz]['parkarea']]) + os.linesep)
    counter += 1
f.close()

#create dc alternatives file, using taz collected from maz file
f = open(dc_alts,'wb')
f.write('a,mgra,dest' + os.linesep)
counter = 1
for maz in mazs:
    f.write(','.join([str(counter),str(maz),cdata[maz]['TAZ']]) + os.linesep)
    counter += 1
f.close()

#create soa alternatives file
f = open(soa_dist_alts,'wb')
f.write('a,dest' + os.linesep)
counter = 1
for taz in tazs:
    f.write(','.join([str(counter),str(taz)]) + os.linesep)
    counter += 1
f.close()

#create parking soa alternatives file
f = open(parking_soa_alts,'wb')
f.write('a,mgra' + os.linesep)
counter = 1
for maz in mazs:
    f.write(','.join([str(counter),str(maz)]) + os.linesep)
    counter += 1
f.close()

