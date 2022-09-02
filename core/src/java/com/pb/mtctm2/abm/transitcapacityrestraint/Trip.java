package com.pb.mtctm2.abm.transitcapacityrestraint;

import org.apache.log4j.Logger;
/**
 * A holder class for trips.
 * @author joel.freedman
 *
 */
class Trip implements Comparable{
   	long hhid;		
	long personId;
	int personNumber;
	int tourid;
	int stopid;
	int inbound;
	int joint;
	int numberParticipants;

	int originMaz;
	int destinationMaz;
	int departPeriod;
	float departTime; //minutes after 3 AM
	int occupancy;
	float sampleRate;
	int mode;
	int boardingTap;
	int alightingTap;
	int set;
	float transitPathRandom;
	String tourPurpose;
	String originPurpose;
	String destinationPurpose;
	float distance;
	int parkingMaz;
	int avAvailable;
	int tourMode;
	
	
	public Trip(long hhid,long personId,int personNumber, int tourid,int stopid,int inbound,int joint,int originMaz, int destinationMaz, int departPeriod, float departTime, float sampleRate, int mode, int boardingTap, int alightingTap, int set, float rnum){
       	this.hhid = hhid;		
       	this.personId = personId;
    	this.personNumber = personNumber;
    	this.tourid = tourid;
    	this.stopid =  stopid;
    	this.inbound = inbound;
    	this.joint = joint;

		this.originMaz = originMaz;
		this.destinationMaz = destinationMaz;
		this.departPeriod = departPeriod;
		this.departTime = departTime;
		this.sampleRate = sampleRate;
		this.mode = mode;
		this.boardingTap = boardingTap;
		this.alightingTap = alightingTap;
		this.set = set;
		this.transitPathRandom = rnum;
		
		
	}
	
	public void logTrip(Logger logger) {
		
		logger.info("   hhid:                    "+hhid);
		logger.info("   personId:                "+personId);
    	logger.info("   personNumber:            "+personNumber);
    	logger.info("   tourid:                  "+tourid);
    	logger.info("   stopid:                  "+stopid);
    	logger.info("   inbound:                 "+inbound);
    	logger.info("   joint:                   "+joint);
    	logger.info("   originMaz:               "+originMaz);
    	logger.info("   destinationMaz:          "+destinationMaz);
    	logger.info("   departPeriod:            "+departPeriod);
    	logger.info("   departTime:              "+departTime);
    	logger.info("   sampleRate:              "+sampleRate);
    	logger.info("   mode:                    "+mode);
    	logger.info("   original boardingTap:    "+boardingTap);
    	logger.info("   original alightingTap:   "+alightingTap);
    	logger.info("   original set:            "+set);
    	logger.info("   transit path rnum        "+transitPathRandom);
	}

	public long getHhid() {
		return hhid;
	}

	public void setHhid(long hhid) {
		this.hhid = hhid;
	}

	public long getPersonId() {
		return personId;
	}

	public void setPersonId(long personId) {
		this.personId = personId;
	}

	public int getPersonNumber() {
		return personNumber;
	}

	public void setPersonNumber(int personNumber) {
		this.personNumber = personNumber;
	}

	public int getTourid() {
		return tourid;
	}

	public void setTourid(int tourid) {
		this.tourid = tourid;
	}

	public int getStopid() {
		return stopid;
	}

	public void setStopid(int stopid) {
		this.stopid = stopid;
	}

	public int getInbound() {
		return inbound;
	}

	public void setInbound(int inbound) {
		this.inbound = inbound;
	}

	public int getJoint() {
		return joint;
	}

	public void setJoint(int joint) {
		this.joint = joint;
	}

	public int getOriginMaz() {
		return originMaz;
	}

	public void setOriginMaz(int originMaz) {
		this.originMaz = originMaz;
	}

	public int getDestinationMaz() {
		return destinationMaz;
	}

	public void setDestinationMaz(int destinationMaz) {
		this.destinationMaz = destinationMaz;
	}

	public int getDepartPeriod() {
		return departPeriod;
	}

	public void setDepartPeriod(int departPeriod) {
		this.departPeriod = departPeriod;
	}

	public float getDepartTime() {
		return departTime;
	}

	public void setDepartTime(float departTime) {
		this.departTime = departTime;
	}

	public int getOccupancy() {
		return occupancy;
	}

	public void setOccupancy(int occupancy) {
		this.occupancy = occupancy;
	}

	public float getSampleRate() {
		return sampleRate;
	}

	public void setSampleRate(float sampleRate) {
		this.sampleRate = sampleRate;
	}

	public int getMode() {
		return mode;
	}

	public void setMode(int mode) {
		this.mode = mode;
	}

	public int getBoardingTap() {
		return boardingTap;
	}

	public void setBoardingTap(int boardingTap) {
		this.boardingTap = boardingTap;
	}

	public int getAlightingTap() {
		return alightingTap;
	}

	public void setAlightingTap(int alightingTap) {
		this.alightingTap = alightingTap;
	}

	public int getSet() {
		return set;
	}

	public void setSet(int set) {
		this.set = set;
	}

	public String getTourPurpose() {
		return tourPurpose;
	}

	public void setTourPurpose(String tourPurpose) {
		this.tourPurpose = tourPurpose;
	}

	public String getOriginPurpose() {
		return originPurpose;
	}

	public void setOriginPurpose(String originPurpose) {
		this.originPurpose = originPurpose;
	}

	public String getDestinationPurpose() {
		return destinationPurpose;
	}

	public void setDestinationPurpose(String destinationPurpose) {
		this.destinationPurpose = destinationPurpose;
	}

	public float getDistance() {
		return distance;
	}

	public void setDistance(float distance) {
		this.distance = distance;
	}

	public int getParkingMaz() {
		return parkingMaz;
	}

	public void setParkingMaz(int parkingMaz) {
		this.parkingMaz = parkingMaz;
	}

	public int getAvAvailable() {
		return avAvailable;
	}

	public void setAvAvailable(int avAvailable) {
		this.avAvailable = avAvailable;
	}

	public int getNumberParticipants() {
		return numberParticipants;
	}

	public void setNumberParticipants(int numberParticipants) {
		this.numberParticipants = numberParticipants;
	}

	public int getTourMode() {
		return tourMode;
	}

	public void setTourMode(int tourMode) {
		this.tourMode = tourMode;
	}

	public float getTransitPathRandom() {
		return transitPathRandom;
	}

	public void setTransitPathRandom(float transitPathRandom) {
		this.transitPathRandom = transitPathRandom;
	}

	/**
	 * Compare based on departure time.
	 */
	public int compareTo(Object aThat) {
	    final int BEFORE = -1;
	    final int EQUAL = 0;
	    final int AFTER = 1;

	    final Trip that = (Trip)aThat;

	    //primitive numbers follow this form
	    if (this.departTime < that.departTime) return BEFORE;
	    if (this.departTime > that.departTime) return AFTER;

		return EQUAL;
	}
}
