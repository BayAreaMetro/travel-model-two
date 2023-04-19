package com.pb.mtctm2.abm.application;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Set;
import java.util.TreeMap;

import org.apache.log4j.Logger;
import com.pb.common.datafile.TableDataSet;
import com.pb.common.datafile.CSVFileReader;

import com.pb.mtctm2.abm.ctramp.CtrampApplication;

public class NodeZoneMapping {
	public static final String NETWORK_NODE_SEQUENCE_FILE_PROPERTY = "network.node.seq.mapping.file";
	
	private final Map<Integer,Integer> originalToSequenceTaz;
	private final Map<Integer,Integer> originalToSequenceMaz;
	private final Map<Integer,Integer> sequenceToOriginalTaz;
	private final Map<Integer,Integer> sequenceToOriginalMaz;
	
	public NodeZoneMapping(Map<String,String> properties) {
		originalToSequenceTaz = new TreeMap<>();
		originalToSequenceMaz = new TreeMap<>();
		loadNodeSequenceData(Paths.get(properties.get(CtrampApplication.PROPERTIES_PROJECT_DIRECTORY) + properties.get(NETWORK_NODE_SEQUENCE_FILE_PROPERTY)));
		sequenceToOriginalTaz = reverseMap(originalToSequenceTaz);
		sequenceToOriginalMaz = reverseMap(originalToSequenceMaz);
	}
	
	private void loadNodeSequenceData(Path sequenceFile) {
		try {
			CSVFileReader csvReader = new CSVFileReader();
			TableDataSet nodeSeqTable = csvReader.readFile(sequenceFile.toFile());

			int[] nodeIds = nodeSeqTable.getColumnAsInt("N");
			int[] tazs    = nodeSeqTable.getColumnAsInt("TAZSEQ");
			int[] mazs    = nodeSeqTable.getColumnAsInt("MAZSEQ");

			System.out.println("tazs length= " + tazs.length);
			for(int i=0; i<nodeIds.length; i++) {
				if (tazs[i] > 0) { originalToSequenceTaz.put(nodeIds[i], tazs[i]); }
				if (mazs[i] > 0) { originalToSequenceMaz.put(nodeIds[i], mazs[i]); }
			}
			System.out.println("tazs size= " + originalToSequenceTaz.size());
			System.out.println("mazs size= " + originalToSequenceMaz.size());
			System.out.println("taz for node 200700: " + originalToSequenceTaz.get(200700));

        } catch (IOException e) {
        	throw new RuntimeException();
        }
	}

	private Map<Integer,Integer> reverseMap(Map<Integer,Integer> map) {
		Map<Integer,Integer> rmap = new TreeMap<>();
		for (Entry<Integer,Integer> entry : map.entrySet())
			rmap.put(entry.getValue(),entry.getKey());
		return rmap;
	}
	
	public int getSequenceTaz(int originalTaz) {
		return originalToSequenceTaz.get(originalTaz);
	}
	
	public int getSequenceMaz(int originalMaz) {
		return originalToSequenceMaz.get(originalMaz);
	}
	
	public int getOriginalTaz(int sequenceTaz) {
		return sequenceToOriginalTaz.get(sequenceTaz);
	}
	
	public int getOriginalMaz(int sequenceMaz) {
		return sequenceToOriginalMaz.get(sequenceMaz);
	}

	public Set<Integer> getOriginalTazs() {
		return originalToSequenceTaz.keySet();
	}

	public Set<Integer> getOriginalMazs() {
		return originalToSequenceMaz.keySet();
	}

	public Set<Integer> getSequenceTazs() {
		return sequenceToOriginalTaz.keySet();
	}

	public Set<Integer> getSequenceMazs() {
		return sequenceToOriginalMaz.keySet();
	}

}
