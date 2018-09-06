#for instructions on setup (on aws lambda+redshift) please see: 
#https://github.com/BayAreaMetro/Data-And-Visualization-Projects/tree/master/aws-lambda-deployments
import datetime, urllib, json, os, sys, time, traceback, tempfile, pg8000, logging, boto3

from sqlalchemy import create_engine
import pandas as pd

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

def write_feed_to_db(the_url, conn, feed_name):
    """
    Dumps the url's data to the given file in csv format.
    Assumes file is open and doesn't close it.
    The first time through, establishes columns.
    Returns ttl (seconds)
    """
    current_time = datetime.datetime.now()
    the_response = urllib.urlopen(the_url)
    the_data     = json.loads(the_response.read())
    df1 = pd.DataFrame(the_data['data']['facilities'])
    df1['time_checked'] = current_time
    db_tablename = "vta_expresslanes_" + feed_name 
    try:
        df1.to_sql(db_tablename,conn,index=False,if_exists='append')
    except Exception as e:
        logging.warning("db write error at {}".format(current_time))
        logging.warning(e)

def handler():
    #logging.warning('entered the handler')  # will print a message to the console
    OUTPUT_DIR = "vta_expresslanes_%s" % datetime.date.today().isoformat() # 2002-12-04
    OUTPUT_BUCKET      = "vta-express-toll"
    TOLL_FEEDS_URL     = "https://mtlfs.vta.org/mtlfs/mtlfs.json"
    TOLL_FEED_FILE     = "vta_toll_feed.txt"

    ONGOING_FEEDS      = {
        "toll_status"  : "vta_toll_status.csv",
    }
    #connection to redshift
    conn = create_engine("postgresql+pg8000://tbuckley:DataViz@mtc375@data-viz-cluster.cepkffrgvgkl.us-west-2.redshift.amazonaws.com:5439/dev", client_encoding='utf8')

    static_feed_file_s3_name = os.path.join(OUTPUT_DIR, TOLL_FEED_FILE)
    static_feed_tempfile = tempfile.NamedTemporaryFile()

    s3_client = boto3.client('s3')

    with open(static_feed_tempfile.name, 'w+') as f:
        feed_data = straight_dump_to_file(None, TOLL_FEEDS_URL, f)
        feed_urls = {} # map name to url
        for feed in feed_data["data"]["en"]["feeds"]:
            straight_dump_to_file(feed["name"], feed["url"], f)
            feed_urls[feed["name"]] = feed["url"]
    s3_client.upload_file(static_feed_tempfile.name.strip(), OUTPUT_BUCKET, static_feed_file_s3_name)
    #todo:results.append(output_bucket+"/"+flat_file_name)

    for feed_name,feed_filename in ONGOING_FEEDS.iteritems():
        write_feed_to_db(feed_urls[feed_name], conn, feed_name)
