package com.pb.mtctm2.abm.reports;

import com.pb.common.calculator.DataEntry;
import com.pb.common.calculator.MatrixDataServerIf;
import com.pb.common.datafile.CSVFileReader;
import com.pb.common.datafile.TableDataSet;
import com.pb.common.matrix.Matrix;
import com.pb.common.util.ResourceUtil;
import org.apache.log4j.Logger;
import com.pb.mtctm2.abm.ctramp.MatrixDataServer;
import com.pb.mtctm2.abm.ctramp.MatrixDataServerRmi;
import com.pb.mtctm2.abm.ctramp.ModelStructure;

import java.io.*;
import java.lang.reflect.Method;
import java.net.MalformedURLException;
import java.net.URL;
import java.net.URLClassLoader;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * The {@code DataExporter} ...
 *
 * @author crf
 *         Started 9/20/12 8:36 AM
 * @revised 5/6/2013 for SERPM (ymm)
 */
public class DataExporter {
    private static final Logger logger = Logger.getLogger(DataExporter.class);

    private static final String NUMBER_FORMAT_NAME = "NUMBER";
    private static final String STRING_FORMAT_NAME = "STRING";
    public static final String PROJECT_PATH_PROPERTY_TOKEN = "%project.folder%"; 
    private static final String TOD_TOKEN = "%TOD%";

    private final Properties properties;
//    private final String projectPath;
    private final File projectPathFile;
    private final String outputPath;
    private final int feedbackIterationNumber;
    private final Set<String> tables;
    private final String[] timePeriods = ModelStructure.MODEL_PERIOD_LABELS;

    public DataExporter(String propertiesFile, String projectPath, int feedbackIterationNumber, String outputPath) {
        projectPath = new File(projectPath).getAbsolutePath().replace("\\","/");
        properties = new Properties();
        try {
            properties.load(new FileInputStream(propertiesFile));
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        for (Object key : properties.keySet()) {
            String value = (String) properties.get(key);
            properties.setProperty((String) key,value.replace(PROJECT_PATH_PROPERTY_TOKEN,projectPath));
        }
        projectPathFile = new File(projectPath);
//        this.projectPath = projectPath;
        this.feedbackIterationNumber = feedbackIterationNumber;
        this.outputPath = outputPath;
        tables = new LinkedHashSet<String>();
    }

    private void addTable(String table) {
        tables.add(table);
        logger.info("exporting data: " + table);
        try {
            clearMatrixServer();
        } catch (Throwable e) {
            //log it, but swallow it
            logger.warn("exception caught clearing matrix server: " + e.getMessage());
        }
    }

    private void clearMatrixServer() {
        String serverAddress = (String) properties.get("RunModel.MatrixServerAddress");
        int serverPort = Integer.parseInt((String) properties.get("RunModel.MatrixServerPort"));
        new MatrixDataServerRmi(serverAddress,serverPort,MatrixDataServer.MATRIX_DATA_SERVER_NAME).clear();
    }

    private String getPath(String path) {
        if (properties.containsKey(path))
            return getPathFromProperty(path);
        File ff = new File(path);
        if (!ff.exists())
            ff = new File(projectPathFile,path);
        return ff.getAbsolutePath();
    }

    //Have to check for forward slashes otherwise path is corrupt
    private String getPathFromProperty(String propertyToken) {
        String path = (String) properties.get(propertyToken);
        String pathSlashes = path.replaceAll("/","\\\\");
        if (!path.startsWith(projectPathFile.getAbsolutePath()) && !pathSlashes.startsWith(projectPathFile.getAbsolutePath()))
        {
        	path = new File(projectPathFile,path).getAbsolutePath();
        }
        return path;
    }

    private String getOutputPath(String file) {
        return new File(outputPath,file).getAbsolutePath();
    }

    private String getData(TableDataSet data, int row, int column, FieldType type) {
        switch (type) {
            case INT : return "" + Math.round(data.getValueAt(row,column));
            case FLOAT : return "" + data.getValueAt(row,column);
            case STRING : return data.getStringValueAt(row,column);
            case BIT : return Boolean.parseBoolean(data.getStringValueAt(row,column)) ? "1" : "0";
            default : throw new IllegalStateException("undefined field type: " + type);
        }
    }

    private String getPreferredColumnName(String columnName) {
        if (columnName.equalsIgnoreCase("hh_id"))
            return "HH_ID";
        if (columnName.equalsIgnoreCase("person_id"))
            return "PERSON_ID";
        if (columnName.toLowerCase().contains("maz"))
            return columnName.toLowerCase().replace("maz","mgra").toUpperCase();
        return columnName.toUpperCase();
    }






    private void exportData(String tableName, TableDataSet data, String outputFileBase, Map<String,String> outputMapping, Map<String,FieldType> outputTypes, Set<String> primaryKeys){
        Map<String,Integer> stringWidths = exportData(data,outputFileBase + ".csv",outputMapping,outputTypes);
        saveSqlImport(tableName,outputFileBase,outputMapping,outputTypes,primaryKeys,stringWidths);
    }

    private Map<String,Integer> exportData(TableDataSet data, String outputFileName, Map<String,String> outputMapping, Map<String,FieldType> outputTypes) {
        int[] outputIndices = new int[outputMapping.size()];
        FieldType[] outputFieldTypes = new FieldType[outputIndices.length];
        int[] stringWidths = new int[outputIndices.length];
        StringBuilder header = new StringBuilder();
        boolean first = true;
        int counter = 0;
        for (String column : outputMapping.keySet()) {
            if (first) {
                first = false;
            } else {
                header.append(",");
            }
            header.append(column);
            outputIndices[counter] = data.getColumnPosition(outputMapping.get(column));
            outputFieldTypes[counter] = outputTypes.get(column);
            stringWidths[counter++] = 0;
        }

        PrintWriter writer = null;
        try {
            writer = new PrintWriter(getOutputPath(outputFileName));
            writer.println(header.toString());

            for (int i = 1; i <= data.getRowCount(); i++) {
                StringBuilder line = new StringBuilder();
                line.append(getData(data,i,outputIndices[0],outputFieldTypes[0]));
                for (int j = 1; j < outputIndices.length; j++) {
                    String d = getData(data,i,outputIndices[j],outputFieldTypes[j]);
                    line.append(",").append(d);
                    stringWidths[j] = Math.max(stringWidths[j],d.length());
                }
                writer.println(line.toString());
            }
        } catch (IOException e) {
            throw new RuntimeException(e);
        } finally {
            if (writer != null)
                writer.close();
        }

        Map<String,Integer> widths = new HashMap<String,Integer>();
        counter = 0;
        for (String column : outputMapping.keySet()) {
            if (outputTypes.get(column) == FieldType.STRING)
                widths.put(column,Math.round(stringWidths[counter]*1.5f));
            counter++;
        }

        return widths;
    }

    private TableDataSet exportDataGeneric(String outputFileBase, String filePropertyToken, boolean includeFeedbackIteration, String[] formats,
                                           Set<String> floatColumns, Set<String> stringColumns, Set<String> intColumns, Set<String> bitColumns, FieldType defaultFieldType, Set<String> primaryKey, TripStructureDefinition tripStructureDefinition) {
        return exportDataGeneric(outputFileBase,filePropertyToken,includeFeedbackIteration,formats,floatColumns,stringColumns,intColumns,bitColumns,defaultFieldType,primaryKey,tripStructureDefinition,null);
    }

    private TableDataSet exportDataGeneric(String outputFileBase, String filePropertyToken, boolean includeFeedbackIteration, String[] formats,
                                       Set<String> floatColumns, Set<String> stringColumns, Set<String> intColumns, Set<String> bitColumns, FieldType defaultFieldType, Set<String> primaryKey, TripStructureDefinition tripStructureDefinition, JoinData joinData) {
        return exportDataGeneric(outputFileBase,filePropertyToken,includeFeedbackIteration,formats,floatColumns,stringColumns,intColumns,bitColumns,defaultFieldType,primaryKey,new HashMap<String,String>(),tripStructureDefinition,joinData);
    }

    private TableDataSet exportDataGeneric(String outputFileBase, String filePropertyToken, boolean includeFeedbackIteration, String[] formats,
                                           Set<String> floatColumns, Set<String> stringColumns, Set<String> intColumns, Set<String> bitColumns, FieldType defaultFieldType, Set<String> primaryKey,
                                           Map<String,String> overridingFieldMappings, TripStructureDefinition tripStructureDefinition) {
        return exportDataGeneric(outputFileBase,filePropertyToken,includeFeedbackIteration,formats,floatColumns,stringColumns,intColumns,bitColumns,defaultFieldType,primaryKey,overridingFieldMappings,tripStructureDefinition,null);
    }

    private TableDataSet exportDataGeneric(String outputFileBase, String filePropertyToken, boolean includeFeedbackIteration, String[] formats,
                                       Set<String> floatColumns, Set<String> stringColumns, Set<String> intColumns, Set<String> bitColumns, FieldType defaultFieldType, Set<String> primaryKey,
                                       Map<String,String> overridingFieldMappings, TripStructureDefinition tripStructureDefinition, JoinData joinData) {
        TableDataSet table;
        try {
            String f = includeFeedbackIteration ? getPath(filePropertyToken).replace(".csv","_" + feedbackIterationNumber + ".csv") : getPath(filePropertyToken);
            table = formats == null ? new CSVFileReader().readFile(new File(f)) : new CSVFileReader().readFileWithFormats(new File(f),formats);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        if (joinData != null)
            joinData.joinDataToTable(table);
        exportDataGeneric(table,outputFileBase,floatColumns,stringColumns,intColumns,bitColumns,defaultFieldType,primaryKey,overridingFieldMappings,tripStructureDefinition);
        return table;
    }

    private class JoinData {
        private final Map<String,Map<Integer,?>> data;
        private final Map<String,FieldType> dataType;
        private final String idColumn;

        public JoinData(String idColumn) {
            this.idColumn = idColumn;
            data = new LinkedHashMap<String,Map<Integer,?>>();
            dataType = new HashMap<String,FieldType>();
        }

        public void addJoinData(Map<Integer,?> joinData, FieldType type, String columnName) {
            data.put(columnName,joinData);
            dataType.put(columnName,type);
        }

        public void joinDataToTable(TableDataSet table) {
            int[] ids = table.getColumnAsInt(idColumn);
            for (String column : data.keySet())
                table.appendColumn(getData(ids,column),column);
        }

        private Object getData(int[] ids, String column) {
            switch (dataType.get(column)) {
                case INT : {
                    int[] columnData = new int[ids.length];
                    @SuppressWarnings("unchecked") //this is correct
                    Map<Integer,Integer> dataMap = (Map<Integer,Integer>) data.get(column);
                    for (int i = 0; i < ids.length; i++)
                        columnData[i] = dataMap.get(ids[i]);
                    return columnData;
                }
                case FLOAT : {
                    float[] columnData = new float[ids.length];
                    @SuppressWarnings("unchecked") //this is correct
                    Map<Integer,Float> dataMap = (Map<Integer,Float>) data.get(column);
                    for (int i = 0; i < ids.length; i++)
                        columnData[i] = dataMap.get(ids[i]);
                    return columnData;
                }
                case STRING : {
                    String[] columnData = new String[ids.length];
                    @SuppressWarnings("unchecked") //this is correct
                    Map<Integer,String> dataMap = (Map<Integer,String>) data.get(column);
                    for (int i = 0; i < ids.length; i++)
                        columnData[i] = dataMap.get(ids[i]);
                    return columnData;
                }
                case BIT : {
                    boolean[] columnData = new boolean[ids.length];
                    @SuppressWarnings("unchecked") //this is correct
                    Map<Integer,Boolean> dataMap = (Map<Integer,Boolean>) data.get(column);
                    for (int i = 0; i < ids.length; i++)
                        columnData[i] = dataMap.get(ids[i]);
                    return columnData;
                }
                default : throw new IllegalStateException("shouldn't be here: " + dataType.get(column));
            }
        }
    }

    private void exportDataGeneric(TableDataSet table, String outputFileBase,
                                   Set<String> floatColumns, Set<String> stringColumns, Set<String> intColumns, Set<String> bitColumns,
                                   FieldType defaultFieldType, Set<String> primaryKey, TripStructureDefinition tripStructureDefinition) {
        exportDataGeneric(table,outputFileBase,floatColumns,stringColumns,intColumns,bitColumns,defaultFieldType,primaryKey,new HashMap<String,String>(),tripStructureDefinition);

    }

    private void exportDataGeneric(TableDataSet table, String outputFileBase,
                                   Set<String> floatColumns, Set<String> stringColumns, Set<String> intColumns, Set<String> bitColumns,
                                   FieldType defaultFieldType, Set<String> primaryKey,
                                   Map<String,String> overridingFieldMappings, TripStructureDefinition tripStructureDefinition) {
        Map<String,String> fieldMappings = new LinkedHashMap<String,String>();
        Map<String,FieldType> fieldTypes = new HashMap<String,FieldType>();

        if (tripStructureDefinition != null) {
            appendTripData(table,tripStructureDefinition);
            floatColumns.add("TRIP_TIME");
            floatColumns.add("TRIP_DISTANCE");
            floatColumns.add("TRIP_COST");
            stringColumns.add("TRIP_PURPOSE_NAME");
            stringColumns.add("TRIP_MODE_NAME");
            intColumns.add("RECID");
        }
        
        if (primaryKey.size() == 0) {
            //have to add in a key - call it ID
            int[] id = new int[table.getRowCount()];
            for (int i = 0; i < id.length; i++)
                id[i] = i+1;
            table.appendColumn(id,"ID");

            primaryKey.add("ID");
            intColumns.add("ID");
        }

        outer:
        for (String column : table.getColumnLabels()) {
            String c = overridingFieldMappings.containsKey(column) ? overridingFieldMappings.get(column) : getPreferredColumnName(column);
            fieldMappings.put(c,column);
            for (String fc : floatColumns) {
                if (fc.equalsIgnoreCase(column)) {
                    fieldTypes.put(c,FieldType.FLOAT);
                    continue outer;
                }
            }
            for (String sc : stringColumns) {
                if (sc.equalsIgnoreCase(column)) {
                    fieldTypes.put(c,FieldType.STRING);
                    continue outer;
                }
            }
            for (String ic : intColumns) {
                if (ic.equalsIgnoreCase(column)) {
                    fieldTypes.put(c,FieldType.INT);
                    continue outer;
                }
            }
            for (String bc : bitColumns) {
                if (bc.equalsIgnoreCase(column)) {
                    fieldTypes.put(c,FieldType.BIT);
                    continue outer;
                }
            }
            fieldTypes.put(c,defaultFieldType);
        }
        Set<String> pKey = new LinkedHashSet<String>();
        for (String column : primaryKey)
            pKey.add(getPreferredColumnName(column));
        exportData(outputFileBase.toUpperCase(),table,outputFileBase,fieldMappings,fieldTypes,pKey);
    }




    private String getSqlType(FieldType type, int width) {
        switch (type) {
            case INT : return "int";
            case FLOAT : return "real";
            case STRING : return "varchar(" + width + ")";
            case BIT : return "bit";
            default : throw new IllegalArgumentException("shouldn't be here");
        }
    }

    private void saveSqlImport(String tableName, String outputFileBase, Map<String,String> outputMapping, Map<String,FieldType> outputTypes, Set<String> primaryKeys, Map<String,Integer> stringWidths) {
        String lineSeparator = System.getProperty("line.separator");
        StringBuilder sql = new StringBuilder();
        sql.append("CREATE TABLE ").append(tableName).append(" (").append(lineSeparator);
        for (String column : outputMapping.keySet())
            sql.append("    ").append(column).append(" ").append(getSqlType(outputTypes.get(column),stringWidths.containsKey(column) ? stringWidths.get(column) : -1)).append(",").append(lineSeparator); //null values for int/reals will be ignored in widths
        sql.append("    ").append("CONSTRAINT ").append(tableName).append("_pkey PRIMARY KEY (");
        boolean first = true;
        for (String column : primaryKeys) {
            if (first) {
                first = false;
            } else {
                sql.append(",");
            }
            sql.append(column);
        }
        sql.append(")").append(lineSeparator).append(")").append(lineSeparator);
        sql.append(lineSeparator);
        sql.append("BULK INSERT ").append(tableName).append(" FROM \"").append(new File(getOutputPath(outputFileBase + ".csv")).getAbsolutePath()).append("\" WITH (").append(lineSeparator);
        sql.append("    FIELDTERMINATOR=',', FIRSTROW=2, MAXERRORS=0, TABLOCK)").append(lineSeparator);
        sql.append(lineSeparator);


        PrintWriter writer = null;
        try {
            writer = new PrintWriter(getOutputPath(outputFileBase + ".sql"));
            writer.print(sql.toString());
        } catch (IOException e) {
            throw new RuntimeException(e);
        } finally {
            if (writer != null)
                writer.close();
        }
    }

    private volatile PrintWriter tripTableWriter;
    private void initializeMasterTripTable(String baseTableName) {
        logger.info("setting up master trip table: " + baseTableName);
        addTable(baseTableName);
        try {
            tripTableWriter = new PrintWriter(getOutputPath(baseTableName + ".csv"));
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        Map<String,String> outputMapping = new LinkedHashMap<String,String>();
        Map<String,FieldType> outputTypes = new LinkedHashMap<String,FieldType>();
        Map<String,Integer> stringWidths = new HashMap<String,Integer>();
        outputTypes.put("ID",FieldType.INT);
        outputTypes.put("TRIPTYPE",FieldType.STRING);
        stringWidths.put("TRIPTYPE",10);
        outputTypes.put("RECID",FieldType.INT);
        outputTypes.put("PARTYSIZE",FieldType.INT);
        outputTypes.put("ORIG_MGRA",FieldType.INT);
        outputTypes.put("DEST_MGRA",FieldType.INT);
        outputTypes.put("ORIG_TAZ",FieldType.INT);
        outputTypes.put("DEST_TAZ",FieldType.INT);
        outputTypes.put("TRIP_BOARD_TAP",FieldType.INT);
        outputTypes.put("TRIP_ALIGHT_TAP",FieldType.INT);
        outputTypes.put("TRIP_BOARD_TAZ",FieldType.INT);
        outputTypes.put("TRIP_ALIGHT_TAZ",FieldType.INT);
        outputTypes.put("TRIP_DEPART_TIME",FieldType.INT);
        outputTypes.put("TRIP_TIME",FieldType.FLOAT);
        outputTypes.put("TRIP_DISTANCE",FieldType.FLOAT);
        outputTypes.put("TRIP_COST",FieldType.FLOAT);
        outputTypes.put("TRIP_PURPOSE_NAME",FieldType.STRING);
        stringWidths.put("TRIP_PURPOSE_NAME",30);
        outputTypes.put("TRIP_MODE_NAME",FieldType.STRING);
        stringWidths.put("TRIP_MODE_NAME",20);
        Set<String> primaryKeys = new HashSet<String>();
        primaryKeys.add("ID");
        StringBuilder header = new StringBuilder();
        for (String column : outputTypes.keySet()) {
            outputMapping.put(column,column);
            header.append(",").append(column.toLowerCase());
        }
        tripTableWriter.println(header.deleteCharAt(0).toString());
        saveSqlImport(baseTableName.toUpperCase(),baseTableName,outputMapping,outputTypes,primaryKeys,stringWidths);
    }

    private void appendTripData(TableDataSet table, TripStructureDefinition tripStructureDefinition) {
        //id triptype recid partysize orig_mgra dest_mgra trip_board_tap trip_alight_tap trip_depart_time trip_time trip_distance trip_cost trip_purpose_name trip_mode_name
        int rowCount = table.getRowCount();
        //columns to add: trip_time, trip_distance, trip_cost, trip_purpose_name, trip_mode_name, recid
        float[] tripTime = new float[rowCount];
        float[] tripDistance = new float[rowCount];
        float[] tripCost = new float[rowCount];
        String[] tripPurpose = new String[rowCount];
        String[] tripMode = new String[rowCount];
        int[] tripId = new int[rowCount];
        int[] tripDepartTime = new int[rowCount];
        int[] tripBoardTaz = new int[rowCount];
        int[] tripAlightTaz = new int[rowCount];
        int[] originTaz = new int[rowCount];
        int[] destinationTaz = new int[rowCount];

        SkimBuilder skimBuilder = new SkimBuilder(properties);
        boolean hasPurposeColumn = tripStructureDefinition.originPurposeColumn > -1;
        for (int i = 0; i < rowCount; i++) {
            int row = i+1;

            boolean inbound = tripStructureDefinition.booleanIndicatorVariables ? table.getBooleanValueAt(row,tripStructureDefinition.inboundColumn) :
                                table.getValueAt(row,tripStructureDefinition.inboundColumn) == 1.0;
         


            SkimBuilder.TripAttributes attributes = skimBuilder.getTripAttributes(
                    (int) table.getValueAt(row,tripStructureDefinition.originMgraColumn),
                    (int) table.getValueAt(row,tripStructureDefinition.destMgraColumn),
                    (int) table.getValueAt(row,tripStructureDefinition.modeColumn),
                    (int) table.getValueAt(row,tripStructureDefinition.boardTapColumn),
                    (int) table.getValueAt(row,tripStructureDefinition.alightTapColumn),
                    (int) table.getValueAt(row,tripStructureDefinition.todColumn),
                    inbound,
                    (int) table.getValueAt(row,tripStructureDefinition.setColumn));
            tripTime[i] = attributes.getTripTime();
            tripDistance[i] = attributes.getTripDistance();
            tripCost[i] = attributes.getTripCost();
            if (hasPurposeColumn) {
                tripPurpose[i] = table.getStringValueAt(row,tripStructureDefinition.destinationPurposeColumn);
            } else {
                if (!inbound) //going out
                    tripPurpose[i] = tripStructureDefinition.destinationName;
                else
                    tripPurpose[i] = tripStructureDefinition.homeName;
            }
            tripMode[i] = "";
            tripId[i] = i;
            tripDepartTime[i] = attributes.getTripStartTime();
            tripBoardTaz[i] = attributes.getTripBoardTaz();
            tripAlightTaz[i] = attributes.getTripAlightTaz();
            originTaz[i] = attributes.getTripOriginTaz();
            destinationTaz[i] = attributes.getTripDestinationTaz();
        }
        table.appendColumn(tripTime,"TRIP_TIME");
        table.appendColumn(tripDistance,"TRIP_DISTANCE");
        table.appendColumn(tripCost,"TRIP_COST");
        table.appendColumn(tripPurpose,"TRIP_PURPOSE_NAME");
        table.appendColumn(tripMode,"TRIP_MODE_NAME");
        table.appendColumn(tripId,"RECID");
        table.appendColumn(tripBoardTaz,"TRIP_BOARD_TAZ");
        table.appendColumn(tripAlightTaz,"TRIP_ALIGHT_TAZ");
        table.appendColumn(originTaz,"ORIG_TAZ");
        table.appendColumn(destinationTaz,"DEST_TAZ");
        //augmentMasterTableWithTrips(table,tripStructureDefinition.tripType,tripDepartTime,tripStructureDefinition,tripTableWriter);
    }

    private final AtomicInteger masterTripRecordCounter = new AtomicInteger(0);
    private void augmentMasterTableWithTrips(TableDataSet table, String tripType, int[] tripDepartTime, TripStructureDefinition tripStructureDefinition, PrintWriter tripTableWriter) {

        for (int i = 0; i < tripDepartTime.length; i++) {
            int row = i+1;
            //id triptype recid partysize orig_mgra dest_mgra trip_board_tap trip_alight_tap trip_depart_time trip_time trip_distance trip_cost trip_purpose_name trip_mode_name
            StringBuilder line = new StringBuilder();
            line.append(masterTripRecordCounter.incrementAndGet());
            line.append(",").append(tripType);
            line.append(",").append(getData(table,row,tripStructureDefinition.recIdColumn,FieldType.INT));
            line.append(",").append(tripStructureDefinition.partySizeColumn < 0 ? 1 : getData(table,row,tripStructureDefinition.partySizeColumn,FieldType.INT));
            line.append(",").append(getData(table,row,tripStructureDefinition.originMgraColumn,FieldType.INT));
            line.append(",").append(getData(table,row,tripStructureDefinition.destMgraColumn,FieldType.INT));
            
            line.append(",").append(getData(table,row,table.getColumnPosition("ORIG_TAZ"),FieldType.INT));
            line.append(",").append(getData(table,row,table.getColumnPosition("DEST_TAZ"),FieldType.INT));
            
            line.append(",").append(getData(table,row,tripStructureDefinition.boardTapColumn,FieldType.INT));
            line.append(",").append(getData(table,row,tripStructureDefinition.alightTapColumn,FieldType.INT));
            line.append(",").append(getData(table,row,tripStructureDefinition.boardTazColumn,FieldType.INT));
            line.append(",").append(getData(table,row,tripStructureDefinition.alightTazColumn,FieldType.INT));
            line.append(",").append(tripDepartTime[i]);
            line.append(",").append(getData(table,row,tripStructureDefinition.tripTimeColumn,FieldType.FLOAT));
            line.append(",").append(getData(table,row,tripStructureDefinition.tripDistanceColumn,FieldType.FLOAT));
            line.append(",").append(getData(table,row,tripStructureDefinition.tripCostColumn,FieldType.FLOAT));
            line.append(",").append(getData(table,row,tripStructureDefinition.tripPurposeNameColumn,FieldType.STRING));
            line.append(",").append(getData(table,row,tripStructureDefinition.tripModeNameColumn,FieldType.STRING));
            if(tripTableWriter != null && line != null)
            	tripTableWriter.println(line.toString());
            else
            	throw new RuntimeException("Trip table or line is NULL");
            	
        }
    }






    private void exportAccessibilities(String outputFileBase) {
        addTable(outputFileBase);
        Set<String> intColumns = new HashSet<String>(Arrays.asList("mgra"));
        Set<String> floatColumns = new HashSet<String>();
        Set<String> stringColumns = new HashSet<String>();           
        Set<String> bitColumns = new HashSet<String>();
        Set<String> primaryKey = new LinkedHashSet<String>(Arrays.asList("mgra"));
        exportDataGeneric(outputFileBase,"acc.output.file",false,null,floatColumns,stringColumns,intColumns,bitColumns,FieldType.FLOAT,primaryKey,null);
    }

    private void exportMazData(String outputFileBase) {
        addTable(outputFileBase);
        Set<String> intColumns = new HashSet<String>(Arrays.asList("mgra","TAZ","ZIP09"));
        Set<String> floatColumns = new HashSet<String>();
        Set<String> stringColumns = new HashSet<String>();                  
                Set<String> bitColumns = new HashSet<String>();
        Set<String> primaryKey = new LinkedHashSet<String>(Arrays.asList("mgra"));
        exportDataGeneric(outputFileBase,"mgra.socec.file",false,null,floatColumns,stringColumns,intColumns,bitColumns,FieldType.FLOAT,primaryKey,null);
    }

    private void nullifyFile(String file) {
        String tempFile = file + ".temp";
        File f = new File(file);
        if (!f.renameTo(new File(tempFile)))
            throw new RuntimeException("Couldn't rename to file: " + f);
        BufferedReader reader = null;
        PrintWriter writer = null;
        try {
            reader = new BufferedReader(new FileReader(tempFile));
            writer = new PrintWriter(file);
            String line;
            while ((line = reader.readLine()) != null)
                writer.println(line.replace(NULL_VALUE,""));
        } catch (IOException e) {
            throw new RuntimeException(e);
        } finally {
            if (reader != null) {
                try{
                    reader.close();
                } catch (IOException e) {
                    //ignore
                }
            }
            if (writer != null)
                    writer.close();
        }
        new File(tempFile).delete();
    }

    public static int NULL_INT_VALUE = -98765;
    public static float NULL_FLOAT_VALUE = NULL_INT_VALUE;
    public static String NULL_VALUE = "" + NULL_FLOAT_VALUE;
    private void exportTapData(String outputFileBase) {
        addTable(outputFileBase);
        Map<String,float[]> ptype = readSpaceDelimitedData(properties.getProperty("generic.path") + "/" + properties.getProperty("tap.ptype.file"),Arrays.asList("TAP","LOTID","PTYPE","TAZ","CAPACITY","DISTANCE"));
        //Map<String,float[]> pelev = readSpaceDelimitedData(getPath("tap.ptype.file").replace("ptype","elev"),Arrays.asList("TAP","ELEV"));
        //float[] taps = ptype.get("TAP");
        //float[] etaps = pelev.get("TAP");
        //ptype.put("ELEV",getPartialData(taps,etaps,pelev.get("ELEV")));

        TableDataSet finalData = new TableDataSet();
        for (String columnName : ptype.keySet())
            finalData.appendColumn(ptype.get(columnName),columnName);

        Set<String> intColumns = new HashSet<String>();
        Set<String> floatColumns = new HashSet<String>();
        Set<String> stringColumns = new HashSet<String>();           
                Set<String> bitColumns = new HashSet<String>();
        Set<String> primaryKey = new LinkedHashSet<String>(Arrays.asList("TAP"));
        exportDataGeneric(finalData,outputFileBase,floatColumns,stringColumns,intColumns,bitColumns,FieldType.INT,primaryKey,null);
        nullifyFile(getOutputPath(outputFileBase + ".csv"));
    }

    private void exportMgraToTapData(String outputFileBase) {
        addTable(outputFileBase);
        Map<String,float[]> mgraToTap = readSpaceDelimitedData(properties.getProperty("generic.path") + "/" + properties.getProperty("mgra.wlkacc.taps.and.distance.file"),Arrays.asList("MGRA","TAP","DISTANCE"));
        TableDataSet finalData = new TableDataSet();
        for (String columnName : mgraToTap.keySet())
            finalData.appendColumn(mgraToTap.get(columnName),columnName);

        Set<String> intColumns = new HashSet<String>();
        Set<String> floatColumns = new HashSet<String>();
        Set<String> stringColumns = new HashSet<String>();              
        Set<String> bitColumns = new HashSet<String>();
        Set<String> primaryKey = new LinkedHashSet<String>(Arrays.asList("MGRA","TAP"));
        exportDataGeneric(finalData,outputFileBase,floatColumns,stringColumns,intColumns,bitColumns,FieldType.INT,primaryKey,null);
        nullifyFile(getOutputPath(outputFileBase + ".csv"));
    }

    private void exportMgraToMgraData(String outputFileBase) {
        addTable(outputFileBase);
        Map<String,float[]> mgraToMgra = readSpaceDelimitedData(properties.getProperty("generic.path") + "/" + properties.getProperty("mgra.walkdistance.file"),Arrays.asList("ORIG_MGRA","DEST_MGRA","DISTANCE"));

        Map<String,List<Number>> actualData = new LinkedHashMap<String,List<Number>>();
        for (String column : Arrays.asList("ORIG_MGRA","DEST_MGRA","DISTANCE"))
            actualData.put(column,new LinkedList<Number>());
        float[] dcolumn  = mgraToMgra.get("DISTANCE");
        float[] origColumn  = mgraToMgra.get("ORIG_MGRA");
        float[] destColumn  = mgraToMgra.get("DEST_MGRA");
        for (int i = 0; i < dcolumn.length; i++) {
        	actualData.get("ORIG_MGRA").add((int) origColumn[i]);
            actualData.get("DEST_MGRA").add((int) destColumn[i]);
            actualData.get("DISTANCE").add(dcolumn[i]);
        }



        TableDataSet finalData = new TableDataSet();
        for (String columnName : actualData.keySet()) {
            Object data;
            if (columnName.equals("DISTANCE")) {
                float[] dd = new float[actualData.get(columnName).size()];
                int counter = 0;
                for (Number n : actualData.get(columnName))
                    dd[counter++] = n.floatValue();
                data = dd;
            } else {
                int[] dd = new int[actualData.get(columnName).size()];
                int counter = 0;
                for (Number n : actualData.get(columnName))
                    dd[counter++] = n.intValue();
                data = dd;
            }
            finalData.appendColumn(data,columnName);
        }

        Set<String> intColumns = new HashSet<String>(Arrays.asList("TAZ","ORIG_MGRA","DEST_MGRA"));
        Set<String> floatColumns = new HashSet<String>(Arrays.asList("DISTANCE"));
        Set<String> stringColumns = new HashSet<String>();               
        Set<String> bitColumns = new HashSet<String>();
        Set<String> primaryKey = new LinkedHashSet<String>(Arrays.asList("ORIG_MGRA","DEST_MGRA"));
        exportDataGeneric(finalData,outputFileBase,floatColumns,stringColumns,intColumns,bitColumns,FieldType.INT,primaryKey,null);
        nullifyFile(getOutputPath(outputFileBase + ".csv"));
    }

    private void exportTazToTapData(String outputFileBase) {
        addTable(outputFileBase);
        Map<String,float[]> tazToTap = readSpaceDelimitedData(properties.getProperty("generic.path") + "/" + properties.getProperty("taz.driveaccess.taps.file"),Arrays.asList("A","B","C"));

        Map<String,List<Number>> actualData = new LinkedHashMap<String,List<Number>>();
        for (String column : Arrays.asList("TAZ","TAP","TIME","DISTANCE"))
            actualData.put(column,new LinkedList<Number>());
        float[] nullOrDistance  = tazToTap.get("C");
        float[] origTazOrDestTap  = tazToTap.get("A");
        float[] countOrTime  = tazToTap.get("B");
        for (int i = 0; i < nullOrDistance.length; i++) {
            int count = 0;
            if (nullOrDistance[i] < 0)
                count = (int) countOrTime[i];
            int taz = (int) origTazOrDestTap[i];
            while (count-- > 0) {
                i++;
                actualData.get("TAZ").add(taz);
                actualData.get("TAP").add((int) origTazOrDestTap[i]);
                actualData.get("TIME").add(countOrTime[i]);
                actualData.get("DISTANCE").add(nullOrDistance[i]);
            }
        }


        TableDataSet finalData = new TableDataSet();
        for (String columnName : actualData.keySet()) {
            Object data;
            if (columnName.equals("DISTANCE") || columnName.equals("TIME")) {
                float[] dd = new float[actualData.get(columnName).size()];
                int counter = 0;
                for (Number n : actualData.get(columnName))
                    dd[counter++] = n.floatValue();
                data = dd;
            } else {
                int[] dd = new int[actualData.get(columnName).size()];
                int counter = 0;
                for (Number n : actualData.get(columnName))
                    dd[counter++] = n.intValue();
                data = dd;
            }
            finalData.appendColumn(data,columnName);
        }

        Set<String> intColumns = new HashSet<String>(Arrays.asList("TAZ","TAP"));
        Set<String> floatColumns = new HashSet<String>(Arrays.asList("TIME","DISTANCE"));
        Set<String> stringColumns = new HashSet<String>();
        Set<String> bitColumns = new HashSet<String>();
        Set<String> primaryKey = new LinkedHashSet<String>(Arrays.asList("TAZ","TAP"));
        exportDataGeneric(finalData,outputFileBase,floatColumns,stringColumns,intColumns,bitColumns,FieldType.INT,primaryKey,null);
        nullifyFile(getOutputPath(outputFileBase + ".csv"));
    }




    private float[] toFloatArray(int[] data) {
        float[] f = new float[data.length];
        for (int i = 0; i < f.length; i++)
            f[i] = data[i];
        return f;
    }

    private float[] getPartialData(float[] fullKey, float[] partialKey, float[] partialData) {
        float[] data = new float[fullKey.length];
        Arrays.fill(data,NULL_FLOAT_VALUE);
        int counter = 0;
        for (float key : fullKey) {
            for (int i = 0; i < partialKey.length; i++) {
                if (partialKey[i] == key) {
                    data[counter] = partialData[i];
                }
            }
            counter++;
        }
        return data;
    }

    private void exportTazData(String outputFileBase) {
        addTable(outputFileBase);
        int[] tazs = getTazList();
        TableDataSet data = new TableDataSet();
        data.appendColumn(tazs,"TAZ");
        Map<String,float[]> term = readSpaceDelimitedData(properties.getProperty("generic.path") + "/" + properties.getProperty("taz.terminal.time.file"),Arrays.asList("TAZ","TERM"));
        //Map<String,float[]> park = readSpaceDelimitedData(getPath("taz.parkingtype.file"),Arrays.asList("TAZ","PARK"));
        data.appendColumn(getPartialData(toFloatArray(tazs),term.get("TAZ"),term.get("TERM")),"TERM");
        //data.appendColumn(getPartialData(toFloatArray(tazs),park.get("TAZ"),park.get("PARK")),"PARK");

        Set<String> intColumns = new HashSet<String>();
        Set<String> floatColumns = new HashSet<String>();
        Set<String> stringColumns = new HashSet<String>();                
        Set<String> bitColumns = new HashSet<String>();
        Set<String> primaryKey = new LinkedHashSet<String>(Arrays.asList("TAZ"));
        exportDataGeneric(data,outputFileBase,floatColumns,stringColumns,intColumns,bitColumns,FieldType.INT,primaryKey,null);
        nullifyFile(getOutputPath(outputFileBase + ".csv"));
    }

    private int[] getTazList() {
        Set<Integer> tazs = new TreeSet<Integer>();
        TableDataSet mgraData;
        try {
            mgraData = new CSVFileReader().readFile(new File(getPath("mgra.socec.file")));
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        boolean first = true;
        for (int taz : mgraData.getColumnAsInt("taz")) {
            if (first) {
                first = false;
                continue;
            }
            tazs.add(taz);
        }
        int[] finalTazs = new int[tazs.size()];
        int counter = 0;
        for (int taz : tazs)
            finalTazs[counter++] = taz;
        return finalTazs;
    }

    private Map<String,float[]> readSpaceDelimitedData(String location, List<String> columnNames) {
        Map<String,List<Integer>> data = new LinkedHashMap<String,List<Integer>>();
        for (String columnName : columnNames)
            data.put(columnName,new LinkedList<Integer>());
        BufferedReader reader = null;
        try {
            reader = new BufferedReader(new FileReader(location));
            String line;
            while ((line = reader.readLine()) != null) {
            	if(!line.equals(""))//Skip over blank lines
            	{
	                String[] d = line.trim().split("\\s+");
	                if(d.length > 0)//And check again to be sure
	                {
		                int counter = 0;
		                for (String columnName : columnNames) {
		                    if (counter < d.length) {
		                        data.get(columnName).add(Integer.parseInt(d[counter++]));
		                    } else {
		                        data.get(columnName).add(NULL_INT_VALUE); //if missing entry/entries, then put in null value
		                    }
		                }
	                }
            	}
            }
        } catch (IOException e) {
            throw new RuntimeException(e);
        } finally {
            if (reader != null) {
                try{
                    reader.close();
                } catch (IOException e) {
                    //ignore
                }
            }
        }
        Map<String,float[]> d = new LinkedHashMap<String,float[]>();
        for (String columnName : columnNames) {
            float[] f = new float[data.get(columnName).size()];
            int counter = 0;
            for (Integer i : data.get(columnName))
                f[counter++] = i;
            d.put(columnName,f);
        }
        return d;
    }

    private void exportHouseholdData(String outputFileBase) {
        addTable(outputFileBase);
        String[] formats = {NUMBER_FORMAT_NAME, //hh_id
                            NUMBER_FORMAT_NAME, //home_mgra
                            NUMBER_FORMAT_NAME, //income
                            NUMBER_FORMAT_NAME, //autos
                            NUMBER_FORMAT_NAME, //transponder
                            STRING_FORMAT_NAME, //cdap_pattern
                            NUMBER_FORMAT_NAME, //jtf_choice
                            };
        Set<String> intColumns = new HashSet<String>();
        Set<String> floatColumns = new HashSet<String>();
        Set<String> stringColumns = new HashSet<String>(Arrays.asList("cdap_pattern"));             
        Set<String> bitColumns = new HashSet<String>();
        Set<String> primaryKey = new LinkedHashSet<String>(Arrays.asList("hh_id"));
        exportDataGeneric(outputFileBase,"Results.HouseholdDataFile",true,formats,floatColumns,stringColumns,intColumns,bitColumns,FieldType.INT,primaryKey,null);
    }

    private void exportPersonData(String outputFileBase) {
        addTable(outputFileBase);
        String[] formats = {NUMBER_FORMAT_NAME, // hh_id
                            NUMBER_FORMAT_NAME, // person_id
                            NUMBER_FORMAT_NAME, // person_num
                            NUMBER_FORMAT_NAME, // age
                            STRING_FORMAT_NAME, // gender
                            STRING_FORMAT_NAME, // type
                            NUMBER_FORMAT_NAME, // value_of_time  (float)
                            STRING_FORMAT_NAME, // activity_pattern
                            NUMBER_FORMAT_NAME, // imf_choice
                            NUMBER_FORMAT_NAME, // inmf_choice
                            NUMBER_FORMAT_NAME, // fp_choice
                            NUMBER_FORMAT_NAME, // reimb_pct (float)
                            NUMBER_FORMAT_NAME, // ie_choice
                            };
        Set<String> intColumns = new HashSet<String>();
        Set<String> floatColumns = new HashSet<String>(Arrays.asList("value_of_time","reimb_pct"));
        Set<String> stringColumns = new HashSet<String>(Arrays.asList("gender","type","activity_pattern"));           
        Set<String> bitColumns = new HashSet<String>();
        Set<String> primaryKey = new LinkedHashSet<String>(Arrays.asList("person_id"));
        exportDataGeneric(outputFileBase,"Results.PersonDataFile",true,formats,floatColumns,stringColumns,intColumns,bitColumns,FieldType.INT,primaryKey,null);
    }

    private void exportSyntheticHouseholdData(String outputFileBase) {
        addTable(outputFileBase);
        String[] formats = {
        		NUMBER_FORMAT_NAME, // hh_id
                NUMBER_FORMAT_NAME, // household_serial_no
                NUMBER_FORMAT_NAME, // taz
                NUMBER_FORMAT_NAME, // mgra
                NUMBER_FORMAT_NAME, // hinccat1
                NUMBER_FORMAT_NAME, // hinc
                NUMBER_FORMAT_NAME, // hworker
                NUMBER_FORMAT_NAME, // veh
                NUMBER_FORMAT_NAME, // persons
                NUMBER_FORMAT_NAME, // hht
                NUMBER_FORMAT_NAME, // bldgsz
                NUMBER_FORMAT_NAME, // unittype
                };
        Set<String> intColumns = new HashSet<String>();
        Set<String> floatColumns = new HashSet<String>();
        Set<String> stringColumns = new HashSet<String>(Arrays.asList("household_serial_no"));                           
        Set<String> bitColumns = new HashSet<String>();
        Set<String> primaryKey = new LinkedHashSet<String>(Arrays.asList("HHID"));
        exportDataGeneric(outputFileBase,"PopulationSynthesizer.InputToCTRAMP.HouseholdFile",false,formats,floatColumns,stringColumns,intColumns,bitColumns,FieldType.INT,primaryKey,null);
    }

    private void exportSyntheticPersonData(String outputFileBase) {
        addTable(outputFileBase);
        String[] formats = {NUMBER_FORMAT_NAME, //HHID
                            NUMBER_FORMAT_NAME, //PERID
                            NUMBER_FORMAT_NAME, // household_serial_no
                            NUMBER_FORMAT_NAME, // PNUM
                            NUMBER_FORMAT_NAME, // AGE
                            NUMBER_FORMAT_NAME, // SEX
                            NUMBER_FORMAT_NAME, // MILTARY
                            NUMBER_FORMAT_NAME, // PEMPLOY
                            NUMBER_FORMAT_NAME, // PSTUDENT
                            NUMBER_FORMAT_NAME, // PTYPE
                            NUMBER_FORMAT_NAME, // EDUC
                            NUMBER_FORMAT_NAME, // GRADE
                            NUMBER_FORMAT_NAME, // OCCCEN1
                            NUMBER_FORMAT_NAME, // INDCEN
                            NUMBER_FORMAT_NAME, // WKW
                            NUMBER_FORMAT_NAME, // HOURS
                            };
        Set<String> intColumns = new HashSet<String>();
        Set<String> floatColumns = new HashSet<String>();
        Set<String> stringColumns = new HashSet<String>(Arrays.asList("household_serial_no"));                
        Set<String> bitColumns = new HashSet<String>();
        Set<String> primaryKey = new LinkedHashSet<String>(Arrays.asList("PERID"));
        exportDataGeneric(outputFileBase,"PopulationSynthesizer.InputToCTRAMP.PersonFile",false,formats,floatColumns,stringColumns,intColumns,bitColumns,FieldType.INT,primaryKey,null);
    }

    private void exportWorkSchoolLocation(String outputFileBase) {
        addTable(outputFileBase);
        Set<String> intColumns = new HashSet<String>();
        Set<String> floatColumns = new HashSet<String>(Arrays.asList("WorkLocationDistance","WorkLocationLogsum","SchoolLocation","SchoolLocationDistance","SchoolLocationLogsum"));
        Set<String> stringColumns = new HashSet<String>();
        Set<String> bitColumns = new HashSet<String>();
        Set<String> primaryKey = new LinkedHashSet<String>(Arrays.asList("PERSON_ID"));
        Map<String,String> overridingNames = new HashMap<String,String>();
        overridingNames.put("PersonID","PERSON_ID");
        exportDataGeneric(outputFileBase,"Results.UsualWorkAndSchoolLocationChoice",true,null,floatColumns,stringColumns,intColumns,bitColumns,FieldType.INT,primaryKey,overridingNames,null);
    }

    private void exportIndivToursData(String outputFileBase) {
        addTable(outputFileBase);
        String[] formats = {NUMBER_FORMAT_NAME, // hh_id
                            NUMBER_FORMAT_NAME, // person_id
                            NUMBER_FORMAT_NAME, // person_num
                            NUMBER_FORMAT_NAME, // person_type
                            NUMBER_FORMAT_NAME, // tour_id
                            STRING_FORMAT_NAME, // tour_category
                            STRING_FORMAT_NAME, // tour_purpose
                            NUMBER_FORMAT_NAME, // orig_mgra
                            NUMBER_FORMAT_NAME, // dest_mgra
                            NUMBER_FORMAT_NAME, // start_period
                            NUMBER_FORMAT_NAME, // end_period
                            NUMBER_FORMAT_NAME, // tour_mode
                            NUMBER_FORMAT_NAME, // tour_distance
                            NUMBER_FORMAT_NAME, // tour_time
                            NUMBER_FORMAT_NAME, // atWork_freq
                            NUMBER_FORMAT_NAME, // num_ob_stops
                            NUMBER_FORMAT_NAME, // num_ib_stops
                            NUMBER_FORMAT_NAME, // util_1
                            NUMBER_FORMAT_NAME, // util_2
                            NUMBER_FORMAT_NAME, // util_3
                            NUMBER_FORMAT_NAME, // util_4
                            NUMBER_FORMAT_NAME, // util_5
                            NUMBER_FORMAT_NAME, // util_6
                            NUMBER_FORMAT_NAME, // util_7
                            NUMBER_FORMAT_NAME, // util_8
                            NUMBER_FORMAT_NAME, // util_9
                            NUMBER_FORMAT_NAME, // util_10
                            NUMBER_FORMAT_NAME, // util_11
                            NUMBER_FORMAT_NAME, // util_12
                            NUMBER_FORMAT_NAME, // util_13
                            NUMBER_FORMAT_NAME, // util_14
                            NUMBER_FORMAT_NAME, // util_15
                            NUMBER_FORMAT_NAME, // util_16
                            NUMBER_FORMAT_NAME, // util_17
                            NUMBER_FORMAT_NAME, // util_18
                            NUMBER_FORMAT_NAME, // util_19
                            NUMBER_FORMAT_NAME, // util_20
                            NUMBER_FORMAT_NAME, // util_21
                            NUMBER_FORMAT_NAME, // util_22
                            NUMBER_FORMAT_NAME, // util_23
                            NUMBER_FORMAT_NAME, // util_24
                            NUMBER_FORMAT_NAME, // util_25
                            NUMBER_FORMAT_NAME, // util_26
                            NUMBER_FORMAT_NAME, // prob_1
                            NUMBER_FORMAT_NAME, // prob_2
                            NUMBER_FORMAT_NAME, // prob_3
                            NUMBER_FORMAT_NAME, // prob_4
                            NUMBER_FORMAT_NAME, // prob_5
                            NUMBER_FORMAT_NAME, // prob_6
                            NUMBER_FORMAT_NAME, // prob_7
                            NUMBER_FORMAT_NAME, // prob_8
                            NUMBER_FORMAT_NAME, // prob_9
                            NUMBER_FORMAT_NAME, // prob_10
                            NUMBER_FORMAT_NAME, // prob_11
                            NUMBER_FORMAT_NAME, // prob_12
                            NUMBER_FORMAT_NAME, // prob_13
                            NUMBER_FORMAT_NAME, // prob_14
                            NUMBER_FORMAT_NAME, // prob_15
                            NUMBER_FORMAT_NAME, // prob_16
                            NUMBER_FORMAT_NAME, // prob_17
                            NUMBER_FORMAT_NAME, // prob_18
                            NUMBER_FORMAT_NAME, // prob_19
                            NUMBER_FORMAT_NAME, // prob_20
                            NUMBER_FORMAT_NAME, // prob_21
                            NUMBER_FORMAT_NAME, // prob_22
                            NUMBER_FORMAT_NAME, // prob_23
                            NUMBER_FORMAT_NAME, // prob_24
                            NUMBER_FORMAT_NAME, // prob_25
                            NUMBER_FORMAT_NAME // prob_26
                        };
        Set<String> intColumns = new HashSet<String>(Arrays.asList("hh_id","person_id","person_num","person_type","tour_id","orig_mgra","dest_mgra","start_period","end_period","tour_mode","atWork_freq","num_ob_stops","num_ib_stops"));
        Set<String> floatColumns = new HashSet<String>();
        Set<String> stringColumns = new HashSet<String>(Arrays.asList("tour_category","tour_purpose"));                      
        Set<String> bitColumns = new HashSet<String>();
        Set<String> primaryKey = new LinkedHashSet<String>(Arrays.asList("hh_id","person_id","tour_category","tour_id","tour_purpose"));
        exportDataGeneric(outputFileBase,"Results.IndivTourDataFile",true,formats,floatColumns,stringColumns,intColumns,bitColumns,FieldType.FLOAT,primaryKey,null);
    }

    private void exportJointToursData(String outputFileBase) {
        addTable(outputFileBase);
        String[] formats = {NUMBER_FORMAT_NAME, // hh_id
                            NUMBER_FORMAT_NAME, // tour_id
                            STRING_FORMAT_NAME, // tour_category
                            STRING_FORMAT_NAME, // tour_purpose
                            NUMBER_FORMAT_NAME, // tour_composition
                            STRING_FORMAT_NAME, // tour_participants
                            NUMBER_FORMAT_NAME, // orig_mgra
                            NUMBER_FORMAT_NAME, // dest_mgra
                            NUMBER_FORMAT_NAME, // start_period
                            NUMBER_FORMAT_NAME, // end_period
                            NUMBER_FORMAT_NAME, // tour_mode
                            NUMBER_FORMAT_NAME, // tour_distance
                            NUMBER_FORMAT_NAME, // tour_time
                            NUMBER_FORMAT_NAME, // num_ob_stops
                            NUMBER_FORMAT_NAME, // num_ib_stops
                            NUMBER_FORMAT_NAME, // util_1
                            NUMBER_FORMAT_NAME, // util_2
                            NUMBER_FORMAT_NAME, // util_3
                            NUMBER_FORMAT_NAME, // util_4
                            NUMBER_FORMAT_NAME, // util_5
                            NUMBER_FORMAT_NAME, // util_6
                            NUMBER_FORMAT_NAME, // util_7
                            NUMBER_FORMAT_NAME, // util_8
                            NUMBER_FORMAT_NAME, // util_9
                            NUMBER_FORMAT_NAME, // util_10
                            NUMBER_FORMAT_NAME, // util_11
                            NUMBER_FORMAT_NAME, // util_12
                            NUMBER_FORMAT_NAME, // util_13
                            NUMBER_FORMAT_NAME, // util_14
                            NUMBER_FORMAT_NAME, // util_15
                            NUMBER_FORMAT_NAME, // util_16
                            NUMBER_FORMAT_NAME, // util_17
                            NUMBER_FORMAT_NAME, // util_18
                            NUMBER_FORMAT_NAME, // util_19
                            NUMBER_FORMAT_NAME, // util_20
                            NUMBER_FORMAT_NAME, // util_21
                            NUMBER_FORMAT_NAME, // util_22
                            NUMBER_FORMAT_NAME, // util_23
                            NUMBER_FORMAT_NAME, // util_24
                            NUMBER_FORMAT_NAME, // util_25
                            NUMBER_FORMAT_NAME, // util_26
                            NUMBER_FORMAT_NAME, // prob_1
                            NUMBER_FORMAT_NAME, // prob_2
                            NUMBER_FORMAT_NAME, // prob_3
                            NUMBER_FORMAT_NAME, // prob_4
                            NUMBER_FORMAT_NAME, // prob_5
                            NUMBER_FORMAT_NAME, // prob_6
                            NUMBER_FORMAT_NAME, // prob_7
                            NUMBER_FORMAT_NAME, // prob_8
                            NUMBER_FORMAT_NAME, // prob_9
                            NUMBER_FORMAT_NAME, // prob_10
                            NUMBER_FORMAT_NAME, // prob_11
                            NUMBER_FORMAT_NAME, // prob_12
                            NUMBER_FORMAT_NAME, // prob_13
                            NUMBER_FORMAT_NAME, // prob_14
                            NUMBER_FORMAT_NAME, // prob_15
                            NUMBER_FORMAT_NAME, // prob_16
                            NUMBER_FORMAT_NAME, // prob_17
                            NUMBER_FORMAT_NAME, // prob_18
                            NUMBER_FORMAT_NAME, // prob_19
                            NUMBER_FORMAT_NAME, // prob_20
                            NUMBER_FORMAT_NAME, // prob_21
                            NUMBER_FORMAT_NAME, // prob_22
                            NUMBER_FORMAT_NAME, // prob_23
                            NUMBER_FORMAT_NAME, // prob_24
                            NUMBER_FORMAT_NAME, // prob_25
                            NUMBER_FORMAT_NAME // prob_26
                        };
        Set<String> intColumns = new HashSet<String>(Arrays.asList("hh_id","tour_id","tour_composition","orig_mgra","dest_mgra","start_period","end_period","tour_mode","num_ob_stops","num_ib_stops"));
        Set<String> floatColumns = new HashSet<String>();
        Set<String> stringColumns = new HashSet<String>(Arrays.asList("tour_category","tour_purpose","tour_participants"));                     
        Set<String> bitColumns = new HashSet<String>();
        Set<String> primaryKey = new LinkedHashSet<String>(Arrays.asList("hh_id","tour_category","tour_id","tour_purpose"));
        exportDataGeneric(outputFileBase,"Results.JointTourDataFile",true,formats,floatColumns,stringColumns,intColumns,bitColumns,FieldType.FLOAT,primaryKey,null);
    }

    private void exportIndivTripData(String outputFileBase) {
        addTable(outputFileBase);
        String[] formats = {NUMBER_FORMAT_NAME, // hh_id
                            NUMBER_FORMAT_NAME, // person_id
                            NUMBER_FORMAT_NAME, // person_num
                            NUMBER_FORMAT_NAME, // tour_id
                            NUMBER_FORMAT_NAME, // stop_id
                            NUMBER_FORMAT_NAME, // inbound
                            STRING_FORMAT_NAME, // tour_purpose
                            STRING_FORMAT_NAME, // orig_purpose
                            STRING_FORMAT_NAME, // dest_purpose
                            NUMBER_FORMAT_NAME, // orig_mgra
                            NUMBER_FORMAT_NAME, // dest_mgra
                            NUMBER_FORMAT_NAME, // parking_mgra
                            NUMBER_FORMAT_NAME, // stop_period
                            NUMBER_FORMAT_NAME, // trip_mode
                            NUMBER_FORMAT_NAME, // trip_board_tap
                            NUMBER_FORMAT_NAME, // trip_alight_tap
                            NUMBER_FORMAT_NAME, // tour_mode
                            NUMBER_FORMAT_NAME // set
                        };
        Set<String> intColumns = new HashSet<String>();
        Set<String> floatColumns = new HashSet<String>();
        Set<String> stringColumns = new HashSet<String>(Arrays.asList("tour_purpose","orig_purpose","dest_purpose"));              
        Set<String> bitColumns = new HashSet<String>();
        Set<String> primaryKey = new LinkedHashSet<String>(Arrays.asList("hh_id","person_id","tour_id","tour_purpose","inbound","stop_id"));
        exportDataGeneric(outputFileBase,"Results.IndivTripDataFile",true,formats,floatColumns,stringColumns,intColumns,bitColumns,FieldType.INT,primaryKey,new TripStructureDefinition(10,11,8,9,13,14,15,16,-1,17,"INDIV",6,18,false));
    }

    private void exportJointTripData(String outputFileBase) {
        addTable(outputFileBase);
        String[] formats = {NUMBER_FORMAT_NAME, // hh_id
                            NUMBER_FORMAT_NAME, // tour_id
                            NUMBER_FORMAT_NAME, // stop_id
                            NUMBER_FORMAT_NAME, // inbound
                            STRING_FORMAT_NAME, // tour_purpose
                            STRING_FORMAT_NAME, // orig_purpose
                            STRING_FORMAT_NAME, // dest_purpose
                            NUMBER_FORMAT_NAME, // orig_mgra
                            NUMBER_FORMAT_NAME, // dest_mgra
                            NUMBER_FORMAT_NAME, // parking_mgra
                            NUMBER_FORMAT_NAME, // stop_period
                            NUMBER_FORMAT_NAME, // trip_mode
                            NUMBER_FORMAT_NAME, // num_participants
                            NUMBER_FORMAT_NAME, // trip_board_tap
                            NUMBER_FORMAT_NAME, // trip_alight_tap
                            NUMBER_FORMAT_NAME, // tour_mode
                            NUMBER_FORMAT_NAME // set
                        };
        Set<String> intColumns = new HashSet<String>();
        Set<String> floatColumns = new HashSet<String>();
        Set<String> stringColumns = new HashSet<String>(Arrays.asList("tour_purpose","orig_purpose","dest_purpose"));             
        Set<String> bitColumns = new HashSet<String>();
        Set<String> primaryKey = new LinkedHashSet<String>(Arrays.asList("hh_id","tour_id","tour_purpose","inbound","stop_id"));
        exportDataGeneric(outputFileBase,"Results.JointTripDataFile",true,formats,floatColumns,stringColumns,intColumns,bitColumns,FieldType.INT,primaryKey, new TripStructureDefinition(8,9,6,7,11,12,14,15,13,16,"JOINT",4,17,false));
    }


    private Matrix getMatrixFromFile(String matrixPath,String core) {
        if (!matrixPath.endsWith(".mtx"))
            matrixPath += ".mtx";
        String path = getPath(matrixPath);
        DataEntry dataEntry = new DataEntry("matrix",path + "  " + core,"transcad",path,core,"",false);
        try {
            String serverAddress = (String) properties.get("RunModel.MatrixServerAddress");
            int serverPort = Integer.parseInt((String) properties.get("RunModel.MatrixServerPort"));
            MatrixDataServerIf server = new MatrixDataServerRmi(serverAddress,serverPort,MatrixDataServer.MATRIX_DATA_SERVER_NAME);
            return server.getMatrix(dataEntry);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }


    private Map<String,String> getVehicleSkimFileNameMapping() {
        Map<String,String> map = new LinkedHashMap<String,String>();
        map.put("impdat_" + TOD_TOKEN,"DRIVE_ALONE_TOLL");
        map.put("impdan_" + TOD_TOKEN,"DRIVE_ALONE_FREE");
        map.put("imps2th_" + TOD_TOKEN,"HOV2_TOLL");
        map.put("imps2nh_" + TOD_TOKEN,"HOV2_FREE");
        map.put("imps3th_" + TOD_TOKEN,"HOV3_TOLL");
        map.put("imps3nh_" + TOD_TOKEN,"HOV3_FREE");
        map.put("imphhdt_" + TOD_TOKEN,"TRUCK_HH_TOLL");
        map.put("imphhdn_" + TOD_TOKEN,"TRUCK_HH_FREE");
        map.put("impmhdt_" + TOD_TOKEN,"TRUCK_MH_TOLL");
        map.put("impmhdn_" + TOD_TOKEN,"TRUCK_MH_FREE");
        map.put("implhdt_" + TOD_TOKEN,"TRUCK_LH_TOLL");
        map.put("implhdn_" + TOD_TOKEN,"TRUCK_LH_FREE");
        return map;
    }
    
    private Map<String,String[]> getVehicleSkimFileCoreNameMapping() { //distance,time,cost
        Map<String,String[]> map = new LinkedHashMap<String,String[]>();
        map.put("impdat_" + TOD_TOKEN,new String[] {"Length (Skim)","*STM_" + TOD_TOKEN + " (Skim)","dat_" + TOD_TOKEN + " - itoll_" + TOD_TOKEN});
        map.put("impdan_" + TOD_TOKEN,new String[] {"Length (Skim)","*STM_" + TOD_TOKEN + " (Skim)"});
        map.put("imps2th_" + TOD_TOKEN,new String[] {"Length (Skim)","*HTM_" + TOD_TOKEN + " (Skim)","s2t_" + TOD_TOKEN + " - itoll_" + TOD_TOKEN});
        map.put("imps2nh_" + TOD_TOKEN,new String[] {"Length (Skim)","*HTM_" + TOD_TOKEN + " (Skim)"});
        map.put("imps3th_" + TOD_TOKEN,new String[] {"Length (Skim)","*HTM_" + TOD_TOKEN + " (Skim)","s3t_" + TOD_TOKEN + " - itoll_" + TOD_TOKEN});
        map.put("imps3nh_" + TOD_TOKEN,new String[] {"Length (Skim)","*HTM_" + TOD_TOKEN + " (Skim)"});
        map.put("imphhdt_" + TOD_TOKEN,new String[] {"Length (Skim)","*STM_" + TOD_TOKEN + " (Skim)","hhdt - ITOLL2_" + TOD_TOKEN});
        map.put("imphhdn_" + TOD_TOKEN,new String[] {"Length (Skim)","*STM_" + TOD_TOKEN + " (Skim)"});
        map.put("impmhdt_" + TOD_TOKEN,new String[] {"Length (Skim)","*STM_" + TOD_TOKEN + " (Skim)","mhdt - ITOLL2_" + TOD_TOKEN});
        map.put("impmhdn_" + TOD_TOKEN,new String[] {"Length (Skim)","*STM_" + TOD_TOKEN + " (Skim)"});
        map.put("implhdt_" + TOD_TOKEN,new String[] {"Length (Skim)","*STM_" + TOD_TOKEN + " (Skim)","lhdt - ITOLL2_" + TOD_TOKEN});
        map.put("implhdn_" + TOD_TOKEN,new String[] {"Length (Skim)","*STM_" + TOD_TOKEN + " (Skim)"});
        return map;
    }

    private void exportAutoSkims(String outputFileBase) {
        addTable(outputFileBase);
        String[] includedTimePeriods = getTimePeriodsForSkims(); //can't include them all
        Set<Integer> internalZones = new LinkedHashSet<Integer>();


        PrintWriter writer = null;
        List<String> costColumns = new LinkedList<String>();
        try {
            writer = new PrintWriter(getOutputPath(outputFileBase + ".csv"));


            Map<String,String> vehicleSkimFiles = getVehicleSkimFileNameMapping();
            Map<String,String[]> vehicleSkimCores = getVehicleSkimFileCoreNameMapping();
            Set<String> modeNames = new LinkedHashSet<String>();
            for (String n : vehicleSkimFiles.keySet())
                modeNames.add(vehicleSkimFiles.get(n));
            boolean first = true;
            for (String period : includedTimePeriods) {
                clearMatrixServer();
                Map<String,Matrix> lengthMatrix = new LinkedHashMap<String,Matrix>();
                Map<String,Matrix> timeMatrix = new LinkedHashMap<String,Matrix>();
                Map<String,Matrix> fareMatrix = new LinkedHashMap<String,Matrix>();

                for (String key : vehicleSkimCores.keySet()) {
                    String name = vehicleSkimFiles.get(key);
                    String[] cores = vehicleSkimCores.get(key);
                    String file = "output/" + key.replace(TOD_TOKEN,period);
                    lengthMatrix.put(name,getMatrixFromFile(file,cores[0].replace(TOD_TOKEN,period)));
                    timeMatrix.put(name,getMatrixFromFile(file,cores[1].replace(TOD_TOKEN,period)));
                    if (cores.length > 2)
                        fareMatrix.put(name,getMatrixFromFile(file,cores[2].replace(TOD_TOKEN,period)));
                    if (internalZones.size() == 0) {
                        boolean f = true;
                        for (int zone : lengthMatrix.get(name).getExternalColumnNumbers()) {
                            if (f) {
                                f = false;
                                continue;
                            }
                            internalZones.add(zone);
                        }
                    }
                }

                //put data into arrays for faster access
                Matrix[] orderedData = new Matrix[lengthMatrix.size()+timeMatrix.size()+fareMatrix.size()];
                int counter = 0;
                for (String mode : modeNames) {
                    orderedData[counter++] = lengthMatrix.get(mode);
                    orderedData[counter++] = timeMatrix.get(mode);
                    if (fareMatrix.containsKey(mode))
                        orderedData[counter++] = fareMatrix.get(mode);
                }

                StringBuilder sb = new StringBuilder();
                if (first) {
                    sb.append("ORIG_TAZ,DEST_TAZ,TOD");
                    for (String modeName : modeNames) {
                        sb.append(",DIST_").append(modeName);
                        sb.append(",TIME_").append(modeName);
                        costColumns.add("DIST_" + modeName);
                        costColumns.add("TIME_" + modeName);
                        if (fareMatrix.containsKey(modeName)) {
                            sb.append(",COST_").append(modeName);
                            costColumns.add("COST_" + modeName);
                        }
                    }
                    writer.println(sb.toString());
                    first = false;
                }

                for (int i : internalZones) {
                    for (int j : internalZones) {
                        sb = new StringBuilder();
                        sb.append(i).append(",").append(j).append(",").append(period);
                        for (Matrix matrix : orderedData)
                            sb.append(",").append(matrix.getValueAt(i,j));
                        writer.println(sb.toString());
                    }
                }
            }

        } catch (IOException e) {
            throw new RuntimeException(e);
        } finally {
            if (writer != null)
                writer.close();
        }

        writer = null;
        try {
            writer = new PrintWriter(getOutputPath(outputFileBase + ".sql"));
            String tableName = outputFileBase.toUpperCase();
            writer.println("CREATE TABLE " + tableName + " (");
            writer.println("    ORIG_TAZ int,");
            writer.println("    DEST_TAZ int,");
            writer.println("    TOD varchar(15),");
            for (String column : costColumns)
                writer.println("    " + column + " real,");
            writer.println("    CONSTRAINT " + tableName + "_PKEY PRIMARY KEY (ORIG_TAZ,DEST_TAZ,TOD)");
            writer.println(")");
            writer.println();
            writer.println("BULK INSERT " + tableName + " FROM \"" + new File(getOutputPath(outputFileBase + ".csv")).getAbsolutePath() + "\" WITH (");
            writer.println("    FIELDTERMINATOR=',', FIRSTROW=2, MAXERRORS=0, TABLOCK)");
            writer.println();
        } catch (IOException e) {
            throw new RuntimeException(e);
        } finally {
            if (writer != null)
                writer.close();
        }
    }

    private Map<String,String> getTransitSkimFileNameMapping() {
        Map<String,String> map = new LinkedHashMap<String,String>();
        map.put("implocl_" + TOD_TOKEN + "o","LOCAL_TRANSIT");
        map.put("impprem_" + TOD_TOKEN + "o","PREMIUM_TRANSIT");
        return map;
    }

    private String getTransitSkimFileFareCoreName() {
        return "Fare";
    }

    private Map<String,String[]> getTransitSkimFileTimeCoreNameMapping() { //distance,time,cost
        Map<String,String[]> map = new LinkedHashMap<String,String[]>();
        map.put("implocl_" + TOD_TOKEN + "o",new String[] {"Total IV Time","Initial Wait Time","Transfer Wait Time","Walk Time"});
        map.put("impprem_" + TOD_TOKEN + "o",new String[] {"IVT:CR","IVT:LR","IVT:BRT","IVT:EXP","IVT:LB","Initial Wait Time","Transfer Wait Time","Walk Time"});
        return map;
    }

    private String[] getTimePeriodsForSkims() {
        return new String[] {"AM","MD","PM"};
    }

    private void exportTransitSkims(String outputFileBase) {
        addTable(outputFileBase);
        String[] includedTimePeriods = getTimePeriodsForSkims(); //can't include them all
        Set<Integer> internalZones = new LinkedHashSet<Integer>();


        PrintWriter writer = null;
        List<String> costColumns = new LinkedList<String>();
        try {
            writer = new PrintWriter(getOutputPath(outputFileBase + ".csv"));


            Map<String,String> transitSkimFiles = getTransitSkimFileNameMapping();
            Map<String,String[]> transitSkimTimeCores = getTransitSkimFileTimeCoreNameMapping();
            String fareCore = getTransitSkimFileFareCoreName();
            Set<String> modeNames = new LinkedHashSet<String>();
            for (String n : transitSkimFiles.keySet())
                modeNames.add(transitSkimFiles.get(n));
            boolean first = true;
            for (String period : includedTimePeriods) {
                clearMatrixServer();
                Map<String,Matrix[]> timeMatrix = new LinkedHashMap<String,Matrix[]>();
                Map<String,Matrix> fareMatrix = new LinkedHashMap<String,Matrix>();

                for (String key : transitSkimFiles.keySet()) {
                    String name = transitSkimFiles.get(key);
                    String[] timeCores = transitSkimTimeCores.get(key);
                    String file = "output/" + key.replace(TOD_TOKEN,period);
                    Matrix[] timeMatrices = new Matrix[timeCores.length];
                    for (int i = 0; i < timeCores.length; i++)
                        timeMatrices[i] = getMatrixFromFile(file,timeCores[i].replace(TOD_TOKEN,period));
                    timeMatrix.put(name,timeMatrices);
                    fareMatrix.put(name,getMatrixFromFile(file,fareCore.replace(TOD_TOKEN,period)));
                    if (internalZones.size() == 0) {
                        boolean f = true;
                        for (int zone : fareMatrix.get(name).getExternalColumnNumbers()) {
                            if (f) {
                                f = false;
                                continue;
                            }
                            internalZones.add(zone);
                        }
                    }
                }

                //put data into arrays for faster access
                Matrix[][] orderedTimeData = new Matrix[timeMatrix.size()][];
                Matrix[] fareData = new Matrix[orderedTimeData.length];
                int counter = 0;
                for (String mode : modeNames) {
                    orderedTimeData[counter] = timeMatrix.get(mode);
                    fareData[counter++] = fareMatrix.get(mode);
                }

                StringBuilder sb = new StringBuilder();
                if (first) {
                    sb.append("ORIG_TAP,DEST_TAP,TOD");
                    for (String modeName : modeNames) {
                        sb.append(",TIME_").append(modeName);
                        costColumns.add("TIME_" + modeName);
                        sb.append(",FARE_").append(modeName);
                        costColumns.add("FARE_" + modeName);
                    }
                    writer.println(sb.toString());
                    first = false;
                }

                for (int i : internalZones) {
                    for (int j : internalZones) {
                        sb = new StringBuilder();
                        sb.append(i).append(",").append(j).append(",").append(period);
                        float runningTotal = 0.0f;
                        for (int m = 0; m < orderedTimeData.length; m++) {
                            float time = 0.0f;
                            for (Matrix tm : orderedTimeData[m])
                                time += tm.getValueAt(i,j);
                            float fare = fareData[m].getValueAt(i,j);
                            runningTotal += fare + time;
                            sb.append(",").append(time).append(",").append(fare);
                        }
                        if (runningTotal > 0.0f)
                            writer.println(sb.toString());
                    }
                }
            }

        } catch (IOException e) {
            throw new RuntimeException(e);
        } finally {
            if (writer != null)
                writer.close();
        }

        writer = null;
        try {
            writer = new PrintWriter(getOutputPath(outputFileBase + ".sql"));
            String tableName = outputFileBase.toUpperCase();
            writer.println("CREATE TABLE " + tableName + " (");
            writer.println("    ORIG_TAP int,");
            writer.println("    DEST_TAP int,");
            writer.println("    TOD varchar(15),");
            for (String column : costColumns)
                writer.println("    " + column + " real,");
            writer.println("    CONSTRAINT " + tableName + "_PKEY PRIMARY KEY (ORIG_TAP,DEST_TAP,TOD)");
            writer.println(")");
            writer.println();
            writer.println("BULK INSERT " + tableName + " FROM \"" + new File(getOutputPath(outputFileBase + ".csv")).getAbsolutePath() + "\" WITH (");
            writer.println("    FIELDTERMINATOR=',', FIRSTROW=2, MAXERRORS=0, TABLOCK)");
            writer.println();
        } catch (IOException e) {
            throw new RuntimeException(e);
        } finally {
            if (writer != null)
                writer.close();
        }
    }

    private void exportDefinitions(String outputFileBase) {
        addTable(outputFileBase);
        Map<String,String> tripPurposes = new LinkedHashMap<String,String>();
        Map<String,String> modes = new LinkedHashMap<String,String>();
        Map<String,String> ejCategories = new LinkedHashMap<String,String>();

        PrintWriter writer = null;
        try {
            writer = new PrintWriter(getOutputPath(outputFileBase + ".csv"));
            writer.println("type,code,description");
            writer.println("nothing,placeholder,this describes nothing");
            for (String tripPurpose : tripPurposes.keySet())
                writer.println("trip_purpose," + tripPurpose + "," + tripPurposes.get(tripPurpose));
            for (String mode : modes.keySet())
                writer.println("mode," + mode + "," + modes.get(mode));
            for (String ejCategory : ejCategories.keySet())
                writer.println("ej_category," + ejCategory + "," + ejCategories.get(ejCategory));
        } catch (IOException e) {
            throw new RuntimeException(e);
        } finally {
            if (writer != null)
                writer.close();
        }

        writer = null;
        try {
            writer = new PrintWriter(getOutputPath(outputFileBase + ".sql"));
            String tableName = outputFileBase.toUpperCase();
            writer.println("CREATE TABLE " + tableName + " (");
            writer.println("    TYPE varchar(50),");
            writer.println("    CODE varchar(50),");
            writer.println("    DESCRIPTION varchar(500),");
            writer.println("    CONSTRAINT " + tableName + "_PKEY PRIMARY KEY (TYPE,CODE)");
            writer.println(")");
            writer.println();
            writer.println("BULK INSERT " + tableName + " FROM \"" + new File(getOutputPath(outputFileBase + ".csv")).getAbsolutePath() + "\" WITH (");
            writer.println("    FIELDTERMINATOR=',', FIRSTROW=2, MAXERRORS=0, TABLOCK)");
            writer.println();
        } catch (IOException e) {
            throw new RuntimeException(e);
        } finally {
            if (writer != null)
                writer.close();
        }
    }

    private void exportPnrVehicleData(String outputFileBase) {
        addTable(outputFileBase);
        Set<String> intColumns = new HashSet<String>(Arrays.asList("TAP"));
        Set<String> floatColumns = new HashSet<String>();
        Set<String> stringColumns = new HashSet<String>();
                Set<String> bitColumns = new HashSet<String>();
        Set<String> primaryKey = new LinkedHashSet<String>(Arrays.asList("TAP"));
        exportDataGeneric(outputFileBase,"Results.PNRFile",false,null,floatColumns,stringColumns,intColumns,bitColumns,FieldType.FLOAT,primaryKey,null);
    }

    private void exportCbdVehicleData(String outputFileBase) {
        addTable(outputFileBase);
        Set<String> intColumns = new HashSet<String>(Arrays.asList("MGRA"));
        Set<String> floatColumns = new HashSet<String>();
        Set<String> stringColumns = new HashSet<String>();
                Set<String> bitColumns = new HashSet<String>();
        Set<String> primaryKey = new LinkedHashSet<String>(Arrays.asList("MGRA"));
        exportDataGeneric(outputFileBase,"Results.CBDFile",false,null,floatColumns,stringColumns,intColumns,bitColumns,FieldType.FLOAT,primaryKey,null);
    }
    
//    private void exportPecasCodes(String outputFileBase) {
//        addTable(outputFileBase);
//        String[] formats = {NUMBER_FORMAT_NAME, //occcen1
//                            NUMBER_FORMAT_NAME, //pecas_occ
//                            };
//        Set<String> intColumns = new HashSet<String>();
//        Set<String> floatColumns = new HashSet<String>();             
//        Set<String> bitColumns = new HashSet<String>();
//        Set<String> stringColumns = new HashSet<String>();
//        Set<String> primaryKey = new LinkedHashSet<String>(Arrays.asList("occcen1"));
//        exportDataGeneric(outputFileBase,"PopulationSynthesizer.OccupCodes",true,formats,floatColumns,stringColumns,intColumns,bitColumns,FieldType.INT,primaryKey,null);
//    }
    
    private void exportDistrictDefinitions(String outputFileBase) {
        addTable(outputFileBase);
        String[] formats = {NUMBER_FORMAT_NAME, //TAZ_REG
                            NUMBER_FORMAT_NAME, //COUNTY
                            NUMBER_FORMAT_NAME, //TAZ2010
                            NUMBER_FORMAT_NAME, //DISTRICT
                            };
        Set<String> intColumns = new HashSet<String>();
        Set<String> floatColumns = new HashSet<String>();             
        Set<String> bitColumns = new HashSet<String>();
        Set<String> stringColumns = new HashSet<String>();
        Set<String> primaryKey = new LinkedHashSet<String>(Arrays.asList("TAZ2010"));
        exportDataGeneric(outputFileBase,"District.Definitions",true,formats,floatColumns,stringColumns,intColumns,bitColumns,FieldType.INT,primaryKey,null);
    }


    private void buildFullSqlImportFile(String databaseSchema, boolean deleteFiles) {
        List<String> sqlTables = new LinkedList<String>(tables);
        sqlTables.add("node");
        sqlTables.add("link");
        sqlTables.add("route");
        sqlTables.add("routetap");
        sqlTables.add("transitflow");
        SqlImportFileBuilder sifb = new SqlImportFileBuilder();
        sifb.buildImportFile(outputPath,sqlTables,"sql_table_import.sql",databaseSchema,deleteFiles);
        //sifb.buildTripFile(outputPath,sqlTables,"trip_table.sql",databaseSchema); 
    }



    private static enum FieldType {
        INT,
        FLOAT,
        STRING,
        BIT
    }

    private class TripStructureDefinition {
        private final int recIdColumn;
        private final int partySizeColumn;
        private final int originMgraColumn;
        private final int destMgraColumn;
        private final int originPurposeColumn;
        private final int destinationPurposeColumn;
        private final int todColumn;
        private final int setColumn;
        private final int modeColumn;
        private final int boardTapColumn;
        private final int alightTapColumn;
        private final int tripTimeColumn;
        private final int tripDistanceColumn;
        private final int tripCostColumn;
        private final int tripPurposeNameColumn;
        private final int tripModeNameColumn;
        private final int boardTazColumn;
        private final int alightTazColumn;
        private final String tripType;

        private final String homeName;
        private final String destinationName;
        private final int inboundColumn;
        private final boolean booleanIndicatorVariables;
//        private final int originIsDestinationColumn;
//        private final int destinationIsDestinationColumn;


        private TripStructureDefinition(int originMgraColumn, int destMgraColumn, int originPurposeColumn, int destinationPurposeColumn, int todColumn, int modeColumn, int boardTapColumn, int alightTapColumn, int partySizeColumn,
                                        int tripTimeColumn, int tripDistanceColumn, int tripCostColumn, int tripPurposeNameColumn, int tripModeNameColumn, int recIdColumn, int boardTazColumn, int alightTazColumn,
                                        String tripType, String homeName, String destinationName, int inboundColumn, int setColumn, boolean booleanIndicatorVariables) {
            this.recIdColumn = recIdColumn;
            this.originMgraColumn = originMgraColumn;
            this.destMgraColumn = destMgraColumn;
            this.originPurposeColumn = originPurposeColumn;
            this.destinationPurposeColumn = destinationPurposeColumn;
            this.todColumn = todColumn;
            this.setColumn = setColumn;
            this.modeColumn = modeColumn;
            this.boardTapColumn = boardTapColumn;
            this.alightTapColumn = alightTapColumn;
            this.partySizeColumn = partySizeColumn;
            this.tripTimeColumn = tripTimeColumn;
            this.tripDistanceColumn = tripDistanceColumn;
            this.tripCostColumn = tripCostColumn;
            this.tripPurposeNameColumn = tripPurposeNameColumn;
            this.tripModeNameColumn = tripModeNameColumn;
            this.tripType = tripType;
            this.homeName = homeName;
            this.destinationName = destinationName;
            this.inboundColumn = inboundColumn;
            this.boardTazColumn = boardTazColumn;
            this.alightTazColumn = alightTazColumn;
            this.booleanIndicatorVariables = booleanIndicatorVariables;
        }
        private TripStructureDefinition(int originMgraColumn, int destMgraColumn, int originPurposeColumn, int destinationPurposeColumn, int todColumn, int modeColumn, int boardTapColumn, int alightTapColumn, int partySizeColumn, int columnCount, String tripType, int inboundColumn, int setColumn, boolean booleanIndicatorVariables) {
            this(originMgraColumn,destMgraColumn,originPurposeColumn,destinationPurposeColumn,todColumn,modeColumn,boardTapColumn,alightTapColumn,partySizeColumn,
                  columnCount+1,columnCount+2,columnCount+3,columnCount+4,columnCount+5,columnCount+6,columnCount+7,columnCount+8,tripType,"","",inboundColumn,setColumn,booleanIndicatorVariables);
        }
        private TripStructureDefinition(int originMgraColumn, int destMgraColumn, int todColumn, int modeColumn, int boardTapColumn, int alightTapColumn, int partySizeColumn, int columnCount, String tripType, String homeName, String destinationName, int inboundColumn, int setColumn, boolean booleanIndicatorVariables) {
            this(originMgraColumn,destMgraColumn,-1,-1,todColumn,modeColumn,boardTapColumn,alightTapColumn,partySizeColumn,
                  columnCount+1,columnCount+2,columnCount+3,columnCount+4,columnCount+5,columnCount+6,columnCount+7,columnCount+8,tripType,homeName,destinationName,inboundColumn,setColumn,booleanIndicatorVariables);
        }
        
    }

    public static void main(String ... args) {
        String projectFolder;
        String outputFolder;
        String propertiesFile;
        int feedbackIteration;
        String databaseSchema;
        List<String> definedTables;

        if (args.length == 4 || args.length == 5 || args.length == 6) {
            projectFolder = args[0];
            outputFolder = args[1];
            propertiesFile = new File(projectFolder,"serpm_abm.properties").getAbsolutePath(); //Properties filepath
            feedbackIteration = Integer.parseInt(args[2]);
            databaseSchema = args[3];
            
            //Force proper naming
            if(!Character.isLetter(databaseSchema.charAt(0)))
            	databaseSchema = "S_" + databaseSchema;
            
            
            if (args.length > 5) {
                definedTables = new ArrayList<String>();
                for (String table : args[5].split(","))
                    definedTables.add(table.trim().toLowerCase());
            } else {
                //add all of the tables
                definedTables = Arrays.asList(//"trip",
                                              "accessibilities",
                                              "mgra",
                                              "taz",
                                              "tap",
                                              "mgratotap",
                                              "mgratomgra",
                                              "taztotap",
                                              "hhdata",
                                              "persondata",
                                              "wslocation",
                                              "synhh",
                                              "synperson",
                                              "indivtours",
                                              "jointtours",
                                              "indivtrips",
                                              "jointtrips",
                                              //"definition",
                                              "pnrvehicles",
                                              "cbdvehicles",
                                              "pecascodes",
                                              "districtdefinitions"
                                              );
            }
            //check for full trips set
            List<String> tripsSet = Arrays.asList(/*"trip",*/"indivtrips","jointtrips");
            if (!Collections.disjoint(tripsSet,definedTables) && !definedTables.containsAll(tripsSet))
                throw new IllegalArgumentException("If trips table(s) are included, then all must be included: + " + tripsSet.toString());
        } else {
            throw new IllegalArgumentException("Invalid command line: java ... com.pb.abm.serpm.reports.DataExporter project_folder output_folder feedback_iteration database_schema [table_list]");
        }

        DataExporter dataExporter = new DataExporter(propertiesFile,projectFolder,feedbackIteration,outputFolder);

        try {
//            if (definedTables.contains("trip"))
//                dataExporter.initializeMasterTripTable("trip");
            if (definedTables.contains("accessibilities"))
                dataExporter.exportAccessibilities("accessibilities");
            if (definedTables.contains("mgra"))
                dataExporter.exportMazData("mgra");
            if (definedTables.contains("taz"))
                dataExporter.exportTazData("taz");
            if (definedTables.contains("tap"))
                dataExporter.exportTapData("tap");
            if (definedTables.contains("mgratotap"))
                dataExporter.exportMgraToTapData("mgratotap");
            if (definedTables.contains("mgratomgra"))
                dataExporter.exportMgraToMgraData("mgratomgra");
            if (definedTables.contains("taztotap"))
                dataExporter.exportTazToTapData("taztotap");
            if (definedTables.contains("hhdata"))
                dataExporter.exportHouseholdData("hhdata");
            if (definedTables.contains("persondata"))
                dataExporter.exportPersonData("persondata");
            if (definedTables.contains("wslocation"))
                dataExporter.exportWorkSchoolLocation("wslocation");
            if (definedTables.contains("synhh"))
                dataExporter.exportSyntheticHouseholdData("synhh");
            if (definedTables.contains("synperson"))
                dataExporter.exportSyntheticPersonData("synperson");
            if (definedTables.contains("indivtours"))
                dataExporter.exportIndivToursData("indivtours");
            if (definedTables.contains("jointtours"))
                dataExporter.exportJointToursData("jointtours");
            if (definedTables.contains("indivtrips"))
                dataExporter.exportIndivTripData("indivtrips");
            if (definedTables.contains("jointtrips"))
                dataExporter.exportJointTripData("jointtrips");
//            if (definedTables.contains("definition"))
//                dataExporter.exportDefinitions("definition");
            if (definedTables.contains("pnrvehicles"))
                dataExporter.exportPnrVehicleData("pnrvehicles");
            if (definedTables.contains("cbdvehicles"))
                dataExporter.exportCbdVehicleData("cbdvehicles");
//            if (definedTables.contains("pecascodes"))
//                dataExporter.exportPecasCodes("pecascodes");
            if (definedTables.contains("districtdefinitions"))
                dataExporter.exportDistrictDefinitions("districtdefinitions");
            
        } finally {
            if (dataExporter.tripTableWriter != null)
                dataExporter.tripTableWriter.close();
        }

        if(args.length > 4 && args[4].equals("TRUE"))
        	dataExporter.buildFullSqlImportFile(databaseSchema, true);
        else
        	dataExporter.buildFullSqlImportFile(databaseSchema, false);
    }

}