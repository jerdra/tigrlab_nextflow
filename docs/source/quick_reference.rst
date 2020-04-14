.. _quick_reference:


----------------------------------------
Quick Reference Guide to Pipeline Usage
----------------------------------------

This is a quick reference guide to some information surrounding outputs of our default pipelines and how to use TIGR-PURR. 

Before running any TIGR-PURR pipeline please load the following module::

        python/3.6.3-boutiques-0.5.20


Default Pipeline Outputs
==========================
Default pipelines are defined as regularly running BIDS applications on our internal data stores found within::

        /archive/data/<PROJECT>

The outputs are stored in the following directory::

        /archive/data/<PROJECT>/pipelines/bids_apps/<BIDS_APPLICATION>


Running a Default Pipeline
===========================

You can run a default pipeline with the following lines::

        nextflow /archive/code/tigrlab_nextflow/bids.nf \
        -c /archive/code/tigrlab_nextflow/nextflow_conf/<bids_app>-<version>.nf.config \
        --bids <path_to_bids_dir> --out <path_to_output>

This will run *all* subjects within the BIDS folder

Running a subset of subjects
=============================

The ``--subjects`` flag allows you to specify a text-file containing **one subject per-line**::

        nextflow /archive/code/tigrlab_nextflow/bids.nf \
        -c <nextflow_config_file> \
        --bids <path_to_bids_dir> \
        --out <path_to_output> \
        --subjects <path_to_subject_list_text_file>

Using custom BIDS-app arguments
================================

Make an **invocation JSON** and supply it via the ``--invocation`` flag::

        nextflow /archive/code/tigrlab_nextflow/bids.nf \
        -c <nextflow_config_file> \
        --bids <path_to_bids_dir> \
        --out <path_to_output> \
        --invocation <path_to_invocation_json>

.. note::
        When making your own **invocation JSON** please version control it using Git!
        If you have questions ask the Kimel staff and they'll be more than happy to help you version control your invocation JSONs!

Running on other clusters
=================================

By default TIGR-PURR submits to high-moby jobs on the local Kimel cluster. To use other system such as the SCC, Niagara or your local computer use the ``-profile <system_name>`` flag::


        nextflow /archive/code/tigrlab_nextflow/bids.nf \
        -c <nextflow_config_file> \
        --bids <path_to_bids_dir> \
        --out <path_to_output> \
        -profile {scc,kimel,local}

.. note::
        Niagara will be supported in the future, we will update you when it's available!


Using custom SLURM directives
====================================
SLURM directives are fully captured by a **Nextflow Configuration File**. Check the ones in the archive as a reference::

        /archive/code/tigrlab_nextflow/nextflow_conf/

SLURM submission options are defined under::

        process {
                withName: run_bids {
                        clusterOptions=...
                        }
                }
        
.. note::
        You will need to create a copy of the config files from the archive. Please make sure you version-control your nextflow configuration options!

