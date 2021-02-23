import pandas as pd

# parse transit line file
route_info = {"route_name": [], "long_name": []}
field_lookup = {"LINE NAME": "route_name", "LONGNAME": "long_name"}

with open("transitLines.lin", "r") as f:
    line = f.readline()

    while line:
        if (line.startswith("LINE NAME") | line.startswith(" LONGNAME")):
            # extract field name and corresponding route info
            field = field_lookup[line.split("=")[0].strip()]
            info = line.split("=")[1].strip().replace("\"", "").replace(",", "")

            # append info into route_info dictionary based on the field name
            route_info[field].append(info)

        line = f.readline()


# make sure two lists in the route_info dictionary have same length
assert len(route_info["route_name"]) == len(route_info["long_name"])


# convert to dataframe format
route_df = pd.DataFrame.from_dict(route_info)


# the "route" field will be matched with the route info from the transit assignment result summary
route_df["route"] = "line_" + (route_df.index + 1).astype(str)
print(route_df.shape)
print(route_df.head())


# write result to csv
route_df.to_csv("trn_route_name_lookup.csv", index=False)