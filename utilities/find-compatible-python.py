# Helper script to reveal requirements for python packages/versions.
# This is uesful because installing Emme python packages brings in:
#  gdal-2.3.3
#  fiona 1.8.5
#  shapely-1.6.4.post1
#  numpy-1.17.0
#  pandas-0.24.2
#  pyproj-1.9.6
# 
# Trying to find packages that are compatible --
# -- looks like geopandas-0.6.3 works; geopandas-0.70 requires pyproj >=2.2.0
# -- looks like scipy-1.7.3 works (requires numpy (<1.23.0,>=1.16.5))
#
# Found geopandsa-0.6.2 on Gohlke's site (https://www.lfd.uci.edu/~gohlke/pythonlibs/)
# and saved to M:\Software\Python\geopandas-0.6.2-py2.py3-none-any.whl
import argparse, requests,sys

PACKAGE_VERSIONS = {
    "geopandas":[
        "0.10.2",
        "0.10.1",
        "0.10.0",
        "0.9.0",
        "0.8.2",
        "0.8.1",
        "0.8.0",
        "0.7.0",
        "0.6.3",
        "0.6.2",
        "0.6.1",
        "0.6.0",
        "0.5.1",
        "0.5.0",
        "0.4.1",
        "0.4.0"
    ],
    "scipy":[
        "1.8.0",
        "1.7.3",
        "1.7.2",
        "1.7.1",
        "1.7.0",
        "1.6.3",
        "1.6.2",
        "1.6.1",
        "1.6.0",
        "1.5.4",
        "1.5.3",
        "1.5.2",
        "1.5.1",
        "1.5.0",
        "1.4.1",
        "1.4.0",
        "1.3.3",
        "1.3.2",
        "1.3.1",
        "1.3.0",
        "1.2.3",
        "1.2.2",
        "1.2.1",
        "1.2.0",
        "1.1.0"]
}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Grabs information about some python package requirements", formatter_class=argparse.RawDescriptionHelpFormatter,)
    parser.add_argument("package", choices=PACKAGE_VERSIONS.keys())
    args = parser.parse_args()

    for version in PACKAGE_VERSIONS[args.package]:
        print("checking {} version {}".format(args.package,version))
        url = "https://pypi.python.org/pypi/{}/{}/json".format(args.package, version)
        r = requests.get(url)
        print("received: {}".format(r.status_code))
        data = r.json()
        if 'info' not in data.keys():
            print("No info for this version")
            continue
        if 'requires_dist' not in data['info'].keys():
            print("No requires_dist in info for this version")
            continue
        requires_dist = r.json()['info']['requires_dist']
        if type(requires_dist) != list:
            print("requires_dist is not a list: {}".format(requires_dist))
            continue
        for req in requires_dist:
            print("  {}".format(req))

    sys.exit()