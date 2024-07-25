package com.pb.mtctm2.abm.application;

import java.util.HashMap;

import com.pb.mtctm2.abm.ctramp.ExplicitTelecommuteDMU;

public class SandagExplicitTelecommuteDMU
        extends ExplicitTelecommuteDMU
{

    public SandagExplicitTelecommuteDMU()
    {
        super();
        setupMethodIndexMap();
    }

    private void setupMethodIndexMap()
    {
        methodIndexMap = new HashMap<String, Integer>();

        methodIndexMap.put("getLnhhinc",0);//;getHhIncomeInDollars", 0);
        methodIndexMap.put("getPersonIsFullTimeWorker", 1);
        methodIndexMap.put("getPersonIsPartTimeWorker", 2);

    }

    public double getValueForIndex(int variableIndex, int arrayIndex)
    {

        switch (variableIndex)
        {
            case 0:
                return getLnhhinc(); //getIncomeInDollars();
            case 1:
                return getPersonIsFullTimeWorker();
            case 2:
                return getPersonIsPartTimeWorker();



            default:
                logger.error("method number = " + variableIndex + " not found");
                throw new RuntimeException("method number = " + variableIndex + " not found");

        }
    }

}