## Calibration Documentation
In progress -- Calibration is evolving

#### General Outline of Mode Choice Calibration:
1. Process onboard survey data to determine tour level targets with _processOBSDataBase.R_ and _create_mode_choice_target_inputs.ipynb_.
2. Input the result (_obs_mode_choice_input.csv_) into _Calibration Mode Choice Targets 2015 with TNC.xlsx_ which combines TNC data, CHTS data, and transit data to create targets.
3. Copy targets to Tour and Trip mode choice calibration spreadsheets: _TourMode_Calibration_with_TNC.xlsx_ and _TripMode_Calibration_with_TNC.xlsx_
4. Run the model and visualizer to produce tour and trip mode summary files, _tmodeProfile_vis.csv_ and _tripModeProfile_vis.csv_ respectively.  Copy the data from these csv's into the calibration spreadsheets input page.
5. Copy old coefficients from UEC's into spreadsheets and copy adjusted coefficients back into UEC.

#### Auto Ownership and Work Destination County Level Calibration:
1. Run the _zero_auto_coef_changes.ipynb_ to calculate auto ownership calibration constants (both regionally and by district for zero auto households)
2. Copy the data from  _into county_flows_calibration.xlsx_ to calculate worker flow calibration constants by county.
3. (optional) Use the _coef_change_helper.xlsx_ spreadsheet to help format calibration constants for the corresponding UECs.
