#!/usr/bin/env python

import os
import sys
import argparse

import nibabel as nib

from nilearn.image import resample_to_img
from nilearn import image as img
from resample import ResampleTPM

from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu, fsl
from nipype.interfaces.fsl import FLIRT
from nipype.interfaces import io as nio
from nipype.algorithms import confounds as nac
from nipype.utils.filemanip import fname_presuffix
from nipype.interfaces.ants import ApplyTransforms

from niworkflows.engine.workflows import LiterateWorkflow as Workflow
from niworkflows.interfaces.confounds import ExpandModel, SpikeRegressors
from niworkflows.interfaces.fixes import FixHeaderApplyTransforms
from niworkflows.interfaces.images import SignalExtraction
from niworkflows.interfaces.masks import ROIsPlot
from niworkflows.interfaces.utility import KeySelect
from niworkflows.interfaces.patches import (RobustACompCor as ACompCor,
                                            RobustTCompCor as TCompCor)
from niworkflows.interfaces.utils import (TPM2ROI, AddTPMs, AddTSVHeader,
                                          TSV2JSON, DictMerge)

from templateflow.api import get as get_template


def main():

    parser = argparse.ArgumentParser(
        description='Extract confounds from WM and CSF')
    parser.add_argument('t1', type=str, help='T1 image')
    parser.add_argument('t1_mask', type=str, help='Binary brain mask')
    parser.add_argument('wm_tpm',
                        type=str,
                        help='White matter tissue probability map')
    parser.add_argument('csf_tpm', type=str, help='CSF tissue probability map')
    parser.add_argument('bold', type=str, help='BOLD image')
    parser.add_argument('bold_mask', type=str, help='BOLD mask')
    parser.add_argument('out_basename', type=str, help='Output file path with basename')
    parser.add_argument('--workdir',
                        type=str,
                        help='Path to use for workdir'
                        ' this path must already exist')

    args = parser.parse_args()
    t1 = args.t1
    t1_mask = args.t1_mask
    wm_tpm = args.wm_tpm
    csf_tpm = args.csf_tpm
    bold = args.bold
    bold_mask = args.bold_mask
    outbase = args.out_basename
    workdir = args.workdir

    # Set up confound workflow
    confound_dir = os.path.join(workdir, 'confound_wf')
    try:
        os.makedirs(confound_dir)
    except OSError:
        pass
    confound_wf = init_confound_wf(t1, t1_mask, wm_tpm, csf_tpm, bold,
                                   bold_mask)
    confound_wf.base_dir = confound_dir

    # Node to export file to destination directory
    ef_confounds = pe.Node(nio.ExportFile(), name='export_confounds')
    ef_confounds.inputs.out_file = f'{outbase}_confounds.tsv'

    ef_wm = pe.Node(nio.ExportFile(), name='export_wm')
    ef_wm.inputs.out_file = f'{outbase}_wm_roi.nii.gz'

    ef_csf = pe.Node(nio.ExportFile(), name='export_csf')
    ef_csf.inputs.out_file = f'{outbase}_csf_roi.nii.gz'

    # Set up wrapper workflow for export
    main_dir = os.path.join(workdir, 'main_wf')
    try:
        os.makedirs(main_dir)
    except OSError:
        pass
    wf = pe.Workflow(name='main_wf')
    wf.base_dir = main_dir
    wf.connect([
        (confound_wf, ef_confounds, [('outputnode.signals', 'in_file')]),
        (confound_wf, ef_wm, [('outputnode.wm_roi','in_file')]),
        (confound_wf, ef_csf, [('outputnode.csf_roi','in_file')])
        ])
    wf.run()


def init_confound_wf(t1, t1_mask, wm_tpm, csf_tpm, bold, bold_mask):
    '''
    Initialize the confound extraction workflow
    '''

    inputnode = pe.Node(niu.IdentityInterface(
        fields=['bold', 'bold_mask', 't1w_mask', 't1w', 'wm_tpm', 'csf_tpm']),
                        name='inputnode')

    inputnode.inputs.bold = bold
    inputnode.inputs.bold_mask = bold_mask
    inputnode.inputs.t1w_mask = t1_mask
    inputnode.inputs.t1w = t1
    inputnode.inputs.wm_tpm = wm_tpm
    inputnode.inputs.csf_tpm = csf_tpm

    wm_roi = pe.Node(TPM2ROI(erode_prop=0.6, mask_erode_prop=0.6**3),
                     name='wm_roi')
    resample_wm_roi = pe.Node(ResampleTPM(), name='resampled_wm_roi')

    csf_roi = pe.Node(TPM2ROI(erode_mm=0, mask_erode_mm=30), name='csf_roi')
    resample_csf_roi = pe.Node(ResampleTPM(), name='resampled_csf_roi')

    merge_label = pe.Node(niu.Merge(2),
                          name='merge_rois',
                          run_without_submitting=True)

    signals_class_labels = ["white_matter", "csf"]
    signals = pe.Node(SignalExtraction(class_labels=signals_class_labels),
                      name="signals")

    outputnode = pe.Node(niu.IdentityInterface(
        fields=['signals','wm_roi','csf_roi']),
                         name='outputnode')

    wf = pe.Workflow(name='confound_wf')
    wf.config['execution']['crashfile_format'] = 'txt'

    wf.connect([(inputnode, wm_roi, [('wm_tpm', 'in_tpm'),
                                     ('t1w_mask', 'in_mask')]),
                (inputnode, csf_roi, [('csf_tpm', 'in_tpm'),
                                      ('t1w_mask', 'in_mask')]),
                (inputnode, resample_wm_roi, [('bold_mask', 'fixed_file')]),
                (wm_roi, resample_wm_roi, [('roi_file', 'moving_file')]),
                (inputnode, resample_csf_roi, [('bold_mask', 'fixed_file')]),
                (csf_roi, resample_csf_roi, [('roi_file', 'moving_file')]),
                (inputnode, signals, [('bold', 'in_file')]),
                (resample_wm_roi, merge_label, [('out_file', 'in1')]),
                (resample_csf_roi, merge_label, [('out_file', 'in2')]),
                (merge_label, signals, [('out', 'label_files')]),
                (signals, outputnode, [('out_file', 'signals')]),
                (wm_roi, outputnode, [('roi_file', 'wm_roi')]),
                (csf_roi, outputnode, [('roi_file', 'csf_roi')])])

    return wf


if __name__ == '__main__':
    main()
