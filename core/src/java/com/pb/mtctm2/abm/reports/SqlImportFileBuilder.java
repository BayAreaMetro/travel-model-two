package com.pb.mtctm2.abm.reports;

import java.io.*;
import java.util.LinkedList;
import java.util.List;

/**
 * The {@code SqlImportFileBuilder} ...
 *
 * @author crf
 *         Started 10/18/12 8:43 AM 
 * @revised 5/6/2013 for SERPM (ymm)
 */
public class SqlImportFileBuilder {
    public static final String DATABASE_NAME = "SERPMABM";

    public SqlImportFileBuilder() { }

    public void buildImportFile(String directory, List<String> tables, String outputFileName, String schema, boolean deleteFiles) {
        PrintWriter writer = null;
        try {
            writer = new PrintWriter(new File(directory,outputFileName));
            //build prefix
            writer.println("USE MASTER;");
            writer.println("IF db_id('" + DATABASE_NAME + "') IS NULL");
            writer.println("    CREATE DATABASE " + DATABASE_NAME + ";");
            //writer.println("GO");
            writer.println("ALTER DATABASE " + DATABASE_NAME + " SET RECOVERY SIMPLE;");
            writer.println("USE " + DATABASE_NAME + ";");
            writer.println("IF NOT EXISTS (SELECT schema_name FROM information_schema.schemata");
            writer.println("    WHERE schema_name='" + schema + "')");
            writer.println("        EXEC sp_executesql N'CREATE SCHEMA " + schema + "';");
            //writer.println("GO");


            for (String table : tables) {
                BufferedReader reader = null;
                File sqlFile = new File(directory,table + ".sql");
                File csvFile = new File(directory,table + ".csv");
                if (csvFile.exists() && sqlFile.exists()) {
                    writer.println("IF OBJECT_ID('" + schema + "." + table.toUpperCase() + "','U') IS NOT NULL");
                    writer.println("    DROP TABLE " + schema + "." + table.toUpperCase() + ";");
                    try {
                            reader = new BufferedReader(new FileReader(sqlFile));
                            String line;
                            while ((line = reader.readLine()) != null) {
                                writer.println(addSchemaInformation(line,schema));
                            }
                            writer.println();
                    } catch (IOException e) {
                        throw new RuntimeException(e);
                    } finally {
                        if (reader != null) {
                            try {
                                reader.close();
                              //Check if need to cleanup SQL files after run
                                if(deleteFiles)
                                	sqlFile.delete();
                            } catch (IOException e) {
                                //swallow
                            }
                        }
                    }
                    //writer.println("GO");
                }
            }
            

            //EXPLODE TRIP TABLE INTO ALL POSSIBLE JOINT AND INDIVIDUAL TRIPS AND CORRESPONDING TRAVELER ATTRIBUTES
            //writer.println("CREATE INDEX ind1 ON ofhskims_r2010(i);
            writer.println();
            writer.println();
            writer.println("IF OBJECT_ID('" + schema + ".temp_jointtriptour') IS NOT NULL ");
            writer.println("	DROP TABLE " + schema + ".temp_jointtriptour;");
            writer.println();
            writer.println("SELECT 	JTPs.HH_ID,JTPs.TOUR_ID,JTPs.STOP_ID,JTPs.INBOUND,JTPs.TOUR_PURPOSE,JTPs.ORIG_PURPOSE,JTPs.DEST_PURPOSE,JTPs.ORIG_MGRA,JTPs.DEST_MGRA,JTPs.PARKING_MGRA,JTPs.STOP_PERIOD,JTPs.TRIP_MODE,JTPs.NUM_PARTICIPANTS,JTPs.TRIP_BOARD_TAP,JTPs.TRIP_ALIGHT_TAP,JTPs.TOUR_MODE,JTPs.TRIP_TIME,JTPs.TRIP_DISTANCE,JTPs.TRIP_COST,JTPs.TRIP_PURPOSE_NAME,JTPs.TRIP_MODE_NAME,JTPs.RECID,JTPs.TRIP_BOARD_TAZ, JTPs.TRIP_ALIGHT_TAZ,JTPs.ORIG_TAZ,JTPs.DEST_TAZ,JTRs.TOUR_PARTICIPANTS");
            writer.println("	INTO " + schema + ".temp_jointtriptour");
            writer.println("	FROM " + schema + ".JOINTTRIPS as JTPs INNER JOIN " + schema + ".JOINTTOURS as JTRs ON JTPs.HH_ID = JTRs.HH_ID WHERE JTPs.TOUR_ID = JTRs.TOUR_ID;");
            writer.println("ALTER TABLE " + schema + ".temp_jointtriptour ADD rn INT IDENTITY (1,1);"); 
            writer.println("CREATE INDEX ind2 ON " + schema + ".temp_jointtriptour(HH_ID);");
            writer.println("CREATE INDEX ind3 ON " + schema + ".SYNPERSON(HHID);");
            writer.println("IF OBJECT_ID('" + schema + ".TRIP') IS NOT NULL DROP TABLE " + schema + ".TRIP;");
            writer.println();
            writer.println("CREATE TABLE " + schema + ".TRIP (HH_ID int,TOUR_ID int,STOP_ID int,INBOUND int,TOUR_PURPOSE varchar(20),ORIG_PURPOSE varchar(20),DEST_PURPOSE varchar(20),ORIG_MGRA int,DEST_MGRA int,PARKING_MGRA int,STOP_PERIOD int,TRIP_MODE int,NUM_PARTICIPANTS int, TRIP_BOARD_TAP int,TRIP_ALIGHT_TAP int,TOUR_MODE int,TRIP_TIME float(10),TRIP_DISTANCE float(10),TRIP_COST float(10),TRIP_PURPOSE_NAME varchar(20),TRIP_MODE_NAME varchar(20),RECID int,TRIP_BOARD_TAZ int,TRIP_ALIGHT_TAZ int,ORIG_TAZ int,DEST_TAZ int,PERID int,HOUSEHOLD_SERIAL_NO float(20),PNUM int,AGE int,SEX int,MILITARY int,PEMPLOY int,PSTUDENT int,PTYPE int,EDUC int,GRADE int,OCCCEN1 int,INDCEN int,WKW int,WKHP int); ");
            writer.println("DECLARE @i as int; ");
            writer.println("SET @i = 1; ");
            writer.println("DECLARE @numrows int;");
            writer.println("SET @numrows = (SELECT COUNT(*) FROM " + schema + ".temp_jointtriptour); ");
            writer.println("IF @numrows > 0 ");
            writer.println("WHILE (@i <= @numrows) ");
            writer.println("BEGIN");
            writer.println("	DECLARE @participants as VARCHAR(40); ");
            writer.println("	SET @participants = (SELECT TOUR_PARTICIPANTS FROM " + schema + ".temp_jointtriptour WHERE rn = @i);");
            writer.println("	DECLARE @pos int;");
            writer.println("	DECLARE @pnum int;");
            writer.println("	IF RIGHT(RTRIM(@participants),1) <> ' ' ");
            writer.println("	SET @participants = @participants  + ' ' ");
            writer.println("	SET @pos =  PATINDEX('% %' , @participants); ");
            writer.println("	WHILE @pos <> 0 ");
            writer.println("	BEGIN ");
            writer.println("		SET @pnum = CAST(left(@participants, @pos-1) as int); ");
            writer.println("		INSERT INTO " + schema + ".TRIP(HH_ID,TOUR_ID,STOP_ID,INBOUND,TOUR_PURPOSE,ORIG_PURPOSE,DEST_PURPOSE,ORIG_MGRA,DEST_MGRA,PARKING_MGRA,STOP_PERIOD,TRIP_MODE,NUM_PARTICIPANTS, TRIP_BOARD_TAP,TRIP_ALIGHT_TAP,TOUR_MODE,TRIP_TIME,TRIP_DISTANCE,TRIP_COST,TRIP_PURPOSE_NAME,TRIP_MODE_NAME,RECID,TRIP_BOARD_TAZ,TRIP_ALIGHT_TAZ,ORIG_TAZ,DEST_TAZ,PERID,HOUSEHOLD_SERIAL_NO,PNUM,AGE,SEX,MILITARY,PEMPLOY,PSTUDENT,PTYPE,EDUC,GRADE,OCCCEN1,INDCEN,WKW,WKHP) "); 	 
            writer.println("		SELECT JTT.HH_ID,JTT.TOUR_ID,JTT.STOP_ID,JTT.INBOUND,JTT.TOUR_PURPOSE,JTT.ORIG_PURPOSE,JTT.DEST_PURPOSE,JTT.ORIG_MGRA,JTT.DEST_MGRA,JTT.PARKING_MGRA,JTT.STOP_PERIOD,JTT.TRIP_MODE,JTT.NUM_PARTICIPANTS, JTT.TRIP_BOARD_TAP,JTT.TRIP_ALIGHT_TAP,JTT.TOUR_MODE,JTT.TRIP_TIME,JTT.TRIP_DISTANCE,JTT.TRIP_COST,JTT.TRIP_PURPOSE_NAME,JTT.TRIP_MODE_NAME,JTT.RECID,JTT.TRIP_BOARD_TAZ, JTT.TRIP_ALIGHT_TAZ,JTT.ORIG_TAZ,JTT.DEST_TAZ,SP.PERID,SP.HOUSEHOLD_SERIAL_NO,SP.PNUM,SP.AGE,SP.SEX,SP.MILITARY,SP.PEMPLOY,SP.PSTUDENT,SP.PTYPE,SP.EDUC,SP.GRADE,SP.OCCCEN1,SP.INDCEN,SP.WKW,SP.WKHP ");
            writer.println("		FROM " + schema + ".temp_jointtriptour as JTT INNER JOIN " + schema + ".SYNPERSON as SP ON JTT.HH_ID = SP.HHID WHERE rn = @i AND SP.PNUM = @pnum; ");
            writer.println("		SET @participants = STUFF(@participants, 1, @pos, ''); ");
            writer.println("		SET @pos =  PATINDEX('% %' , @participants); ");
            writer.println("	END ");
            writer.println("	SET @i = @i + 1 ");
            writer.println("END ");
            writer.println();
            writer.println("INSERT INTO " + schema + ".TRIP(HH_ID,TOUR_ID,STOP_ID,INBOUND,TOUR_PURPOSE,ORIG_PURPOSE,DEST_PURPOSE,ORIG_MGRA,DEST_MGRA,PARKING_MGRA,STOP_PERIOD,TRIP_MODE,NUM_PARTICIPANTS, TRIP_BOARD_TAP,TRIP_ALIGHT_TAP,TOUR_MODE,TRIP_TIME,TRIP_DISTANCE,TRIP_COST,TRIP_PURPOSE_NAME,TRIP_MODE_NAME,RECID,TRIP_BOARD_TAZ,TRIP_ALIGHT_TAZ,ORIG_TAZ,DEST_TAZ,PERID,HOUSEHOLD_SERIAL_NO,PNUM,AGE,SEX,MILITARY,PEMPLOY,PSTUDENT,PTYPE,EDUC,GRADE,OCCCEN1,INDCEN,WKW,WKHP)");
            writer.println("SELECT ITT.HH_ID,ITT.TOUR_ID,ITT.STOP_ID,ITT.INBOUND,ITT.TOUR_PURPOSE,ITT.ORIG_PURPOSE,ITT.DEST_PURPOSE,ITT.ORIG_MGRA,ITT.DEST_MGRA,ITT.PARKING_MGRA,ITT.STOP_PERIOD,ITT.TRIP_MODE,1, ITT.TRIP_BOARD_TAP,ITT.TRIP_ALIGHT_TAP,ITT.TOUR_MODE,ITT.TRIP_TIME,ITT.TRIP_DISTANCE,ITT.TRIP_COST,ITT.TRIP_PURPOSE_NAME,ITT.TRIP_MODE_NAME,ITT.RECID,ITT.TRIP_BOARD_TAZ, ITT.TRIP_ALIGHT_TAZ,ITT.ORIG_TAZ,ITT.DEST_TAZ,SP.PERID,SP.HOUSEHOLD_SERIAL_NO,SP.PNUM,SP.AGE,SP.SEX,SP.MILITARY,SP.PEMPLOY,SP.PSTUDENT,SP.PTYPE,SP.EDUC,SP.GRADE,SP.OCCCEN1,SP.INDCEN,SP.WKW,SP.WKHP ");
            writer.println("FROM " + schema + ".INDIVTRIPS as ITT INNER JOIN " + schema + ".SYNPERSON as SP ON ITT.PERSON_ID = SP.PERID; ");
            writer.println("ALTER TABLE " + schema + ".TRIP ADD occ_code varchar(20);");
            writer.println("UPDATE " + schema + ".TRIP SET occ_code = (SELECT pecas_occ FROM " + schema + ".PECASCODES as POC WHERE " + schema + ".TRIP.OCCCEN1 = POC.OCCCEN1);");
            writer.println("IF OBJECT_ID('" + schema + ".temp_jointtriptour') IS NOT NULL DROP TABLE " + schema + ".temp_jointtriptour;");    
            
            
            
            //EXPLODE TOUR TABLE INTO ALL POSSIBLE JOINT AND INDIVIDUAL TOURS AND CORRESPONDING TRAVELER ATTRIBUTES
            writer.println();
            writer.println();
            writer.println("IF OBJECT_ID('" + schema + ".temp_tour') IS NOT NULL"); 
            writer.println("DROP TABLE " + schema + ".temp_tour;");
            writer.println();
            writer.println("SELECT HH_ID,TOUR_ID,TOUR_CATEGORY,TOUR_PURPOSE,TOUR_COMPOSITION,TOUR_PARTICIPANTS,ORIG_MGRA,DEST_MGRA,START_PERIOD,END_PERIOD,TOUR_MODE,NUM_OB_STOPS,NUM_IB_STOPS");
            writer.println("	INTO " + schema + ".temp_tour");
            writer.println("	FROM " + schema + ".JOINTTOURS;");
			writer.println("ALTER TABLE " + schema + ".temp_tour ADD rn INT IDENTITY (1,1);");
			writer.println("CREATE INDEX ind2 ON " + schema + ".temp_tour(HH_ID);");
			writer.println("IF OBJECT_ID('" + schema + ".TOUR') IS NOT NULL DROP TABLE " + schema + ".TOUR;");
			writer.println();
			writer.println("CREATE TABLE " + schema + ".TOUR (HH_ID int,TOUR_ID int,TOUR_CATEGORY varchar(40),TOUR_PURPOSE varchar(20),ORIG_MGRA int,DEST_MGRA int,START_PERIOD int,END_PERIOD int,TOUR_MODE int, NUM_OB_STOPS int, NUM_IB_STOPS int, PERID int,HOUSEHOLD_SERIAL_NO float(20),PNUM int,AGE int,SEX int,MILITARY int,PEMPLOY int,PSTUDENT int,PTYPE int,EDUC int,GRADE int,OCCCEN1 int,INDCEN int,WKW int,WKHP int,NUM_PARTICIPANTS int, TOUR_PARTICIPANTS varchar(20));"); 
			writer.println("SET @i = 1; ");
			writer.println("SET @numrows = (SELECT COUNT(*) FROM " + schema + ".temp_tour); ");
			writer.println("IF @numrows > 0 ");
			writer.println("WHILE (@i <= @numrows) ");
			writer.println("BEGIN");
			writer.println("	SET @participants = (SELECT TOUR_PARTICIPANTS FROM " + schema + ".temp_tour WHERE rn = @i);");
			writer.println("	IF RIGHT(RTRIM(@participants),1) <> ' ' ");
			writer.println("	SET @participants = @participants  + ' ' ");
			writer.println("	SET @pos =  PATINDEX('% %' , @participants);"); 
			writer.println("	WHILE @pos <> 0 ");
			writer.println("	BEGIN ");
			writer.println("		SET @pnum = CAST(left(@participants, @pos-1) as int); ");
			writer.println("		INSERT INTO " + schema + ".TOUR(HH_ID,TOUR_ID,TOUR_CATEGORY,TOUR_PURPOSE,ORIG_MGRA,DEST_MGRA,START_PERIOD,END_PERIOD,TOUR_MODE,NUM_OB_STOPS,NUM_IB_STOPS,PERID,HOUSEHOLD_SERIAL_NO,PNUM,AGE,SEX,MILITARY,PEMPLOY,PSTUDENT,PTYPE,EDUC,GRADE,OCCCEN1,INDCEN,WKW,WKHP,NUM_PARTICIPANTS,TOUR_PARTICIPANTS) ");
			writer.println("		SELECT JTT.HH_ID,JTT.TOUR_ID,JTT.TOUR_CATEGORY,JTT.TOUR_PURPOSE,JTT.ORIG_MGRA,JTT.DEST_MGRA,JTT.START_PERIOD,JTT.END_PERIOD,JTT.TOUR_MODE,JTT.NUM_OB_STOPS,JTT.NUM_IB_STOPS,SP.PERID,SP.HOUSEHOLD_SERIAL_NO,SP.PNUM,SP.AGE,SP.SEX,SP.MILITARY,SP.PEMPLOY,SP.PSTUDENT,SP.PTYPE,SP.EDUC,SP.GRADE,SP.OCCCEN1,SP.INDCEN,SP.WKW,SP.WKHP,LEN(REPLACE(@participants,' ','')), @participants");
			writer.println("		FROM " + schema + ".temp_tour as JTT INNER JOIN " + schema + ".SYNPERSON as SP ON JTT.HH_ID = SP.HHID WHERE rn = @i AND SP.PNUM = @pnum; ");
			writer.println("		SET @participants = STUFF(@participants, 1, @pos, ''); ");
			writer.println("		SET @pos =  PATINDEX('% %' , @participants); ");
			writer.println("	END ");
			writer.println("	SET @i = @i + 1 ");
			writer.println("END ");
			writer.println();
			writer.println("ALTER TABLE " + schema + ".TOUR ADD TOUR_DISTANCE real;");
			writer.println("UPDATE " + schema + ".TOUR SET TOUR_DISTANCE = (SELECT SUM(TRIP_DISTANCE) FROM " + schema + ".JOINTTRIPS as T WHERE " + schema + ".TOUR.HH_ID = T.HH_ID AND " + schema + ".TOUR.TOUR_ID = T.TOUR_ID);");
			writer.println("ALTER TABLE " + schema + ".TOUR ADD TOUR_TIME real;");
			writer.println("UPDATE " + schema + ".TOUR SET TOUR_TIME = (SELECT SUM(TRIP_TIME) FROM " + schema + ".JOINTTRIPS as T WHERE " + schema + ".TOUR.HH_ID = T.HH_ID AND " + schema + ".TOUR.TOUR_ID = T.TOUR_ID);");
			writer.println("ALTER TABLE " + schema + ".TOUR ADD TOUR_TYPE varchar(10);");
			writer.println("UPDATE " + schema + ".TOUR SET TOUR_TYPE = 'JOINT';");
			writer.println();
			writer.println("INSERT INTO " + schema + ".TOUR(HH_ID,TOUR_ID,TOUR_CATEGORY,TOUR_PURPOSE,ORIG_MGRA,DEST_MGRA,START_PERIOD,END_PERIOD,TOUR_MODE,NUM_OB_STOPS,NUM_IB_STOPS,PERID,HOUSEHOLD_SERIAL_NO,PNUM,AGE,SEX,MILITARY,PEMPLOY,PSTUDENT,PTYPE,EDUC,GRADE,OCCCEN1,INDCEN,WKW,WKHP)");
			writer.println("SELECT ITT.HH_ID,ITT.TOUR_ID,ITT.TOUR_CATEGORY,ITT.TOUR_PURPOSE,ITT.ORIG_MGRA,ITT.DEST_MGRA,ITT.START_PERIOD,ITT.END_PERIOD,ITT.TOUR_MODE,ITT.NUM_OB_STOPS,ITT.NUM_IB_STOPS,SP.PERID,SP.HOUSEHOLD_SERIAL_NO,SP.PNUM,SP.AGE,SP.SEX,SP.MILITARY,SP.PEMPLOY,SP.PSTUDENT,SP.PTYPE,SP.EDUC,SP.GRADE,SP.OCCCEN1,SP.INDCEN,SP.WKW,SP.WKHP ");
			writer.println("FROM " + schema + ".INDIVTOURS as ITT INNER JOIN " + schema + ".SYNPERSON as SP ON ITT.PERSON_ID = SP.PERID; ");
			writer.println("UPDATE " + schema + ".TOUR SET TOUR_DISTANCE = (SELECT SUM(TRIP_DISTANCE) FROM " + schema + ".INDIVTRIPS as T WHERE " + schema + ".TOUR.PERID = T.PERSON_ID AND " + schema + ".TOUR.TOUR_ID = T.TOUR_ID) WHERE " + schema + ".TOUR.TOUR_DISTANCE IS NULL;");
			writer.println("UPDATE " + schema + ".TOUR SET TOUR_TIME = (SELECT SUM(TRIP_TIME) FROM " + schema + ".INDIVTRIPS as T WHERE " + schema + ".TOUR.PERID = T.PERSON_ID AND " + schema + ".TOUR.TOUR_ID = T.TOUR_ID) WHERE " + schema + ".TOUR.TOUR_TIME IS NULL;");
			writer.println("UPDATE " + schema + ".TOUR SET TOUR_TYPE = 'INDIV' WHERE TOUR_TYPE IS NULL;");
			writer.println("UPDATE " + schema + ".TOUR SET NUM_PARTICIPANTS = 1 WHERE NUM_PARTICIPANTS IS NULL;");
			writer.println("UPDATE " + schema + ".TOUR SET TOUR_PARTICIPANTS = CAST(PNUM as varchar(20)) WHERE TOUR_PARTICIPANTS IS NULL;");
			writer.println();
			writer.println("ALTER TABLE " + schema + ".TOUR ADD ORIG_TAZ int;");
			writer.println("UPDATE " + schema + ".TOUR SET ORIG_TAZ = (SELECT T.TAZ FROM " + schema + ".MGRA as T WHERE T.MGRA = ORIG_MGRA);");
			writer.println("ALTER TABLE " + schema + ".TOUR ADD DEST_TAZ int;");
			writer.println("UPDATE " + schema + ".TOUR SET DEST_TAZ = (SELECT T.TAZ FROM " + schema + ".MGRA as T WHERE T.MGRA = DEST_MGRA);");
			writer.println("IF OBJECT_ID('" + schema + ".temp_tour') IS NOT NULL DROP TABLE " + schema + ".temp_tour;");
            writer.println("CREATE INDEX ind4 ON " + schema + ".TRIP(PERID);");
            writer.println("CREATE INDEX ind5 ON " + schema + ".TOUR(HH_ID);");
			
        } catch (IOException e) {
            throw new RuntimeException(e);

        } finally {
            if (writer != null)
                writer.close();
        }
    }

    private String addSchemaInformation(String line, String schema) {
        return line.replace("CREATE TABLE ","CREATE TABLE " + schema + ".")
                   .replace("BULK INSERT ","BULK INSERT " + schema + ".");
    }
    


    public static void main(String ... args) {
        //usage: input_dir schema_name [keepSqlFiles?]
        String sourceDir = args[0];
        List<String> tables = new LinkedList<String>();
        File[] sqlFiles = new File(sourceDir).listFiles(new FilenameFilter() {
            @Override
            public boolean accept(File dir, String name) {
                return name.endsWith("sql");
            }
        });
        File[] csvFiles = new File(sourceDir).listFiles(new FilenameFilter() {
            @Override
            public boolean accept(File dir, String name) {
                return name.endsWith("csv");
            }
        });
        for (File f : sqlFiles) {
            String csv = f.getName().replace(".sql",".csv");
            for (File ff : csvFiles) {
                if (ff.getName().equalsIgnoreCase(csv)) {
                    tables.add(csv.replace(".csv","").toLowerCase());
                    break;
                }
            }
        }
        
        //Check if need to cleanup SQL files after run
        boolean deleteSqlFiles = false;
        if (args.length > 2 && args[2].equals("TRUE"))
        	deleteSqlFiles = true;

        SqlImportFileBuilder sqlmIFB = new SqlImportFileBuilder();
        sqlmIFB.buildImportFile(sourceDir,tables,"sql_table_import.sql",args[1],deleteSqlFiles);
    }
}
