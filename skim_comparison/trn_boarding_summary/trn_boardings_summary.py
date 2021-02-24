import pandas as pd

# define helper function
def get_period_boarding_info(period: str) -> dict:
    """ Extract boardings by route for the given time period.
    
    Arg:
      period: Time period in string format.
              ("EA", "AM", "MD", "PM", or "EV")

    Returns:
      A pandas data frame with period and boardings by route info
    """ 
    boarding_info = {"route": [], "boardings": []}

    with open(f"TRANSIT_ASSIGN_{period}.prn", "r") as f:
        line = f.readline()

        # skip the file content before "REPORT LINEVOLS  UserClass=Total"
        parsing_status = 0
        while line:
            if (line.startswith("REPORT LINEVOLS  UserClass=Total")):
                parsing_status = 1

            if parsing_status and (line.startswith("line_")):
                line_info = line.split()
                route_name = line_info[0]
                route_boardings = float(line_info[4].replace(",", ""))

                boarding_info["route"].append(route_name)
                boarding_info["boardings"].append(route_boardings)

            line = f.readline()

    # convert boarding_info into dataframe and add time period info
    boarding_info_df = pd.DataFrame.from_dict(boarding_info)
    boarding_info_df["period"] = period
    boarding_info_df = boarding_info_df[["period", "route", "boardings"]] # reorder columns

    return boarding_info_df


# combine boarding info by time period into single dataframe
boarding_info_EA = get_period_boarding_info("EA")
boarding_info_AM = get_period_boarding_info("AM")
boarding_info_MD = get_period_boarding_info("MD")
boarding_info_PM = get_period_boarding_info("PM")
boarding_info_EV = get_period_boarding_info("EV")
all_boarding_info = pd.concat([boarding_info_EA, boarding_info_AM, boarding_info_MD, boarding_info_PM, boarding_info_EV], axis=0)


# add route name info
route_name_lookup = pd.read_csv("trn_route_name_lookup.csv")
all_boarding_info = pd.merge(all_boarding_info, route_name_lookup, how="left", on="route")
all_boarding_info = all_boarding_info[["period", "route_name", "long_name", "trn_mode", "operator", "direction", "boardings"]]
print(all_boarding_info.columns)
print(all_boarding_info.shape)
print(all_boarding_info.head())

# export result to csv
all_boarding_info.to_csv("boarding_by_route_and_period.csv", index=False)