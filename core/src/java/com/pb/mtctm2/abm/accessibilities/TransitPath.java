package com.pb.mtctm2.abm.accessibilities;

public class TransitPath implements Comparable<TransitPath>{
	    
    public int              oMaz;
    public int              dMaz;
    public int              accEgr;
    public float            accUtil;
    public float            egrUtil;
    public float			tazTazUtil;
    public static final int NA = -999;
        
	public TransitPath(int oMaz, int dMaz, int accEgr, float tazTazUtil, float accUtil, float egrUtil) {
		this.oMaz = oMaz;
		this.dMaz = dMaz;
		this.accEgr = accEgr;
		this.tazTazUtil = tazTazUtil;
		this.accUtil = accUtil;
		this.egrUtil = egrUtil;
	}
	
	public float getTotalUtility() {
		return(accUtil + tazTazUtil + egrUtil);
	}
	
	@Override
	public int compareTo(TransitPath o) {
					
		//return compareTo value
	    if ( getTotalUtility() < o.getTotalUtility() ) {
	    	return -1;
	    } else if (getTotalUtility() == o.getTotalUtility()) {
	    	return 0;
	    } else {
	    	return 1;
	    }		
	}
	
}