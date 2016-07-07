package com.pb.common.matrix;

import java.io.File;

import org.apache.log4j.Logger;

import omx.OmxFile;
import omx.OmxLookup;
import omx.OmxMatrix;

/**
 * Implements an OMX MatrixWriter
 *
 * @author    Ben Stabler
 * @version   1.0, 02/11/15
 */
public class OMXMatrixWriter extends MatrixWriter {

	private OmxFile omxFile = null;    
	protected static Logger logger = Logger.getLogger("com.pb.common.matrix");
	private double defaultNA = Double.valueOf(0);

	/**
	 * Prevent outside classes from instantiating the default constructor.
	 */
	private OMXMatrixWriter() {}

	/**
	 * @param file represents the physical matrix file
	 */
	public OMXMatrixWriter(File file) throws MatrixException {
		this.file = file;
	}

	public void writeMatrix(Matrix m) throws MatrixException {
		writeMatrix(m.name, m);
	}

	public void writeMatrix(String name, Matrix m) throws MatrixException {
		writeData(name, m);
	}

	/**
	 * Writes a matrix to the underlying file.
	 *
	 *@param  name  matrix name
	 *@param  m  the matrix to write
	 *
	 */
	private void writeData(String name, Matrix m) {
		omxFile = new OmxFile(file.getPath());

		try {
			if(file.exists()) {
				omxFile.openReadWrite();
			} else {
				int[] shape = new int[2];
				shape[0] = m.getRowCount();
				shape[1] = m.getColumnCount();
				omxFile.openNew(shape);
			}
		} catch (Exception e) {
			throw new MatrixException(e, MatrixException.FILE_NOT_FOUND + ", "+ file);
		}

		try {
			//convert to double[][]
			float[][] values = m.getValues();
			double[][] valuesDouble = new double[values.length][values[0].length];
			for (int i = 0 ; i < values.length; i++) {
				for (int j = 0 ; j < values[0].length; j++) {
					valuesDouble[i][j] = (double) values[i][j];
				}
			}   

			//create sequential CUBE_MAT_NUMBER attribute for use with Cube
			int count = 1;
			for (String matName : omxFile.getMatrixNames()) {
				count = count + 1;
			}
			
			//add matrix to file
			OmxMatrix.OmxDoubleMatrix mat = new OmxMatrix.OmxDoubleMatrix(name,valuesDouble,defaultNA);
			omxFile.addMatrix(mat);
			mat.setAttribute("CUBE_MAT_NUMBER",count);
			
			//add external zone numbers as NO lookup
			if (!omxFile.getLookupNames().contains("NO")) {
				OmxLookup.OmxIntLookup omxZoneNums = new OmxLookup.OmxIntLookup("NO", m.getExternalColumnNumbersZeroBased(), 0);
				omxFile.addLookup(omxZoneNums);
			}
			
			//save file			
			omxFile.save();

		} catch (Exception e) {
			throw new MatrixException(e, MatrixException.ERROR_WRITING_FILE);
		}
	}

	/** Writes all tables of an entire matrix
	 *
	 */
	public void writeMatrices(String[] names, Matrix[] m) throws MatrixException {
		for(int i=0; i<names.length; i++) {
			writeData(names[i],m[i]);
		}
	}

}