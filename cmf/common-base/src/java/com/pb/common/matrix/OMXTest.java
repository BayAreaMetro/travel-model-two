package com.pb.common.matrix;

import java.io.File;

import omx.OmxLookup;

/**
 * Test basic OMX Matrix Reader and writer
 * java -classpath "omx.jar;common-base.jar" -Djava.library.path="jhdfdllFolder" com.pb.common.matrix.OMXTest
 * requires omx.jar in classpath and jhdf5.dll,jhdf.dll in the java.library.path
 * @author    Ben Stabler
 * @version   1.0, 02/11/15
 */
public class OMXTest {

	private OMXTest() {}
	
	public static void main(String[] args) {
		
		int[] zoneNames = {100,101,102,103,104};
		File testFile = new File("test.omx");
		
		Matrix mat = new Matrix("test","test",zoneNames.length,zoneNames.length);
		mat.fill(2);
		mat.setExternalNumbersZeroBased(zoneNames);
		
	    OMXMatrixWriter writer = new OMXMatrixWriter(testFile); 
		writer.writeMatrix(mat);
		System.out.println("write test matrix sum:" + Double.valueOf(mat.getSum()));
		
		OMXMatrixReader reader = new OMXMatrixReader(testFile); 
		Matrix matIn = reader.readMatrix("test");
		System.out.println("read test matrix sum:" + Double.valueOf(matIn.getSum()));
		
		for (int j = 0 ; j < matIn.getExternalRowNumbersZeroBased().length; j++) {
			System.out.println("zone " + String.valueOf(matIn.getExternalRowNumbersZeroBased()[j]));
		}
		
	}

}
