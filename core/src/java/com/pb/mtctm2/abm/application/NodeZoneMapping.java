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

import com.pb.mtctm2.abm.ctramp.CtrampApplication;

public class NodeZoneMapping {
	public static final String NETWORK_NODE_SEQUENCE_FILE_PROPERTY = "network.node.seq.mapping.file";
	
	private final Map<Integer,Integer> originalToSequenceTaz;
	private final Map<Integer,Integer> originalToSequenceMaz;
	private final Map<Integer,Integer> originalToSequenceTap;
	private final Map<Integer,Integer> sequenceToOriginalTaz;
	private final Map<Integer,Integer> sequenceToOriginalMaz;
	private final Map<Integer,Integer> sequenceToOriginalTap;
	
	public NodeZoneMapping(Map<String,String> properties) {
		originalToSequenceTaz = new TreeMap<>();
		originalToSequenceMaz = new TreeMap<>();
		originalToSequenceTap = new TreeMap<>();
		loadNodeSequenceData(Paths.get(properties.get(CtrampApplication.PROPERTIES_PROJECT_DIRECTORY) + properties.get(NETWORK_NODE_SEQUENCE_FILE_PROPERTY)));
		sequenceToOriginalTaz = reverseMap(originalToSequenceTaz);
		sequenceToOriginalMaz = reverseMap(originalToSequenceMaz);
		sequenceToOriginalTap = reverseMap(originalToSequenceTap);
	}
	
	private void loadNodeSequenceData(Path sequenceFile) {
		//hard coded the structure of the file, but it has no headers so we have to
		try (BufferedReader reader = new BufferedReader(new FileReader(sequenceFile.toFile()))) {
			String line;
			while ((line = reader.readLine()) != null) {
				line = line.trim();
				if (line.length() == 0)
					continue;
				String[] s = line.trim().split(",");
				int original = Integer.parseInt(s[0]);
				outer: for (int i = 1; i < s.length; i++) {
					int zone = Integer.parseInt(s[i]);
					if (zone > 0) {
						switch (i) {
							case 1 : originalToSequenceTaz.put(original,zone); break outer;
							case 2 : originalToSequenceMaz.put(original,zone); break outer;
							case 3 : originalToSequenceTap.put(original,zone); break outer;						
						}
					}
				}
			}
		} catch (IOException e) {
			throw new RuntimeException(e);
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
	
	public int getSequenceTap(int originalTap) {
		return originalToSequenceTap.get(originalTap);
	}
	
	public int getOriginalTaz(int sequenceTaz) {
		return sequenceToOriginalTaz.get(sequenceTaz);
	}
	
	public int getOriginalMaz(int sequenceMaz) {
		return sequenceToOriginalMaz.get(sequenceMaz);
	}
	
	public int getOriginalTap(int sequenceTap) {
		return sequenceToOriginalTap.get(sequenceTap);
	}

	public Set<Integer> getOriginalTazs() {
		return originalToSequenceTaz.keySet();
	}

	public Set<Integer> getOriginalMazs() {
		return originalToSequenceMaz.keySet();
	}

	public Set<Integer> getOriginalTaps() {
		return originalToSequenceTap.keySet();
	}

	public Set<Integer> getSequenceTazs() {
		return sequenceToOriginalTaz.keySet();
	}

	public Set<Integer> getSequenceMazs() {
		return sequenceToOriginalMaz.keySet();
	}

	public Set<Integer> getSequenceTaps() {
		return sequenceToOriginalTap.keySet();
	}

}
