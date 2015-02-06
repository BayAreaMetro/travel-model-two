
---
layout: page
title: Guide
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
