USAGE="""

Creates dummy population (household and persons file) for the purpose of generating accessiblities logsums
from Travel Model 2.0.

See also https://app.asana.com/0/13098083395690/928542858211542/f

For each MAZ, income category (x4) and vehicle category (x3), the script creates a 2-person household,
including 1 full time worker and 1 part time worker.  See below for attributes.

"""

import collections, os
import pandas

# Set the working directory
#USERPROFILE = os.environ["USERPROFILE"]
#os.chdir = os.path.join(USERPROFILE,"Documents","GitHub","populationsim","bay_area")   

# household HHID,TAZ,HINC,hworkers,PERSONS,HHT,VEHICL,hinccat1
# persons   HHID,PERID,AGE,SEX,pemploy,pstudent,ptype 

#
MAZ_DATA_CSV  = "..\landuse\maz_data_withDensity.csv"
OUTPUT_PREFIX = "accessibilities_dummy"


# median of weighted seed_households hh_income_2000; see populationsim\bay_area\households\data\helpful_seed_viewer.twb
#    12878  hh_inc_30
#    35282  hh_inc_30_60
#    61799  hh_inc_60_100
#   122820  hh_inc_100_plus

# https://github.com/BayAreaMetro/modeling-website/wiki/PopSynHousehold
household = collections.OrderedDict([
    ("HHINCADJ",         [ 12878, 35282, 61799, 122820]),                     # Median income within each quartile
    ("NWRKRS_ESR",       [ 2,         2,      2,     2]),                     # Two workers
    ("NP",               [ 2,         2,      2,     2]),                     # Two persons
    ("TYPE",             [ 1,         1,      1,     1]),                     # Housing unit 
    ("HHT",              [ 1,         1,      1,     1]),                     # Family hh married couple
    ("BLD",              [ 2,         2,      2,     2]),                     # Detached SF
    ("transponder",      [ 1,         1,      1,     1]),                     # Transponder
    ("sampleRate",       [ 1.0,     1.0,    1.0,   1.0])                      # Sample rate
])
# hh input synpop file: MAZ,TAZ,HHID,ORIG_TAZ,ORIG_MAZ,MTCCountyID,HHINCADJ,NWRKRS_ESR,VEH,NP,HHT,BLD,TYPE
# hh model output file; hh_id,home_mgra,income,autos,automated_vehicles,transponder,cdap_pattern,jtf_choice,sampleRate

# https://github.com/BayAreaMetro/modeling-website/wiki/PopSynPerson
persons = collections.OrderedDict([
    ("person_num",[   1,   2]), # to be updated
    ("AGEP",      [  36,  37]), # 36,37 years old
    ("SEX",       [   1,   1]), # male :p
    ("SCHL",       [  13,  13]), # bachelor degree
    ("OCCP",      [   2,   3]), # professional, services  
    ("WKHP",      [  40,  30]), # Work hours per week (full, part) 
    ("WKW",       [   1,   5]), # full-time, part-time 
    ("ESR",       [   1,   1]), # Civilian employed, at work
    ("SCHG",      [  -9,  -9]), # Not attending
    ("TYPE",      [   1,   2])
])
# person input synpop file: HHID,PERID,AGEP,SEX,SCHL,OCCP,WKHP,WKW,EMPLOYED (not read by data manager),ESR,SCHG


individualTours = collections.OrderedDict([
    ("person_num",          [ 1,            2]),                            # person number
    ("tour_id",             [ 0,            0]),                            # Tour ID     
    ("tour_category",       ["MANDATORY",   "INDIVIDUAL_NON_MANDATORY"]),   # Category   
    ("tour_purpose",        ["Work",        "Shop"]),                       # purpose     
    ("dest_mgra",           [0,             0]),                            # destination unknown 
    ("start_period",        [0,             0]),                            # start period unknown           
    ("end_period",          [0,             0]),                            # end period unknown 
    ("tour_mode",           [0,             0]),                            # tour mode unknown
    ("tour_distance",       [0,             0]),                            # tour dist unknown
    ("tour_time",           [0,             0]),                            # tour time unknown
    ("atWork_freq",         [0,             0]),                            # no at-work subtours
    ("num_ob_stops",        [0,             0]),                            # no outbound stops
    ("num_ib_stops",        [0,             0]),                            # no inbound stops
    ("out_btap",            [0,             0]),                            # outbound boarding tap unknown
    ("out_atap",            [0,             0]),                            # outbound alighting tap unknown
    ("in_btap",             [0,             0]),                            # inbound boarding tap unknown
    ("in_atap",             [0,             0]),                            # inbound alighting tap unknown
    ("out_set",             [0,             0]),                            # outbound tap set unknown
    ("in_set",              [0,             0]),                            # inbound tap set unknown
    ("sampleRate",          [1.0,         1.0]),                            # sample rate
    ("avAvailable",         [0,             0])                             # no AVs available?        
])
#hh_id,person_id,person_num,person_type,tour_id,tour_category,tour_purpose,orig_mgra,dest_mgra,start_period,end_period,tour_mode,tour_distance,tour_time,atWork_freq,num_ob_stops,num_ib_stops,out_btap,out_atap,in_btap,in_atap,out_set,in_set,sampleRate,avAvailable

def replicate_df_for_variable(hh_df, var_name, var_values):
    """
    Duplicate the given hh_df for the given variable with the given values and return.
    """
    new_var_df = pandas.DataFrame({var_name: var_values})
    new_var_df["join_key"] = 1
    hh_df["join_key"]      = 1

    ret_hh_df = pandas.merge(left=hh_df, right=new_var_df, how="outer").drop(columns=["join_key"])
    return ret_hh_df

if __name__ == '__main__':
    pandas.options.display.width    = 180
    pandas.options.display.max_rows = 100

    maz_data_df = pandas.read_csv(MAZ_DATA_CSV)
    print("Read {} rows of {}".format(len(maz_data_df), MAZ_DATA_CSV))
    
    maz_list = sorted(maz_data_df["MAZ"].tolist())

    #############################################################################################################
    # create the base household df
    #############################################################################################################
    household_df = pandas.DataFrame.from_dict(household)
    household_df = replicate_df_for_variable(household_df, "MAZ", maz_list)
    household_df = replicate_df_for_variable(household_df, "VEH",  [0,1,2])
    household_df = replicate_df_for_variable(household_df, "automated_vehicles",[0,1])
    household_df = household_df[((household_df.automated_vehicles==0) & (household_df.VEH==0))|(household_df.VEH>0)]
    household_df = household_df.sort_values(by=["MAZ","HHINCADJ","VEH","automated_vehicles"])
    household_df = household_df.reset_index(drop=True)
    household_df["HHID"] = household_df.index + 1

     # reorder columns
    household_df = household_df[["HHID","MAZ","HHINCADJ","NWRKRS_ESR","NP","HHT","BLD","TYPE","VEH","automated_vehicles","transponder","sampleRate"]]
  #  maz_data_df["join_key"]  = 1
  #  household_df["join_key"] = 1
    household_df = pandas.merge(left=household_df, right=maz_data_df[["MAZ","TAZ","CountyID"]], on='MAZ', how="outer")

    # print(household_df.head(10))
    household_df = household_df.rename({"CountyID":"MTCCountyID"}, axis="columns")
    outfile = "{}_households.csv".format(OUTPUT_PREFIX)
    household_df.to_csv(outfile, index=False)
    print("Wrote {} lines to {}".format(len(household_df), outfile))
    
    #############################################################################################################
    # create model output household file from input household file dataframe
    #############################################################################################################
    household_model_df = household_df.copy()
    household_model_df = household_model_df.drop(columns=["HHT","BLD","TYPE"])
    household_model_df = household_model_df.rename({"HHID": "hh_id", "MAZ": "home_mgra","HHINCADJ":"income","NP":"size","NWRKRS_ESR":"workers","VEH":"autos"}, axis="columns")
    household_model_df["cdap_pattern"] = "MN0"
    household_model_df["jtf_choice"] = "0"
    outfile = "{}_model_households.csv".format(OUTPUT_PREFIX)
    household_model_df.to_csv(outfile, index=False)
    print("Wrote {} lines to {}".format(len(household_model_df), outfile))
    # hh file: MAZ,TAZ,HHID,ORIG_TAZ,ORIG_MAZ,MTCCountyID,HHINCADJ,NWRKRS_ESR,VEH,NP,HHT,BLD,TYPE
    # output file; hh_id,home_mgra,income,autos,automated_vehicles,transponder,cdap_pattern,jtf_choice,sampleRate
    
    #############################################################################################################
    # create persons by duplicating for households
    #############################################################################################################
    persons_df   = pandas.DataFrame.from_dict(persons)
    persons_df["join_key"]    = 1
    household_df["join_key"] = 1
    persons_df = pandas.merge(left=persons_df, right=household_df[["HHID","HHINCADJ","join_key"]], how="outer").drop(columns=["join_key"])
    persons_df["value_of_time"] = persons_df["HHINCADJ"]/2080 * 0.5
    
    # sort by household ID then person ID
    persons_df = persons_df[["HHID","person_num","AGEP","SEX","SCHL","OCCP","WKHP","WKW","ESR","SCHG","value_of_time","TYPE"]].sort_values(["HHID","person_num"]).reset_index(drop=True)
    persons_df["PERID"] = persons_df.index + 1
     # person input synpop file: HHID,PERID,AGEP,SEX,SCHL,OCCP,WKHP,WKW,EMPLOYED (not read by data manager),ESR,SCHG

    # print(persons_df.head(20))
    outfile = "{}_persons.csv".format(OUTPUT_PREFIX)
    persons_df.to_csv(outfile, index=False)
    print("Wrote {} lines to {}".format(len(persons_df), outfile))
    
    #############################################################################################################
    # create model output person file from input person file dataframe
    #############################################################################################################
    persons_model_df = persons_df.copy()
    persons_model_df = persons_model_df.rename(columns={"HHID":"hh_id","PERID":"person_id","AGEP":"age","SEX":"gender","TYPE":"type"})
    
    # convert gender to text
    genderDict = {1: "m", 2: "f"}
    persons_model_df = persons_model_df.replace({"gender": genderDict})    
    
    # convert person type to text
    typeDict = {1:"Full-time worker",2:"Part-time worker",3:"University student",4:"Non-worker",5:"Retired",6:"Student of driving age",
        7:"Student of non-driving age",8:"Child too young for school"}
    persons_model_df = persons_model_df.replace({"TYPE": typeDict})    

    # set up model choices for person based on person number (0 is FT worker with work activity, 1 is PT worker with non-mandatory activity)
    persons_model_df["activity_pattern"] = "M"
    persons_model_df.loc[persons_model_df.person_num==2, "activity_pattern"] = "N"
    persons_model_df["imf_choice"] = 1
    persons_model_df.loc[persons_model_df.person_num==2, "imf_choice"] = 0
    persons_model_df["inmf_choice"] = 1
    persons_model_df.loc[persons_model_df.person_num==1, "inmf_choice"] = 0
    persons_model_df["fp_choice"] = 2 # pay alternative
    persons_model_df["reimb_pct"] = 0.0
    persons_model_df["sampleRate"] = 1.0
    # print
    outfile = "{}_model_persons.csv".format(OUTPUT_PREFIX)
    persons_model_df.to_csv(outfile, index=False)
    print("Wrote {} lines to {}".format(len(persons_model_df), outfile))

    #############################################################################################################
    # create individual tours
    #############################################################################################################
    individualTours_df = pandas.DataFrame.from_dict(individualTours)

    # duplicate for all persons
    perid_list = sorted(persons_df["PERID"].tolist())
    individualTours_df = replicate_df_for_variable(individualTours_df, "PERID", perid_list)

    # merge person file
    individualTours_df = pandas.merge(left=individualTours_df, right=persons_df, on="PERID", how="outer").drop(columns=["person_num_y"])
    individualTours_df = individualTours_df.rename(columns={"HHID_x":"HHID","person_num_x":"person_num"})
    
    # keep mandatory tours for FT workers and non-mandatory tours for PT workers
    individualTours_df = individualTours_df[((individualTours_df.TYPE==1) & (individualTours_df.tour_category=="MANDATORY"))|
        ((individualTours_df.TYPE==2) & (individualTours_df.tour_category=="INDIVIDUAL_NON_MANDATORY"))]
    
    # merge household file so that we can set origin zone
    individualTours_df = pandas.merge(left=individualTours_df, right=household_df, on="HHID",how="outer")
    
    # drop household and person variable fields
    individualTours_df = individualTours_df.drop(columns=["AGEP","SEX","SCHL","OCCP","WKHP","WKW","ESR","SCHG","value_of_time","HHINCADJ","NWRKRS_ESR","NP","HHT","BLD","TYPE_y","VEH","automated_vehicles","sampleRate_y","MTCCountyID","join_key"])
    individualTours_df = individualTours_df.rename(columns={"HHID":"hh_id","TYPE_x":"person_type","PERID":"person_id","MAZ":"orig_mgra","sampleRate_x":"sampleRate"})
    individualTours_df = individualTours_df.sort_values(by=["person_id"])
  
    # reorder columns
    individualTours_df = individualTours_df[["hh_id","person_id","person_num","person_type","tour_id","tour_category",
        "tour_purpose","orig_mgra","dest_mgra","start_period","end_period","tour_mode","tour_distance","tour_time","atWork_freq","num_ob_stops","num_ib_stops","out_btap","out_atap","in_btap","in_atap","out_set","in_set",     
        "sampleRate","avAvailable"]]

    
    outfile = "{}_indivTours.csv".format(OUTPUT_PREFIX)
    individualTours_df.to_csv(outfile, index=False)
    print("Wrote {} lines to {}".format(len(individualTours_df), outfile))
