.. _minimal_setup:

Minimal Set-up Guide
======================

This section outlines a minimal set-up guide to get you up and running. We will be using `fmriprep LTS 20.2.0 <https://fmriprep.org/en/stable/>`_ as our BIDS application of choice in this example. Although adding new pipelines is as easy as setting up a new configuration file and obtaining the required singularity image.


1. Installation
#################

Install Python 3.6+ using the method of your choice. We recommend using python virtual environments such as:

- `virtualenv <https://pypi.org/project/virtualenv/>`_ 
- `pyenv <https://github.com/pyenv/pyenv>`_

To avoid conflicting with your system python install. Once you enter your virtual environment of choice:

.. code-block: bash

        git clone https://github.com/jerdra/TIGR_PURR.git
        cd TIGR_PURR
        pip install -r requirements.txt
        curl -s https://get.nextflow.io | bash
        cd ..

This will install both `Boutiques <https://boutiques.github.io>`_ and `Nextflow <https://nextflow.io>`_. Installation instructions for **Singularity** can be found `here <https://sylabs.io/guides/3.0/user-guide/quick_start.html>`_.

2. Boutiques Setup
#####################

Next we'll set up our Boutiques **invocations** and **descriptors**, pulling from `TIGRLAB's Boutiques Repository <https://github.com/tigrlab/boutiques_jsons>`_:

.. code-block:: bash

        git clone https://github.com/TIGRLab/boutiques_jsons.git

This will create a :code:`boutiques_jsons` directory containing both the :code:`invocations` and :code:`descriptors` directories required for running boutiques. As an example, the **Invocation** file we'll be using is :code:`boutiques_jsons/invocations/fmriprep-20.2.0_invocation.json` which looks as follows:

.. code-block:: json

        {
        "bids_dir": "/bids",
        "output_dir": "/output",
        "work_dir": "/work",
        "analysis_level": "participant",
        "fs_license_file": "/license/license.txt",
        "nprocs": 4,
        "omp_nthreads": 2,
        "verbosity": "-vv",
        "use_aroma": true,
        "use_syn_sdc":true,
            "output_spaces": ["T1w", "MNI152NLin2009cAsym", "fsaverage", "fsaverage5"]
        } 

The JSON keys correspond to fMRIPrep 20.2.0's command-line arguments (dashes replace with an underscore). Boutiques uses a **Descriptor JSON** file in order to translate **Invocation JSONS** into command-line arguments. The respective descriptor file for the above invocation is found in :code:`boutiques_jsons/descriptors/fmriprep-20.2.0.json`. 

.. note::

        *Every BIDS-app must have an associated descriptor for it to work*!
        Boutiques provides utilities to download descriptors for BIDS applications,
        see the Boutiques documentation for more details!

3. Obtaining the fMRIPrep-20.2.0 Container and its Requirements
#################################################################

Before we run TIGR-PURR, we'll need the fMRIPrep-20.2.0 singularity container and its sole requirement, a Freesurfer License file. The singularity container for fMRIPrep can be easily built with the following lines:

.. code-block:: bash

            mkdir singularity_images
            singularity build singularity_images/fmriprep-20.2.0.simg \
                              docker://nipreps/fmriprep:20.2.0

The Freesurfer License file required for fMRIPrep can be found `here <https://surfer.nmr.mgh.harvard.edu/fswiki/License>`_. Once the license is downloaded you may place it here:

.. code-block:: bash

            mkdir license
            mv <path_to_downloaded_license> license/


4. Configuring TIGR-PURR to Run fMRIPrep-20.2.0
###################################################

Only a few tweaks are needed to get fMRIPrep-20.2.0 up and running with TIGR-PURR! First we'll create the :code:`fmriprep-20.2.0.nf.config` file. First we'll copy the provided template file:

.. code-block:: bash

        cp TIGR_PURR/config/TEMPLATE.nf.config TIGR_PURR/config/fmriprep-20.2.0.nf.config

Next we'll fill in the missing fields:

.. code-block:: groovy

        application = "fMRIPrep"
        version = "20.2.0"

        simg = "<path_to_singularity_container>/fmriprep-20.2.0.simg"
        invocation = "<path_to_boutiques_jsons>/invocations/fmriprep-20.2.0_invocation.json"
        descriptor = "<path_to_boutiques_jsons>/descriptors/fmriprep-20.2.0.json"

        cluster_time="36:00:00"
        cluster_mem_cpu="2048"
        cluster_cpus="6"

        params.license = "<directory_with_license_file>/"
        
        includeConfig './bids.nf.config'

.. note::

    Remember that :code:`params.license` becomes a global variable that is
    accessible by the pipeline. TIGR-PURR will always attach the :code:`params.license`
    directory to :code:`/license` within the container. This is only required
    for BIDS application requiring a Freesurfer license file.


5. Configuring the execution of TIGR-PURR
##########################################

The final step is to configure the execution settings for TIGR-PURR in `profiles.nf.config`. For this example we'll use the :code:`local` profile. For setting up TIGR-PURR execution on `SLURM <https://slurm.schedmd.com/documentation.html>`_ systems please refer to and adapt the profiles already configured within :code:`profiles.nf.config`. Note the settings for the :code:`local` profile

.. code-block:: groovy

        local {
        
        // Don't use a cluster queue
        params.cluster_queue = {s->""}

        // The "local" executor means run on the local computer
        process.executor = "local"

        // Only launch 4 fMRIPreps simultaneously at a time
        process.maxForks = 4

        // Use the /tmp/ dir as the work directory
        params.scratchDir = "/tmp/"

    }

Comments are added to explain what each line is doing. Refer to the `Nextflow profiles documentation <https://nextflow.io/docs/latest/config.html#config-profiles>`_ for more information on how to set up your config profile.


.. note::
        Because TIGR-PURR uses Nextflow under the hood to management pipeline
        deployment it is possible to deploy pipelines to cloud computing
        infrastructures. 

        See the `docs <https://nextflow.io/docs/latest/>`_ for more information.


6. Launching fMRIPrep-20.2.0
#############################

Finally we can run fMRIPrep-20.2.0 on a BIDS dataset. If you don't already have a BIDS dataset you can find open-source datasets for use at `OpenNeuro <https://openneuro.org/>`_. Once obtained, fMRIPrep can be run with the following call:

.. code-block:: bash

            nextflow run TIGR_PURR/bids.nf -c TIGR_PURR/config/fmriprep-20.2.0.nf.config \
                                           --bids-dir <path_to_bids> \
                                           --out <path_to_output_dir> \
                                           -profile local

.. note::
            You can view the usage logs for :code:`bids.nf` using the :code:`--help` flag
