package com.pb.mtctm2.abm.application;

public enum TimePeriod {
	EA("EA"),
	AM("AM"),
	MD("MD"),
	PM("PM"),
	EV("EV");
	
	private final String shortName;
	
	private TimePeriod(String shortName) {
		this.shortName = shortName;
	}
	
	public String getShortName() {
		return shortName;
	}

}
