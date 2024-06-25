package com.pb.common.matrix;

import java.io.File;
import java.util.Set;

import org.apache.log4j.Logger;

import omx.OmxFile;
import omx.OmxMatrix;
import omx.OmxMatrix.OmxDoubleMatrix;
import omx.OmxLookup;

/**
 * Implements an OMX MatrixReader
 *
 * @author    Ben Stabler
 * @version   1.0, 02/11/15
 */
public class OMXMatrixReader extends MatrixReader {

	private OmxFile omxFile = null;     
    protected static Logger logger = Logger.getLogger("com.pb.common.matrix");

    /**
     * Prevent outside classes from instantiating the default constructor.
     */
    private OMXMatrixReader() {}

    /**
     * @param file represents the physical matrix file
     */
    public OMXMatrixReader(File file) throws MatrixException {
        this.file = file;
        openOMXFile();
    }

    public Matrix readMatrix() throws MatrixException {
        return readMatrix("");
    }

    public Matrix readMatrix(String name) throws MatrixException {
    	 if(omxFile.getMatrixNames().contains(name)){
    	 	return readData(name);
    	 }
    	 else{
    		 logger.info("No matrix in " + file.getPath() + " with name " + name);
    		 throw new MatrixException(MatrixException.INVALID_TABLE_NAME + " " + name); 
    	 }
    		 
    }

    private void openOMXFile() throws MatrixException {        
        try {
        	omxFile = new OmxFile(file.getPath());
        	omxFile.openReadWrite();
        }
        catch (Exception e) {
            throw new MatrixException(e, MatrixException.FILE_CANNOT_BE_OPENED + ", "+ file.getPath());
        }
    }

	/** 
	 * Reads and returns an entire matrix
	 *
	 */
	public Matrix[] readMatrices() throws MatrixException {

		Matrix[] m = null;
		Set<String> matNames = omxFile.getMatrixNames();
		m = new Matrix[matNames.size()];
		int i = 0;
		for(String matName : omxFile.getMatrixNames()){
			m[i] = readMatrix(matName);
			i++;
		}
		return m;
	};

    /**
    * Returns a matrix.
    *
    */
    private Matrix readData(String name) {
    	OmxMatrix.OmxDoubleMatrix omxMat = null;
    	try {
    		omxMat = (OmxDoubleMatrix) omxFile.getMatrix(name);
    		double[][] values = omxMat.getData();
    		
    		//convert to Matrix float[][]
    		float[][] valuesFloat = new float[values.length][values[0].length];
    		for (int i = 0 ; i < values.length; i++) {
    			for (int j = 0 ; j < values[0].length; j++) {
    				valuesFloat[i][j] = (float) values[i][j];
    			}
    		}
    		
            Matrix m = new Matrix(name, name, valuesFloat);
            
            //set zone numbers if found
            //CUBE - 1 to X
            //VISUM - 'NO'
            //EMME - 'zone number'
            //TransCAD - ?
            if (omxFile.getLookupNames().contains("NO")) {
            	OmxLookup.OmxIntLookup omxZoneNums = (OmxLookup.OmxIntLookup)omxFile.getLookup("NO");
            	m.setExternalNumbersZeroBased(omxZoneNums.getLookup());
            }
            if (omxFile.getLookupNames().contains("zone number")) {
            	OmxLookup.OmxIntLookup omxZoneNums = (OmxLookup.OmxIntLookup)omxFile.getLookup("zone number");
            	m.setExternalNumbersZeroBased(omxZoneNums.getLookup());
            }
            
            return m;
        }
        catch (Exception e) {
            throw new MatrixException("Matrix not found: " + name);
        }
    }
}
