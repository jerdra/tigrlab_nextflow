.. _setup_guide:

--------------------
TIGR-PURR Installation and Configuration
--------------------

This is a detailed instructional on how to configure TIGR-PURR for your system. For a minimal walkthrough of TIGR-PURR setup using an example BIDS-application see the :ref:`minimal_setup`.


Installation
============

Since TIGR-PURR's main BIDS-app functionality relies heavily on the use of Singularity containers to deploy jobs, the installation requirements are minimal. TIGR-PURR requires the user to be inside a :code:`Python 3.6+` environment with :code:`boutiques>=0.5.25`. A `requirements.txt <https://github.com/jerdra/TIGR_PURR/blob/master/requirements.txt>`_ file is provided. Minimal set-up can be done via the following:

.. code-block:: bash

        git clone https://github.com/jerdra/TIGR_PURR.git
        cd TIGR_PURR
        pip install -r requirements.txt
        curl -s https://get.nextflow.io | bash

`Singularity <https://sylabs.io/guides/3.0/user-guide/quick_start.html>`_ is an additional requirement. If using a compute system you will need to ask the System administrator to install singularity. If using locally, then please follow the documentation provided on Singularity's website

Boutiques
====================

TIGR-PURR uses `Boutiques <https://boutiques.github.io>`_ in order to provide a homogenous command-line interface for running BIDS applications. When constructing a **Boutiques Invocation file the following paths must be used**

.. code-block:: json

            {
                "<bids_dir_arg>":"/bids",
                "<output_dir_arg>":"/output",
                "<work_dir_arg>":"/work",
                "<freesurfer_license_file_arg>":"/license",
                "<more_args>":"..." 
            }

TIGR-PURR by default binds the aforementioned directories to a fixed set of mounting points within any Singularity container called.


Not sure where to start with **Boutiques Descriptors and Invocations**? The `TIGRLab's Boutiques Repository <https://github.com/TIGRLab/boutiques_jsons/>`_ provides examples and files that can be used regardless of which system you're using.


Configuration
==============

The main script provided by TIGR-PURR is `bids.nf`, this script provides the core routines that enables any BIDS-app job to be deployed to the compute cluster of your choice. `bids.nf` reads a number of configuration files that can be found in the `config/` directory in order to specify:

- Which pipeline to run
- The cluster configuration options for a given pipeline
- Settings to specify how to deploy pipeline jobs to a cluster
- How to structure the generated HTML report's filename

The following sections provide information needed to configure TIGR-PURR on new clusters or to extend TIGR-PURR with new BIDS pipelines:

- :code:`_config_setup` - a dive into how TIGR-PURR is configured - it's simple!
- :code:`_cluster_config_`  - setting up TIGR-PURR to run on additional compute infrastructures
- :code:`_pipeline_extensions_` - adding new BIDS-app pipelines to TIGR-PURR


Thanks to Nextflow, the configuration for TIGR-PURR is incredibly simple. In this section we show how `bids.nf`, the core run-script of TIGR-PURR, reads configuration files for deployment onto compute clusters. The following configuration files are core to `bids.nf`:

- :code:`config/<pipeline>-<version>.nf.config` - the pipeline configuration file
- :code:`config/bids.nf.config` - core config file for all BIDS applications`
- :code:`config/profiles.nf.config` - cluster configuration file
- :code:`config/report_invocation.nf.config` - report generation configuration file

Pipeline configuration files provided in the `TIGR-PURR repository <https://github.com/jerdra/TIGR_PURR>`_ are of the form:

- :code:`config/<pipeline_name>-<pipeline_version>.nf.config`

.. note::
        TIGR-PURR can be extended to run additional BIDS-applications simply
        by creating new pipeline configuration files. See :ref:`pipeline_extensions`

.. note::
        `.nf.config` files are Groovy scripts and therefore allow for some light
        programming syntax to allow for dynamic configuration.

        The configuration required to set up a new cluster *does not require*
        knowledge of the Groovy syntax.



How do Configuration Files Link Together?
############################################

A core question is **how these configuration files are linked together when running `bids.nf`**? The basic workflow is as follows:

1. A user provides a pipeline configuration file (i.e :code:`fmriprep-1.3.2.nf.config`). This file sets a number of key variables required to configure a run of a pipeline
2. The pipeline configuration file *must include a line at the end* :code:`includeConfig './bids.nf.config'`, which loads :code:`bids.nf.config`. This in turn sets run-time variables that are accessible by :code:`bids.nf` of the form :code:`params.VARIABLENAME`. In addition :code:`bids.nf.config` loads in both the :code:`profiles.nf.config` and :code:`report_invocation.nf.config` files
3. The :code:`profiles.nf.config` finalizes the :code:`params.VARIABLENAME` values and in addition provides the cluster profiles that are selected by the :code:`-profile` command-line argument.
4. The :code:`report_invoction.nf.config` then sets configuration for how the HTML reports generated by Nextflow.


We describe the roles and requirements of the core configuration files in the following sections.

.. _pipeline_config:
.. _pipeline_extensions:

Pipeline Configuration File
############################

The :code:`<pipeline_name>-<pipeline_version>.nf.config` provides a number of settings which tells TIGR-PURR which pipeline to launch and with which arguments. The configuration file has the following structure (this is from `config/TEMPLATE.nf.config`):

.. code-block:: groovy

                application="Name of application being run"
                version="Version of pipeline"

                simg="Default Singularity image to use"
                invocation="Default Boutiques invocation JSON to use"
                descriptor="Default Boutiques descriptor JSON to use"

                cluster_time="Expected run-time of cluster"
                cluster_mem_cpu="MB of memory required per pipeline run"
                cluster_cpus="Number of CPUs required per pipeline run"

                includeConfig '<path to tigr-purr config>'/bids.nf.config'

To set up a *new pipeline* to run on TIGR-PURR, all that is needed is a configuration file that follows the above template.


Dynamic time allocation with `cluster_time`
********************************************

BIDS-applications may vary their run-time based on the number of sessions (i.e Freesurfer Longitudinal). As a result :code:`cluster_time` is allowed some flexibility, allowable values are:

- A constant :code:`string` value representing the time required (i.e "24:00:00")
- A Groovy :code:`closure` function of form :code:`{ s -> ... }`

In the latter case :code:`s` represents the number of sessions for a given BIDS subject. This can be used to scale the run-time based on the number of sessions within a subject's BIDS folder. For example:

.. code-block:: groovy

        cluster_time = { s-> return "${24*s}:00:00" }

Here :code:`cluster_time` scales such that each session within a subject folder adds 24 hours to the total run-time of the pipeline *for a given subject*. This means you can heterogeneously configure pipeline job submissions at the subject level


.. _bids_config:

Core Configuration File
########################

The core configuration file plays a simple role in the deployment of :code:`bids.nf` jobs:

1. Sets variables that are accessible by :code:`bids.nf` as :code:`params.VARNAME` options (i.e :code:`params.cluster_time`)
2. Loads in :code:`profiles.nf.config` which provides the profiles used for the :code:`-profile` command-line argument
3. Loads in :code:`report_invocation.nf.config` which configures the HTML reports
4. Sets the :code:`clusterOptions` for job submission derived from the pipeline configuration file

For the most part this file will not need to be modified.

.. note::
        Nextflow configuration variables starting with :code:`params` are overrideable
        in a command-line call. This is how the default invocation file can be
        overrided using :code:`--invocation`!

.. _cluster_config:

Deployment Configuration
#########################

The :code:`profiles.nf.config` file provides the ability to set up profiles referenced by the :code:`-profile` command-line option. The following scope is defined in :code:`profiles.nf.config`:

.. code-block:: groovy

            profiles {

                profile_1{
                ...
                }

                profile_2{
                ...
                }

             }

Additional profiles can be added by specifying an additional profile under :code:`profiles`. Each :code:`profile` scope has access to :code:`params.VARNAME` variables and thus can modify them before being finally read by :code:`bids.nf`.


:code:`profiles.nf.config` allows one to set configuration options that are specific to a given :code:`-profile`. :code:`bids.nf` explicitly and requires :code:`params.cluster_queue` to be set in order to determine which partition/queue to submit to when running BIDS applications.


The :code:`params.cluster_queue` option
***************************************

:code:`params.cluster_queue` must be of type of Groovy :code:`closure` of the form:

.. code-block:: groovy

            params.cluster_queue = { t -> ... }

The :code:`t` parameter passed in is :code:`params.cluster_time`. This can be used to implement flexible selection of cluster partitions based on the time requested. :code:`profile.nf.config` provides a helper function :code:`get_queue` which can be used with a :code:`dictionary`. Here's an example usage:

In :code:`profile.nf.config`:

.. code-block:: groovy

            // Define mapping table
            partition_map = ["12:00:00": "short",
                             "1:00:00:00": "medium",
                             "2:00:00:00": "long"]

            params.cluster_queue = { t -> get_queue(params.cluster_time(t),
                                                    partition_map) }

Here, :code:`partition_map` provides a table of upper time-limits to a set of partition.

The :code:`get_queue` function provided in :code:`profile.nf.config` picks the partition that minimally meets the time requirements of the task ( i.e a task requiring 22:00:00 would be assigned to :code:`medium`, not :code:`long`).


.. note::
        A :code:`closure` must be used because :code:`params.cluster_time` is not determined until
        run-time

.. note::
        In fact, *any* :code:`params` variable can be injected into the :code:`closure` so that :code:`queue`
        selection can depend on variables such as the :code:`params.cluster_cpus` or
        :code:`params.cluster_mem` variables.

        Advanced users may wrap their configuration in as many functions as they'd like
        to automate configuration. However, it is often better to keep configuration
        as simple as possible by usng dynamically configured parameters sparingly.

        An overly-complex configuration file may give rise to un-intended side-effects.

        See `Nextflow Configuration <https://www.nextflow.io/docs/latest/config.html>`_
        for more technical details on :code:`.nf.config` configuration files


.. _minimal-setup:

