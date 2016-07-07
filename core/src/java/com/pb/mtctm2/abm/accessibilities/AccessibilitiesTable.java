package com.pb.mtctm2.abm.accessibilities;

import com.pb.common.util.ObjectUtil;
import com.pb.common.datafile.CSVFileWriter;
import com.pb.common.datafile.OLD_CSVFileReader;
import com.pb.common.datafile.TableDataSet;
import java.io.File;
import java.io.IOException;
import java.io.Serializable;
import org.apache.log4j.Logger;

/**
 * This class holds the accessibility table that is built, or reads it from a previously written file.
 * 
 * @author Jim Hicks
 * @version May, 2011
 */
public final class AccessibilitiesTable
        implements Serializable
{

    protected transient Logger             logger                                           = Logger.getLogger(AccessibilitiesTable.class);

    private static final int            NONMANDATORY_AUTO_ACCESSIBILITY_FIELD_NUMBER     = 1;
    private static final int            NONMANDATORY_TRANSIT_ACCESSIBILITY_FIELD_NUMBER  = 2;
    private static final int            NONMANDATORY_NONMOTOR_ACCESSIBILITY_FIELD_NUMBER = 3;
    private static final int            NONMANDATORY_SOV_0_ACCESSIBILITY_FIELD_NUMBER    = 4;
    private static final int            NONMANDATORY_SOV_1_ACCESSIBILITY_FIELD_NUMBER    = 5;
    private static final int            NONMANDATORY_SOV_2_ACCESSIBILITY_FIELD_NUMBER    = 6;
    private static final int            NONMANDATORY_HOV_0_ACCESSIBILITY_FIELD_NUMBER    = 7;
    private static final int            NONMANDATORY_HOV_1_ACCESSIBILITY_FIELD_NUMBER    = 8;
    private static final int            NONMANDATORY_HOV_2_ACCESSIBILITY_FIELD_NUMBER    = 9;
    private static final int            SHOP_ACCESSIBILITY_HOV_INSUFFICIENT_INDEX        = 10;
    private static final int            SHOP_ACCESSIBILITY_HOV_SUFFICIENT_INDEX          = 11;
    private static final int            SHOP_ACCESSIBILITY_HOV_OVERSUFFICIENT_INDEX      = 12;
    private static final int            MAINT_ACCESSIBILITY_HOV_INSUFFICIENT_INDEX       = 13;
    private static final int            MAINT_ACCESSIBILITY_HOV_SUFFICIENT_INDEX         = 14;
    private static final int            MAINT_ACCESSIBILITY_HOV_OVERSUFFICIENT_INDEX     = 15;
    private static final int            EAT_ACCESSIBILITY_HOV_INSUFFICIENT_INDEX         = 16;
    private static final int            EAT_ACCESSIBILITY_HOV_SUFFICIENT_INDEX           = 17;
    private static final int            EAT_ACCESSIBILITY_HOV_OVERSUFFICIENT_INDEX       = 18;
    private static final int            VISIT_ACCESSIBILITY_HOV_INSUFFICIENT_INDEX       = 19;
    private static final int            VISIT_ACCESSIBILITY_HOV_SUFFICIENT_INDEX         = 20;
    private static final int            VISIT_ACCESSIBILITY_HOV_OVERSUFFICIENT_INDEX     = 21;
    private static final int            DISCR_ACCESSIBILITY_HOV_INSUFFICIENT_INDEX       = 22;
    private static final int            DISCR_ACCESSIBILITY_HOV_SUFFICIENT_INDEX         = 23;
    private static final int            DISCR_ACCESSIBILITY_HOV_OVERSUFFICIENT_INDEX     = 24;
    private static final int            ESCORT_ACCESSIBILITY_HOV_INSUFFICIENT_INDEX      = 25;
    private static final int            ESCORT_ACCESSIBILITY_HOV_SUFFICIENT_INDEX        = 26;
    private static final int            ESCORT_ACCESSIBILITY_HOV_OVERSUFFICIENT_INDEX    = 27;
    private static final int            SHOP_ACCESSIBILITY_SOV_INSUFFICIENT_INDEX        = 28;
    private static final int            SHOP_ACCESSIBILITY_SOV_SUFFICIENT_INDEX          = 29;
    private static final int            SHOP_ACCESSIBILITY_SOV_OVERSUFFICIENT_INDEX      = 30;
    private static final int            MAINT_ACCESSIBILITY_SOV_INSUFFICIENT_INDEX       = 31;
    private static final int            MAINT_ACCESSIBILITY_SOV_SUFFICIENT_INDEX         = 32;
    private static final int            MAINT_ACCESSIBILITY_SOV_OVERSUFFICIENT_INDEX     = 33;
    private static final int            DISCR_ACCESSIBILITY_SOV_INSUFFICIENT_INDEX       = 40;
    private static final int            DISCR_ACCESSIBILITY_SOV_SUFFICIENT_INDEX         = 41;
    private static final int            DISCR_ACCESSIBILITY_SOV_OVERSUFFICIENT_INDEX     = 42;
    private static final int            TOTAL_EMPLOYMENT_ACCESSIBILITY_INDEX             = 45;


    // accessibilities by mgra, accessibility alternative
    private float[][]                   accessibilities;


    /**
     * array of previously computed accessibilities
     * @param computedAccessibilities array of accessibilities
     * 
     * use this constructor if the accessibilities were calculated as opposed to read from a file.
     */
    public AccessibilitiesTable( float[][] computedAccessibilities ) {
        accessibilities = computedAccessibilities;
    }

    /**
     * file name for store accessibilities
     * @param accessibilitiesInputFileName path and filename of file to read
     * 
     * use this constructor if the accessibilities are to be read from a file.
     */
    public AccessibilitiesTable( String accessibilitiesInputFileName ) {
        readAccessibilityTableFromFile( accessibilitiesInputFileName );
    }



    private void readAccessibilityTableFromFile(String fileName)
    {

        File accFile = new File(fileName);

        // read in the csv table
        TableDataSet accTable;
        try
        {
            OLD_CSVFileReader reader = new OLD_CSVFileReader();
            reader.setDelimSet("," + reader.getDelimSet());
            accTable = reader.readFile(accFile);

        } catch (Exception e)
        {
            logger.fatal(String.format( "Exception occurred reading accessibility data file: %s into TableDataSet object.", fileName ) );
            throw new RuntimeException();
        }

        accessibilities = accTable.getValues();

    }

    
    public void writeAccessibilityTableToFile( String accFileName, int[] mgraColumnValues, String mgraColumnHeading )
    {
        
        File accFile = new File(accFileName);
        TableDataSet accData = TableDataSet.create(accessibilities);
        accData.appendColumn( mgraColumnValues, mgraColumnHeading );
        CSVFileWriter csv = new CSVFileWriter();

        try
        {
            csv.writeFile(accData, accFile);
        } catch (IOException e)
        {

            logger.error("Error trying to write accessiblities data file " + accFileName);
            throw new RuntimeException(e);
        }

    }
    

    
    public float getAggregateAccessibility(String type, int homeMgra)
    {
        float returnValue = 0;

        if (type.equalsIgnoreCase("auto")) returnValue = accessibilities[homeMgra][NONMANDATORY_AUTO_ACCESSIBILITY_FIELD_NUMBER - 1];
        else if (type.equalsIgnoreCase("transit")) returnValue = accessibilities[homeMgra][NONMANDATORY_TRANSIT_ACCESSIBILITY_FIELD_NUMBER - 1];
        else if (type.equalsIgnoreCase("nonmotor")) returnValue = accessibilities[homeMgra][NONMANDATORY_NONMOTOR_ACCESSIBILITY_FIELD_NUMBER - 1];
        else if (type.equalsIgnoreCase("sov0")) returnValue = accessibilities[homeMgra][NONMANDATORY_SOV_0_ACCESSIBILITY_FIELD_NUMBER - 1];
        else if (type.equalsIgnoreCase("sov1")) returnValue = accessibilities[homeMgra][NONMANDATORY_SOV_1_ACCESSIBILITY_FIELD_NUMBER - 1];
        else if (type.equalsIgnoreCase("sov2")) returnValue = accessibilities[homeMgra][NONMANDATORY_SOV_2_ACCESSIBILITY_FIELD_NUMBER - 1];
        else if (type.equalsIgnoreCase("hov0")) returnValue = accessibilities[homeMgra][NONMANDATORY_HOV_0_ACCESSIBILITY_FIELD_NUMBER - 1];
        else if (type.equalsIgnoreCase("hov1")) returnValue = accessibilities[homeMgra][NONMANDATORY_HOV_1_ACCESSIBILITY_FIELD_NUMBER - 1];
        else if (type.equalsIgnoreCase("hov2")) returnValue = accessibilities[homeMgra][NONMANDATORY_HOV_2_ACCESSIBILITY_FIELD_NUMBER - 1];
        else if (type.equalsIgnoreCase("shop0")) returnValue = accessibilities[homeMgra][SHOP_ACCESSIBILITY_HOV_INSUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("shop1")) returnValue = accessibilities[homeMgra][SHOP_ACCESSIBILITY_HOV_SUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("shop2")) returnValue = accessibilities[homeMgra][SHOP_ACCESSIBILITY_HOV_OVERSUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("maint0")) returnValue = accessibilities[homeMgra][MAINT_ACCESSIBILITY_HOV_INSUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("maint1")) returnValue = accessibilities[homeMgra][MAINT_ACCESSIBILITY_HOV_SUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("maint2")) returnValue = accessibilities[homeMgra][MAINT_ACCESSIBILITY_HOV_OVERSUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("eatOut0")) returnValue = accessibilities[homeMgra][EAT_ACCESSIBILITY_HOV_INSUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("eatOut1")) returnValue = accessibilities[homeMgra][EAT_ACCESSIBILITY_HOV_SUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("eatOut2")) returnValue = accessibilities[homeMgra][EAT_ACCESSIBILITY_HOV_OVERSUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("visit0")) returnValue = accessibilities[homeMgra][VISIT_ACCESSIBILITY_HOV_INSUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("visit1")) returnValue = accessibilities[homeMgra][VISIT_ACCESSIBILITY_HOV_SUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("visit2")) returnValue = accessibilities[homeMgra][VISIT_ACCESSIBILITY_HOV_OVERSUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("discr0")) returnValue = accessibilities[homeMgra][DISCR_ACCESSIBILITY_HOV_INSUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("discr1")) returnValue = accessibilities[homeMgra][DISCR_ACCESSIBILITY_HOV_SUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("discr2")) returnValue = accessibilities[homeMgra][DISCR_ACCESSIBILITY_HOV_OVERSUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("escort0")) returnValue = accessibilities[homeMgra][ESCORT_ACCESSIBILITY_HOV_INSUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("escort1")) returnValue = accessibilities[homeMgra][ESCORT_ACCESSIBILITY_HOV_SUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("escort2")) returnValue = accessibilities[homeMgra][ESCORT_ACCESSIBILITY_HOV_OVERSUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("totEmp")) returnValue = accessibilities[homeMgra][TOTAL_EMPLOYMENT_ACCESSIBILITY_INDEX - 1];
        else if (type.equalsIgnoreCase("shopSov0")) returnValue = accessibilities[homeMgra][SHOP_ACCESSIBILITY_SOV_INSUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("shopSov1")) returnValue = accessibilities[homeMgra][SHOP_ACCESSIBILITY_SOV_SUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("shopSov2")) returnValue = accessibilities[homeMgra][SHOP_ACCESSIBILITY_SOV_OVERSUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("maintSov0")) returnValue = accessibilities[homeMgra][MAINT_ACCESSIBILITY_SOV_INSUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("maintSov1")) returnValue = accessibilities[homeMgra][MAINT_ACCESSIBILITY_SOV_SUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("maintSov2")) returnValue = accessibilities[homeMgra][MAINT_ACCESSIBILITY_SOV_OVERSUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("discrSov0")) returnValue = accessibilities[homeMgra][DISCR_ACCESSIBILITY_SOV_INSUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("discrSov1")) returnValue = accessibilities[homeMgra][DISCR_ACCESSIBILITY_SOV_SUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("discrSov2")) returnValue = accessibilities[homeMgra][DISCR_ACCESSIBILITY_SOV_OVERSUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("shopHov0")) returnValue = accessibilities[homeMgra][SHOP_ACCESSIBILITY_HOV_INSUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("shopHov1")) returnValue = accessibilities[homeMgra][SHOP_ACCESSIBILITY_HOV_SUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("shopHov2")) returnValue = accessibilities[homeMgra][SHOP_ACCESSIBILITY_HOV_OVERSUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("maintHov0")) returnValue = accessibilities[homeMgra][MAINT_ACCESSIBILITY_HOV_INSUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("maintHov1")) returnValue = accessibilities[homeMgra][MAINT_ACCESSIBILITY_HOV_SUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("maintHov2")) returnValue = accessibilities[homeMgra][MAINT_ACCESSIBILITY_HOV_OVERSUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("discrHov0")) returnValue = accessibilities[homeMgra][DISCR_ACCESSIBILITY_HOV_INSUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("discrHov1")) returnValue = accessibilities[homeMgra][DISCR_ACCESSIBILITY_HOV_SUFFICIENT_INDEX - 1];
        else if (type.equalsIgnoreCase("discrHov2")) returnValue = accessibilities[homeMgra][DISCR_ACCESSIBILITY_HOV_OVERSUFFICIENT_INDEX - 1];
        else
        {
            logger.error("argument type = " + type + ", is not valid.  Must be either 'auto', 'transit', 'nonmotor', or hov0, hov1, or hov2.");
            throw new RuntimeException();
        }

        return returnValue;

    }

}
