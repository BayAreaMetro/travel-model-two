package com.pb.mtctm2.abm.application;

import java.util.HashMap;
import java.util.ResourceBundle;
import com.pb.common.util.ResourceUtil;
import com.pb.mtctm2.abm.ctramp.CtrampApplication;

public class SandagCtrampApplication
        extends CtrampApplication
{

    public static final String PROGRAM_VERSION              = "09June2008";
    public static final String PROPERTIES_PROJECT_DIRECTORY = "Project.Directory";

    public SandagCtrampApplication(ResourceBundle rb, HashMap<String,String> rbMap)
    {
        super(rb, rbMap);

        projectDirectory = rbMap.get( PROPERTIES_PROJECT_DIRECTORY );

    }

}