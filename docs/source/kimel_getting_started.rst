.. _kimel_getting_started:

--------------------
KIMEL Lab User's Guide
--------------------

In this section, we'll begin with where you can find regularly running standard BIDS pipelines. Then we will discuss how you can run your own standard pipeline (for example if you wanted outputs for a specific dataset quickly, although careful with space usage!). Finally we'll go over how you can customize arguments for either the BIDS application you want to run or SLURM if your requirements are more complex. 


Default Pipelines
============================

The **Default Pipelines** are defined as being any BIDS pipelines that are run with our internal (study-specific) settings. Any data that you find in the Kimel ``archive`` will have been run through using a **Default Pipeline**, which can be found in::

        /archive/data/<PROJECT>/pipelines/bids_apps/

These outputs will be automatically produced at regular intervals (depending on the pipeline). Outputs that are automatically run will be pushed into this directory. The particular participants that are run at any given time are those that are found in the **BIDS directory** in our archive which is found in::
        
        /archive/data/<PROJECT>/data/bids/

Each pipeline will contain its own subfolder here and the outputs contained within this subfolder are specific to the pipeline. For example::

        /archive/data/SPINS/pipelines/bids_apps/freesurfer/

Contains outputs from the `Freesurfer BIDS-app <https://github.com/BIDS-Apps/freesurfer>`_. The organization of the contents in this folder are specific to the Freesurfer BIDS-app and not anything specific to TIGRLab. If you have any questions about these outputs consult the user guide of the BIDS application of interest. If you still have questions then the Kimel Staff Team would be a good resource for more details.

Running your own Default Pipeline
====================================

Running your own default pipeline is simple with our set-up. First open up a terminal, then type in::

        module load nextflow/20.10.0


.. note::
        If you're on the SCC you will need to append /KIMEL/tigrlab/ to all paths in this guide. In addition you will need to load in the Kimel module system before loading in nextflow. First type in::

                module load /KIMEL/quarantine/modules/quarantine

        Then proceed with loading in nextflow as stated above. 

This loads in `Nextflow <https://nextflow.io>`_ and `Boutiques <https://boutiques.github.io>`_ which is required by TIGR-PURR. Once this module is loaded in you're ready to go! To run a pipeline some details are needed:

1. Your output directory
2. The BIDS folder that you'd like to run a pipeline on
3. A **Nextflow Configuration** file specifying which pipeline to run.


The **Nextflow Configuration** file is a short specification file which tells our pipeline system:

a. Which pipeline should be run
b. How to submit the job to SLURM (across different systems) if needed.

**Default Pipeline** configuration files will always be found in::

        /archive/code/TIGR_PURR/nextflow_config

Here you will find a bunch of files that look like the following::

        fmriprep-1.3.2.nf.config
        fmriprep_ciftify-1.3.0-post2-2.3.1.nf.config
        freesurfer-6.0.1.nf.config
        mriqc-0.14.2.nf.config

Every **Nextflow Configuration** file ends with a ``*.nf.config`` and always begins with ``<bidsapp>-<version>``. This way you know exactly which version of a pipeline you're running!

Let's say we want to run the ``mriqc-0.14.2`` pipeline. Then running the pipeline is done with the following command::

        nextflow /archive/code/tigrlab_nextflow/bids.nf \
        -c /archive/code/tigrlab_nextflow/nextflow_config/mriqc-0.14.2.nf.config \
        --bids <bids_dir> --out <output_dir> 


This will automatically submit SLURM jobs to the local Kimel cluster and run the **Default** MRIQC pipeline on the specified BIDS dataset. Note that this will run *all* BIDS subjects within the folder.

.. note::
        If you want to run nextflow in the background, add the argument::
                
                -bg


.. _clean:

Cleaning the Nextflow Work folder
==================================

When you run::
        
        module load nextflow/20.10.0
       
A folder is automatically created in ::

        /scratch/<YOUR_NAME>/nextflow_work/

This is a work directory used by nextflow to store intermediate outputs to pipelines. For most of our pipelines running BIDS-applications, not much will be stored here since all bids-apps are configured to use either /tmp/ (on kKimel) or /export/ramdisk (on SCC). However it is important that you clean out this folder periodically as it will continue building up as you use TIGR-PURR. To help you out with this we've built-in a function with the module::

        clean_nxf
        
Which will wipe the contents of your nextflow working directory. 

.. warning::

        Do not run `clean_nxf` when your pipeline is running! It may cause the pipeline to error out!

Running BIDS-apps with Custom Arguments
==============================================

You probably have noticed that no where in the call to nextflow did we specify which BIDS arguments to use when running it. This is because the **Default Pipelines** use a *default set of arguments for each BIDS application*. You can find these arguments here::

        /archive/code/boutiques_jsons/invocations/

In here you'll see a list of ``*.json`` files. Each one stores the default arguments for the associated BIDS application. So when you're using::

        mriqc-0.14.2.nf.config

Then the default JSON file it uses is::

        mriqc-0.14.2_invocation.json

Under the hood, what's actually being called is::

        nextflow /archive/code/tigrlab_nextflow/bids.nf \
        -c /archive/code/tigrlab_nextflow/nextflow_conf/mriqc-0.14.2.nf.config \
        --bids <bids_dir> --out <output_dir> \
        --invocation /archive/code/boutiques_jsons/invocations/mriqc-0.14.2_invocation.json

This means that you can specify any JSON file using the flag ``--invocation`` with an **invocation JSON** as an argument.

.. note::
        When using your own **invocation JSON** you will need to create your own file and place it in your own directory.
       
     A good practice regarding using your own **invocation JSON** is to store it alongside the code that will use the outputs of the pipeline with a file-name that contains the pipeline name and version. That way when you version-control your code (which you should be using) *the invocation JSON will also be stored!*

Invocation JSONS are essentially command-line arguments packed neatly into a JSON file. This explicitly stores the arguments you used for a pipeline so that you can remember what exactly you ran if you need to reproduce outputs of a pipeline or want to incorporate more subjects when running a pipeline. TIGR-PURR uses `Boutiques <https://www.boutiques.github.io>`_ under the hood which handles these JSON files and translates them to command-line calls.

Opening it up reveals what's actually being fed into MRIQC::

        {
                        "bids_dir":"/bids",
                        "analysis_level":"participant",
                        "output_dir":"/output",
                        "n_procs":4,
                        "fd_thres":0.5,
                        "modalities":["T1w"],
                        "verbose_count":"-v",
                        "verbose_reports":true
        }

Each **key:value** pair here corresponds to an argument for MRIQC. Where the  **value** part says "true" is a boolean flag. For example ``verbose_reports`` directly translates to ``--verbose-reports`` when calling MRIQC. A few things to note here:

1. The names of each argument are *ever-so slightly different*, (e.g: ``verbose_reports`` vs ``--verbose-reports``)
2. Any arguments which take a **list of inputs** is specified using a JSON list ``["a","b",...]``
3. The ``bids_dir`` and ``output_dir`` will *always be* ``/bids`` and ``/output`` respectively. This is because when you run the nextflow command, we're actually running everything inside Singularity containers.

While caveats (2) and (3) are relatively easy to reconcile. (1) is a bit harder to swallow, the reason being is that typically the BIDS-app developer or the developers of Boutiques make this decision - we just pull this format directly from them.

If you wanted to run MRIQC with your own custom arguments then you'll need to make JSON file similar to the one above by consulting the **descriptor JSON** file. These can be found in::

        /archive/code/boutiques_jsons/descriptors/

.. note::
        You will never need to write one of these yourself!

These descriptors fully describe the input structure to the provided BIDS application. For the purposes of making your own **invocation JSONS**, you can figure out which **keys** to use with the following command::


        bosh pprint mriqc-0.14.2.json

This will print the full description of the inputs to the BIDS application::

          optional arguments:
          --version [VERSION]   ID: version
                                Value Key: [VERSION]
                                Type: Flag
                                List: False
                                Optional: True
                                Description: show program's version number and exit
          --participant_label [PARTICIPANT_LABEL]
                                ID: participant_label
                                Value Key: [PARTICIPANT_LABEL]
                                Type: String
                                List: True
                                Optional: True
                                List Length: N/A
                                Description: one or more participant identifiers (the sub- prefix can
                                be removed)
          --session-id [SESSION_ID]
                                ID: session_id
                                Value Key: [SESSION_ID]
                                Type: String
                                List: True
                                Optional: True
                                List Length: N/A
                                Description: filter input dataset by session id
                              
          ...

          required arguments:
          [BIDS_DIR]            ID: bids_dir
                                Value Key: [BIDS_DIR]
                                Type: File
                                List: False
                                Optional: False
                                Description: The directory with the input dataset formatted according
                                to the BIDS standard.
          [OUTPUT_DIR]          ID: output_dir
                                Value Key: [OUTPUT_DIR]
                                Type: String
                                List: False
                                Optional: False
                                Description: The directory where the output files should be stored. If
                                you are running group level analysis this folder should be
                                prepopulated with the results of theparticipant level analysis.
          {participant,group}   ID: analysis_level
                                Value Key: [ANALYSIS_LEVEL]
                                Type: String
                                List: False
                                Optional: False
                                Description: Level of the analysis that will be performed. Multiple
                                participant level analyses can be run independently (in parallel)
                                using the same output_dir.



The right-hand side contains the MRIQC command-line argument and the left-hand side contains information about the command-line argument. The following info will help you make your **invocation JSON**:

1. ``ID`` this is the **key** for the associated argument. This is what you use in your JSON
2. ``List`` if true, that means the command-line argument takes multiple inputs. In your JSON you should specify this like ``["a","b",...]``.
3. ``Description`` this is a description of what the command-line argument does in the BIDS app


Now you can create your own custom **invocation JSON** using your favourite code editor. If you want to use it on a BIDS dataset using TIGR-PURR, then simply supply the JSON using the ``--invocation`` flag like follows::

        nextflow run /archive/code/tigrlab_nextflow/bids.nf \
        -c /archive/code/tigrlab_nextflow/nextflow_conf/mriqc-0.14.2.nf.config \
        --bids <BIDS> --out <OUT> \
        --invocation <PATH_TO_YOUR_JSON>

This will run the pipeline using your own custom command-line arguments!


Running Only Specific Subjects
===============================

If you wanted to run only a subset then you'll need to supply a subject list text file. For example if you make a file called ``sublist.txt`` with the following content::

        sub-CMH0144
        sub-MRP0136
        sub-MRC0021

You can run only these subjects by adding the ``--subjects`` flag to the nextflow call::

        nextflow /archive/code/tigrlab_nextflow/bids.nf \
        -c /archive/code/tigrlab_nextflow/nextflow_conf/mriqc-0.14.2.nf.config \
        --bids <bids_dir> --out <output_dir> \
        --subjects sublist.txt


.. _note:
        
        If your subject list contains invalid subjects, subjects for which no BIDS directory exists, a list of invalid subjects will be outputted into ``<output_dir>/pipelines_logs/invalid_subjects.log``

That's it! Now you might be wondering **what exactly did I run with MRIQC?**


.. _invocation:


Making Pipeline Run Reports
=============================

Nextflow has the ability to add pipeline HTML reports which gives you information about CPU usage, memory usage, failed processes, and run-time. This is useful to get a complete overview of your pipeline. TIGR-PURR automatically generates a report for you in the directory specified by `--out`. The file will look like:

        <INVOCATION_FILE_NAME>_<DATE-OF-RUN>.html.[#OFRUNSSINCECURRENT]

So for example, if the day is `2020-12-30` and you ran the default MRIQC pipeline which uses `--invocation mriqc-0.14.2_invocation`, then you should expect to see the following `.html` file in your `--out` directory:

        mriqc-0.14.2_2020-12-30.html

If you ran the MRIQC pipeline more than once on `2020-12-30`, then Nextflow renames the last run to `mriqc-0.14.2_2020-12-30.html.1`. The newest file will *never* contain the `.#` suffix, older runs always get renamed.


.. note::
        
        Good practices for saving reports are to save it into the same folder as your pipeline output. In addition the name of the report should ideally be descriptive of the pipeline you are running (pipeline, version, timestamp, etc..)

For more information on Nextflow reports check out the `Nextflow Reference Documentation <https://www.nextflow.io/docs/latest/tracing.html>`_



Pipeline Logging
====================

When running pipelines often it is desirable to have logs available for each subject in case there are issues with particular participants being run through. Logs are always stored in the output directory that you specify under a folder called ``pipeline_logs/<application_run>`` which contains two types of files named as::

        <subject>.out
        <subject>.err

These are the **standard output** and **standard error** of the processes run respectively and store what would have been outputted to your terminal had you directly run the pipeline without TIGR-PURR (albeit wrapped using Boutiques). 

If you are familiar with using `SLURM's <https://slurm.schedmd.com/>`_ sbatch command, then this will be exactly the outputs that SLURM produces.


.. _profiles:

Running Pipelines on Other Systems (SCC/Scinet/Local)
=====================================================

The default system that TIGR-PURR will run on is on the local Kimel cluster. In the Kimel Lab if you're using an external open-source dataset such as HCP, it is recommended that you perform pre-processing using Scinet. If you're running internal study datasets (found in ``/archive/data/``), then you could use either your local computer, the SCC, or the local Kimel cluster. Specifying which system to run on is done using the ``-profile`` flag. The following options are available:

1. ``-profile local`` - this will run locally on your computer
2. ``-profile kimel`` - this will run on the Kimel Cluster [DEFAULT]
3. ``-profile scc`` - this will run on CAMH's SCC


For example::

        
        nextflow run /KIMEL/tigrlab/archive/code/tigrlab_nextflow/bids.nf \
        -c /KIMEL/tigrlab/archive/code/tigrlab_nextflow/nextflow_conf/mriqc-0.14.2.nf.config \
        --bids <BIDS> --out <OUT> \
        -profile scc

Will run pipelines on the SCC.

.. note::
        In order to run pipelines on the SCC *you must be on the SCC dev node!*. 
        
        Also note that /KIMEL/tigrlab/ is added to the paths to our filesystem, this is necessary!

.. note::
        Because of the unique requirements surrounding niagara usage (every job must use 40 cores/node) running our TIGRLab pipelines isn't currently supported. We're currently working on building infrastructure to handle these sorts of requirements. The documentation will be updated as soon as the ``-profile niagara`` feature is available!

Customizing SLURM Directives (Advanced)
=========================================

SLURM directives (options with which to tell SLURM how to allocate for your job) are stored explicitly in the nextflow configuration file. For example, when using the MRIQC pipeline you specify::

        -c /archive/code/tigrlab_nextflow/nextflow_conf/mriqc-0.14.2.nf.config


This configuration file contains all the information needed to submit a job. If you take a look at this file there is a section with the following specification::

        process {
                withName: run_bids {
                        maxErrors = 3
                        errorStrategy = {task.attempt = task.maxErrors ? "retry" : "ignore" }
                        clusterOptions = "--time=4:00:00 --mem-per-cpu=2048\
                                          --cpus-per-task=4 --job-name mriqc_pipeline\
                                          --nodes=1"
               }
        }

The tidbit with ``clusterOptions`` is equivalent to the command-line arguments used in SLURM's ``sbatch`` command. Therefore you can simply copy and paste this configuration file, and update ``clusterOptions`` as you please. 

.. note::
        We're currently working on a method to allow you to override this without having to make a new
        Nextflow configuration file. Using either command-line arguments or a text file containing 
        SLURM directives. The documentation will be updated when this feature is released
