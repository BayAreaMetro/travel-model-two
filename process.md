
---
layout: page
title: Modeling Process
---

*Work in Progress*

# Modeling Process

1. `preprocess\zone_seq_net_builder.job`
   * summary: Builds a sequential zone numbering system for TAZs, MAZs, TAPs and Externals 
     given the [node number conventions](/travel-model-two/guide/#County-Node-Numbering-System).
   * input: _hwy\mtc_final_network_base.net_
   * output:
     1. _hwy\mtc_final_network.net_ with additional link attributes, _TAZSEQ_, _MAZSEQ_, _TAPSEQ_ and _EXTSEQ_
     2. _hwy\mtc_final_network_zone_seq.csv_ with columns _N_, _TAZSEQ_, _MAZSEQ_, _TAPSEQ_ and _EXTSEQ_
     
1. `preprocess\zone_seq_disseminator.py` 
   * summary: Builds other files with zone numbers
   * input: _hwy\mtc_final_network_zone_seq.csv_
   * output:
   *  1. _landuse\taz_data.csv_
   *  2. _landuse\maz_data.csv_
   *  3. _CTRAMP\model\ParkLocationAlts.csv_ - park location alternatives,  *TODO*: What are these? Move this from _CTRAMP_
   *  4. _CTRAMP\model\DestinationChoiceAlternatives.csv_ - destination choice alternatives. *TODO*: what are these?  Move this from _CTRAMP_
   *  5. _CTRAMP\model\SoaTazDistAlternatives.csv_  *TODO*: what are these?  Move this from _CTRAMP_
   *  6. _CTRAMP\model\ParkLocationSampleAlts.csv_  *TODO*: what are these?  Move this from _CTRAMP_
