.. _kimel_quickstart_tutorial:


-------------------------------------------
TIGR-PURR Quickstart Tutorial for Kimel Lab Members
-------------------------------------------

This tutorial is meant to run you through a simple example of running TIGR-PURR pipelines on your computer using data from our internal SPINS study.

Please refer to :ref:`getting_started` for more detailed information about running TIGR-PURR pipelines.

Setting up the Quickstart Tutorial
=======================================

When we're running a TIGR-PURR pipeline the first thing to do is to organize your project directory. We'll do a simple folder in scratch with the following command::

        mkdir /scratch/<YOU>/nextflow_quickstart
        cd /scratch/<YOU>/nextflow_quickstart


.. note::
        If you want to go through this tutorial on the SCC you must add::

                /KIMEL/tigrlab/

        Before every path!

Next we'll make a text file containing a list of participants from the SPINS study. For this tutorial we'll only run a subset of participants since running all participants will take too much time::

        touch sublist
        
The sublist text file will contain a list of participants (one-per-line) that we want to run, enter the following into ``sublist``::

        sub-CMH0144
        sub-MRP0136
        sub-MRC0021

Finally, load in the **Nextflow** module::

        module load nextflow/20.10.0


.. note::
        If you're on the SCC you must load in our Kimel modules first before loading in nextflow::
                
                module load /KIMEL/quarantine/modules/quarantine

.. note::

        This will create a directory in::

                /scratch/<YOU>/nextflow_work/

        Which you should clean. For more information see :ref:`clean`



Dry-Runs of Pipelines
=================================================================

In this quickstart tutorial we'll be running a **Dry-run** of MRIQC on a bunch of participants from the SPINS study located in the archive. A dry-run is a way of running pipelines without doing actual computation. 


Running the pipeline
======================

Once you have a BIDS-app, subject list, and invocation ready to go you can run a pipeline! Let's run it on the local system (your own computer) first, but feel free to try other profiles!::

        nextflow /archive/code/tigrlab_nextflow/bids.nf \
                -c /archive/code/tigrlab_nextflow/nextflow_config/mriqc-0.14.2.nf.config \
                --bids /archive/data/SPINS/data/bids \
                --out /scratch/<YOU>/nextflow_quickstart \
                --subjects /scratch/<YOU>/nextflow_quickstart/sublist \
                --invocation /archive/code/boutiques_jsons/invocations/dryrun_mriqc-0.14.2_invocation.json \
                -profile local

The process will run the dry-run version of MRIQC in parallel automatically! 

.. note::
        Feel free to try different profiles like "kimel" or "scc". For more information on profiles see: :ref:`profiles`


Cleaning up your TIGR-PURR run
===============================

Once you're finished running a pipeline, you need to *clean out* the Nextflow working directory. By default the working directory is found by examining the ``$NXF_WORK`` environment variable::

        echo $NXF_WORK


To clean it out you can simply type in::

        clean_nxf


Which will clean out the subfolders in this directory.

.. note::
        For more information on cleaning working directories check out :ref:`clean`
