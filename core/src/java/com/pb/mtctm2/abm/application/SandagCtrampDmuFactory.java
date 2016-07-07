/*
 * Copyright 2005 PB Consult Inc. Licensed under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance with the License. You
 * may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
 * Unless required by applicable law or agreed to in writing, software distributed
 * under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
 * CONDITIONS OF ANY KIND, either express or implied. See the License for the
 * specific language governing permissions and limitations under the License.
 */
package com.pb.mtctm2.abm.application;

import java.io.Serializable;

import com.pb.mtctm2.abm.ctramp.AtWorkSubtourFrequencyDMU;
import com.pb.mtctm2.abm.ctramp.AutoOwnershipChoiceDMU;
import com.pb.mtctm2.abm.ctramp.CoordinatedDailyActivityPatternDMU;
import com.pb.mtctm2.abm.ctramp.CtrampDmuFactoryIf;
import com.pb.mtctm2.abm.ctramp.DcSoaDMU;
import com.pb.mtctm2.abm.ctramp.DestChoiceDMU;
import com.pb.mtctm2.abm.ctramp.DestChoiceTwoStageModelDMU;
import com.pb.mtctm2.abm.ctramp.DestChoiceTwoStageSoaTazDistanceUtilityDMU;
import com.pb.mtctm2.abm.ctramp.IndividualMandatoryTourFrequencyDMU;
import com.pb.mtctm2.abm.ctramp.IndividualNonMandatoryTourFrequencyDMU;
import com.pb.mtctm2.abm.ctramp.JointTourModelsDMU;
import com.pb.mtctm2.abm.ctramp.ModelStructure;
import com.pb.mtctm2.abm.ctramp.ParkingChoiceDMU;
import com.pb.mtctm2.abm.ctramp.ParkingProvisionChoiceDMU;
import com.pb.mtctm2.abm.ctramp.StopFrequencyDMU;
import com.pb.mtctm2.abm.ctramp.StopLocationDMU;
import com.pb.mtctm2.abm.ctramp.TourDepartureTimeAndDurationDMU;
import com.pb.mtctm2.abm.ctramp.TourModeChoiceDMU;
import com.pb.mtctm2.abm.ctramp.TransponderChoiceDMU;
import com.pb.mtctm2.abm.ctramp.TripModeChoiceDMU;

/**
 * ArcCtrampDmuFactory is a class that ...
 * 
 * @author Kimberly Grommes
 * @version 1.0, Jul 17, 2008 Created by IntelliJ IDEA.
 */
public class SandagCtrampDmuFactory implements CtrampDmuFactoryIf, Serializable
{

    private ModelStructure modelStructure;

    public SandagCtrampDmuFactory(ModelStructure modelStructure)
    {
        this.modelStructure = modelStructure;
    }

    public AutoOwnershipChoiceDMU getAutoOwnershipDMU()
    {
        return new SandagAutoOwnershipChoiceDMU();
    }

    public TransponderChoiceDMU getTransponderChoiceDMU()
    {
        return new SandagTransponderChoiceDMU();
    }

    public ParkingProvisionChoiceDMU getFreeParkingChoiceDMU()
    {
        return new SandagParkingProvisionChoiceDMU();
    }

    public CoordinatedDailyActivityPatternDMU getCoordinatedDailyActivityPatternDMU()
    {
        return new SandagCoordinatedDailyActivityPatternDMU();
    }

    public DcSoaDMU getDcSoaDMU()
    {
        return new SandagDcSoaDMU();
    }

    public DestChoiceDMU getDestChoiceDMU()
    {
        return new SandagDestChoiceDMU(modelStructure);
    }

    public DestChoiceTwoStageModelDMU getDestChoiceSoaTwoStageDMU()
    {
        return new SandagDestChoiceSoaTwoStageModelDMU(modelStructure);
    }    
    
    public DestChoiceTwoStageSoaTazDistanceUtilityDMU getDestChoiceSoaTwoStageTazDistUtilityDMU()
    {
        return new SandagDestChoiceSoaTwoStageTazDistUtilityDMU();
    }    
    
    public TourModeChoiceDMU getModeChoiceDMU()
    {
        return new SandagTourModeChoiceDMU(modelStructure);
    }

    public IndividualMandatoryTourFrequencyDMU getIndividualMandatoryTourFrequencyDMU()
    {
        return new SandagIndividualMandatoryTourFrequencyDMU();
    }

    public TourDepartureTimeAndDurationDMU getTourDepartureTimeAndDurationDMU()
    {
        return new SandagTourDepartureTimeAndDurationDMU(modelStructure);
    }

    public AtWorkSubtourFrequencyDMU getAtWorkSubtourFrequencyDMU()
    {
        return new SandagAtWorkSubtourFrequencyDMU(modelStructure);
    }

    public JointTourModelsDMU getJointTourModelsDMU()
    {
        return new SandagJointTourModelsDMU(modelStructure);
    }

    public IndividualNonMandatoryTourFrequencyDMU getIndividualNonMandatoryTourFrequencyDMU()
    {
        return new SandagIndividualNonMandatoryTourFrequencyDMU();
    }

    public StopFrequencyDMU getStopFrequencyDMU()
    {
        return new SandagStopFrequencyDMU(modelStructure);
    }

    public StopLocationDMU getStopLocationDMU()
    {
        return new SandagStopLocationDMU(modelStructure);
    }

    public TripModeChoiceDMU getTripModeChoiceDMU()
    {
        return new SandagTripModeChoiceDMU(modelStructure);
    }

    public ParkingChoiceDMU getParkingChoiceDMU()
    {
        return new SandagParkingChoiceDMU();
    }

}
