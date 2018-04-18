import datetime, urllib, json, os, sys, time, traceback

TOLL_FEEDS_URL     = "https://mtlfs.vta.org/mtlfs/mtlfs.json"
OUTPUT_DIR         = "vta_expresslanes_%s" % datetime.date.today().isoformat() # 2002-12-04
TOLL_FEED_FILE     = "vta_toll_feed.txt"

ONGOING_FEEDS      = {
    "toll_status"  :"vta_toll_status.csv",
}
FACILITY_COLUMNS   = {} # for ongoing_feeds

def straight_dump_to_file(name, the_url, the_file):
    """
    Just dumps the url's json to the given file.
    Assumes file is open and doesn't close it.
    """
    the_response = urllib.urlopen(the_url)
    the_data     = json.loads(the_response.read())
    if name: the_file.write(name + "\n")
    the_file.write(the_url)
    the_file.write("\n")
    the_file.write(str(the_data))
    the_file.write("\n\n")
    return the_data

def csv_dump_to_file(name, the_url, the_file):
    """
    Dumps the url's data to the given file in csv format.
    Assumes file is open and doesn't close it.
    The first time through, establishes columns.
    Returns ttl (seconds)
    """
    print "%s csv_dump_to_file %s" % (datetime.datetime.now(), name)
    the_response = urllib.urlopen(the_url)
    the_data     = json.loads(the_response.read())

    for facility_dict in the_data["data"]["facilities"]:
        # establish columns if needed and create header in file
        if name not in FACILITY_COLUMNS.keys():
            FACILITY_COLUMNS[name] = facility_dict.keys()
            print "%s FACILITY_COLUMNS: %s" % (name, str(FACILITY_COLUMNS[name]))
            the_file.write("last_updated,ttl,")
            the_file.write(str(",").join(FACILITY_COLUMNS[name]))
            the_file.write("\n")

        cols = FACILITY_COLUMNS[name]
        the_file.write("%s,%d" % (str(datetime.datetime.fromtimestamp(the_data["last_updated"])), the_data["ttl"]))
        for col in cols:
            the_file.write(",")
            the_file.write(str(facility_dict[col]))
        the_file.write("\n")
    the_file.flush()
    os.fsync(the_file)
    return the_data["ttl"]


if not os.path.exists(OUTPUT_DIR):
    os.mkdir(OUTPUT_DIR)
    print "Created %s" % OUTPUT_DIR

# first, grab a snapshot of everything and just save it
feed_file = open(os.path.join(OUTPUT_DIR, TOLL_FEED_FILE), "w+")
feed_data = straight_dump_to_file(None, TOLL_FEEDS_URL, feed_file)
feed_urls = {} # map name to url
for feed in feed_data["data"]["en"]["feeds"]:
    straight_dump_to_file(feed["name"], feed["url"], feed_file)
    feed_urls[feed["name"]] = feed["url"]

# now just sit and fetch the ones in ONGOING_FEED and write those
out_files = {}

for feed_name,feed_filename in ONGOING_FEEDS.iteritems():
    # open the file
    out_files[feed_name] = open(os.path.join(OUTPUT_DIR, feed_filename), "w+")

# continous loop
try:
    while True:
        ttl = 15*60
        for feed_name,feed_filename in ONGOING_FEEDS.iteritems():
            feed_ttl = csv_dump_to_file(feed_name, feed_urls[feed_name], out_files[feed_name])
            ttl = min(ttl,feed_ttl)
        if ttl == 0: ttl = 15*60
        time.sleep(ttl)

except Exception as ex:
    print "Exception received"
    print traceback.format_exc()
    feed_file.close()
    for feed_name,feed_filename in ONGOING_FEEDS.iteritems():
        out_files[feed_name].close()

