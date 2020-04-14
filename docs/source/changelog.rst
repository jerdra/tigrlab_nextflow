.. _changelog:

--------------------
Changes
--------------------

v1.0.1
====================

- [ENH] Switch to using ANSI supported logging instead of println utility in bids.nf
- [ENH] Filter subjects based on existing output directories to bids.nf
- [ENH] Add --rewrite option to bids.nf allowing for override of subject filtering
- [ENH] Invalid subjects list are now pushed to pipeline-specific logging directory
- [ENH] FeenICS pipeline (feenics.nf) implement gzip to mitigate issues with FSL auto-zipping
- [ENH] Implement orientation fix via scraping mri_info of freesurfer on each sprl scan prior to FeenICS
- [ENH] FeenICS now outputs logs in a consistent manner to bids.nf
- [ENH] FeenICS will filter already existing output directories
- [ENH] FeenICS can run on SCC/Kimel/Local
- [ENH] FeenICS now has profile configurations set up to submit on Kimel/Local/SCC
- [FIX] FeenICS will combine spiral scans after artifact removal
- [ENH] FeenICS strategy switched to ignore after failures to allow ICArus processing
- [ENH] Fieldmap pipeline added for computing fieldmaps on CAMH GE scans (TIGRLAB internal)
- [ENH] Fieldmap pipeline outputs JSON sidecar into output folder containing units (CAMH GE specific!)
- [DOC] Updated TIGR-PURR documentation for non-BIDS internal pipelines
- [FIX] FeenICS had bug associated with uncontrolled file naming, issue is resolved
