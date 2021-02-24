import pandas as pd


operators = {}

## parse transitSystem.pts
with open("transitSystem.pts", "r") as tsf:
    line = tsf.readline()

    while line:
        if (line.startswith("OPERATOR NUMBER")):
            info = line.replace(" NAME", "").replace("\"", "").split("=")
            operator_num = int(info[1])
            operator_name = info[2].strip()

            operators[operator_num] = operator_name

        line = tsf.readline()

print(operators)

# parse transit line file
route_info = {"route_name": [], "long_name": [], "trn_mode": [], "operator": [], "direction": []}
field_lookup = {"LINE NAME": "route_name", "LONGNAME": "long_name", "USERA2": "trn_mode", "OPERATOR": "operator"}

with open("transitLines.lin", "r") as f:
    line = f.readline()

    while line:
        if (line.startswith("LINE NAME") | line.startswith(" LONGNAME") | line.startswith(" USERA2") | line.startswith(" OPERATOR")):
            # extract field name and corresponding route info
            field = field_lookup[line.split("=")[0].strip()]
            info = line.split("=")[1].strip().replace("\"", "").replace(",", "")

            # if the parsing line is "LINE NAME", also add direction information
            if (field == "route_name"):
                if ("_d0_" in info):
                    route_info["direction"].append(0)
                else:
                    route_info["direction"].append(1)

            if (field == "operator"):
                info = operators[int(info)]

            # append info into route_info dictionary based on the field name
            route_info[field].append(info)

        line = f.readline()


# make sure lists in the route_info dictionary have same length
print(len(route_info["route_name"]))
print(len(route_info["long_name"]))
print(len(route_info["trn_mode"]))
print(len(route_info["operator"]))
print(len(route_info["direction"]))


# convert to dataframe format
route_df = pd.DataFrame.from_dict(route_info)


# the "route" field will be matched with the route info from the transit assignment result summary
route_df["route"] = "line_" + (route_df.index + 1).astype(str)
print(route_df.shape)
print(route_df.head())


# write result to csv
route_df.to_csv("trn_route_name_lookup.csv", index=False)