package com.pb.mtctm2.abm.ctramp;

/**
 * This class is used for storing constants. Many of these are listed in the
 * sandag.inc file associated with the FORTRAN code. We should eventually move these
 * into a properties file and have this class set them from the prop file.
 * 
 * I am just trying to not get bogged down in the details.
 * 
 * @author Christi Willison
 * @version Nov 6, 2008
 *          <p/>
 *          Created by IntelliJ IDEA.
 */
public class Constants
{

    public static int       MAX_EXTERNAL       = 12;
    public static float     AutoCostPerMile    = 10.0f;

    public static float[][] parkingCost        = {{0.0f, 50.0f, 200.0f, 300.0f, 400.0f},
            {0.0f, 50.0f, 125.0f, 200.0f, 400.0f}, {0.0f, 50.0f, 100.0f, 200.0f, 400.0f}};

    //public static float     walkMinutesPerFoot = 0.0038f;                                 // 20
    // minutes per mile (dist is in feet) or 3 mph
    
    //public static float     bikeMinutesPerFoot = 0.00095f;                                // 5
    // minutes per mile (dist is in feet) or 12 mph

    
    // revised by AshishK - 8/12/2015
    public static double WALK_SPEED = 3;				//3 mph
    public static double BIKE_SPEED = 12;				//12 mph
    
    public static double walkMinutesPerFoot = (1.0/WALK_SPEED)*60/5280;
    public static double bikeMinutesPerFoot = (1.0/BIKE_SPEED)*60/5280;		
}
