.. tigrlab_nextflow documentation master file, created by
   sphinx-quickstart on Mon Jul  8 12:26:36 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

TIGRLab Pipelines: Utterly Reproducible Research (TIGR-PURR)
============================================================


Welcome to the documentation page for TIGR-PURR.
This is where you'll find information about how to run the lab's supported pipelines yourself as well as the various configuration options available to you. 

TIGR-PURR is a pipeline system based off a combination of `Nextflow <https://www.nextflow.io>`_ and `Boutiques <https://www.boutiques.github.io>`_ which allow us to seamlessly run a variety of `BIDS Applications <https://bids.neuroimaging.io>`_ based distributed pipelines easily with only a little bit of configuration work. The system will allow you to run full BIDS-app pipelines on:

* The local Kimel-Lab Cluster
* CAMH's SCC Cluster
* Scinet's Niagara Cluster
* Your local computer

To learn about how you can run BIDS pipelines on any BIDS dataset go to :ref:`getting_started`

To go through a quick example that you can run yourself, check out the quickstart tutorials.

.. toctree::
   :maxdepth: 2
   :caption: Contents 

   getting_started
   quickstart_tutorial
   quick_reference
   not_bids
   features
   changelog
