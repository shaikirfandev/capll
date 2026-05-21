# CANoe Project Workspace

This folder mirrors a production CANoe bench project layout.

```text
CANoe_Project/
  Databases/MG_Hector_IVI_Training.dbc
  CAPL/RestBus_BCM_VCU_TCU.can
  CAPL/SWC_Simulator.can
  CAPL/ReverseCamera_Test.can
  CAPL/DiagnosticsSmoke.can
  Diagnostics/IVI_UDS_Service_Map.csv
  Panels/PANEL_DESIGN.md
  SystemVariables/MGH_IVI_SystemVariables.vsysvar
  TestModules/Regression_Test_Module.can
  Logs/README.md
```

## CANoe Build Steps

1. Create a new CANoe configuration named `MGH_IVI_Bench.cfg`.
2. Add one CAN network named `InfoCAN` at 500 kbit/s.
3. Attach `Databases/MG_Hector_IVI_Training.dbc`.
4. Add CAPL nodes for BCM/VCU/TCU rest bus, SWC, reverse camera checks and diagnostics smoke.
5. Import system variables from `SystemVariables`.
6. Build panels from `Panels/PANEL_DESIGN.md`.
7. Enable BLF logging and export XML test reports.
