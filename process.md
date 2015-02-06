---
layout: page
title: Modeling Process
---

*Work in Progress*

# Modeling Process

1. `preprocess\zone_seq_net_builder.job`
   * summary: Builds a sequential zone numbering system for TAZs, MAZs, TAPs and Externals 
     given the [node number conventions](/travel-model-two/guide/#County-Node-Numbering-System).
   * input: `hwy\mtc_final_network_base.net`
   * output:
     1. `hwy\mtc_final_network.net` with additional link attributes, _TAZSEQ_, _MAZSEQ_, _TAPSEQ_ and _EXTSEQ_
     2. `hwy\mtc_final_network_zone_seq.csv` with columns _N_, _TAZSEQ_, _MAZSEQ_, _TAPSEQ_ and _EXTSEQ_
     
1. `preprocess\zone_seq_disseminator.py` 
   * summary: Builds other files with zone numbers
   * input: `hwy\mtc_final_network_zone_seq.csv`
   * output:
     1. `landuse\taz_data.csv`
     2. `landuse\maz_data.csv`
     3. `CTRAMP\model\ParkLocationAlts.csv` - park location alternatives,  *TODO*: What are these? Move this from _CTRAMP_
     4. `CTRAMP\model\DestinationChoiceAlternatives.csv` - destination choice alternatives. *TODO*: what are these?  Move this from _CTRAMP_
     5. `CTRAMP\model\SoaTazDistAlternatives.csv`  *TODO*: what are these?  Move this from _CTRAMP_
     6. `CTRAMP\model\ParkLocationSampleAlts.csv`  *TODO*: what are these?  Move this from _CTRAMP_
