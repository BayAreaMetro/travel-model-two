package com.pb.mtctm2.abm.maas;

/**
 * A holder class for vehicle trips read into the model.
 * @author joel.freedman
 *
 */
class VehicleTrip implements Comparable{
   	long hhid;		
	int personNumber;
	int tourid;
	int stopid;
	int inbound;

	int originMaz;
	int destinationMaz;
	int departPeriod;
	float departTime; //minutes after 3 AM
	int occupancy;
	float sampleRate;
	int mode;
	
	/**
	 * A method to create a trip.
	 * @param originMaz
	 * @param destinationMaz
	 * @param departPeriod
	 * @param departTime
	 * @param sampleRate
	 * @param mode
	 */
	public VehicleTrip(long hhid,int personNumber, int tourid,int stopid,int inbound,int originMaz, int destinationMaz, int departPeriod, float departTime, float sampleRate, int mode){
       	this.hhid = hhid;		
    	this.personNumber = personNumber;
    	this.tourid = tourid;
    	this.stopid =  stopid;
    	this.inbound = inbound;

		this.originMaz = originMaz;
		this.destinationMaz = destinationMaz;
		this.departPeriod = departPeriod;
		this.departTime = departTime;
		this.sampleRate = sampleRate;
		this.mode = mode;
		
		
	}

	/**
	 * Compare based on departure time.
	 */
	public int compareTo(Object aThat) {
	    final int BEFORE = -1;
	    final int EQUAL = 0;
	    final int AFTER = 1;

	    final VehicleTrip that = (VehicleTrip)aThat;

	    //primitive numbers follow this form
	    if (this.departTime < that.departTime) return BEFORE;
	    if (this.departTime > that.departTime) return AFTER;

		return EQUAL;
	}
}
