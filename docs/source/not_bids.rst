.. _not_bids:

--------------------------------------
Non-BIDS (TIGRLAB-specific) Pipelines
--------------------------------------

TIGR-PURR also supports non-BIDS compliant pipelines specifically for TIGRLAB's use-cases centered around the `Datman <https://www.github.com/tigrlab/datman>`_ system.


The scripts::

        feenics.nf
        fieldmaps.nf

Can only be run in files organized according to the DATMAN hierarchy of studies and sessions. 

FeenICS
========

`FeenICS <https://www.github.com/tigrlab/feenics>`_ was developed in order to address a particular artifact related to SPIRAL acquisitions in k-space. It was originally developed by Erika Ziraldo, Dr. Sofia Chavez, Dr. Erin Dickie and Dr. Nancy Lobough. This pipeline was then adapted to TIGR-PURR which will regularly produce outputs for all the legacy spiral scans at TIGRLAB. 

FieldMaps
==========

The Fieldmap pipeline was designed to compute fieldmaps from the multi-echo scans acquired for the SPINS study as well as its derivatives. This pipeline was originally developed by Dr. Sofia Chavez specifically for CAMH GE scans.
