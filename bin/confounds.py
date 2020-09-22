#!/usr/bin/env python

import os
import argparse
import json

import nibabel as nib
import numpy as np

from resample import ResampleTPM

from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu
from nipype.interfaces import io as nio
from nipype.utils.filemanip import fname_presuffix

from niworkflows.interfaces.images import SignalExtraction
from niworkflows.interfaces.patches import (RobustACompCor as ACompCor,
                                            RobustTCompCor as TCompCor)
from niworkflows.interfaces.utils import (TPM2ROI, AddTPMs)
from niworkflows.interfaces.registration import _get_vols_to_discard


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
    parser.add_argument('bold_json', type=str, help='BOLD JSON metadat file')
    parser.add_argument('out_basename',
                        type=str,
                        help='Output file path with basename')
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
    bold_json = args.bold_json
    outbase = args.out_basename
    workdir = args.workdir

    # Get TR
    with open(bold_json, 'r') as j:
        metadata = json.load(j)

    # Extract the number of volumes to discard
    ref_im = nib.load(bold)
    skipvol = _get_vols_to_discard(ref_im)

    # Set up confound workflow
    confound_dir = os.path.join(workdir, 'confound_wf')
    try:
        os.makedirs(confound_dir)
    except OSError:
        pass
    confound_wf = init_confound_wf(t1, t1_mask, wm_tpm, csf_tpm, bold,
                                   bold_mask, metadata['RepetitionTime'],
                                   skipvol)
    confound_wf.base_dir = confound_dir

    # Node to export file to destination directory
    ef_confounds = pe.Node(nio.ExportFile(), name='export_confounds')
    ef_confounds.inputs.out_file = f'{outbase}_confounds.tsv'

    ef_wm = pe.Node(nio.ExportFile(), name='export_wm')
    ef_wm.inputs.out_file = f'{outbase}_wm_roi.nii.gz'

    ef_csf = pe.Node(nio.ExportFile(), name='export_csf')
    ef_csf.inputs.out_file = f'{outbase}_csf_roi.nii.gz'

    ef_acc = pe.Node(nio.ExportFile(), name='export-acc')
    ef_acc.inputs.out_file = f'{outbase}_acc_roi.nii.gz'

    # Set up wrapper workflow for export
    main_dir = os.path.join(workdir, 'main_wf')
    try:
        os.makedirs(main_dir)
    except OSError:
        pass
    wf = pe.Workflow(name='main_wf')
    wf.base_dir = main_dir
    wf.connect([(confound_wf, ef_confounds, [('outputnode.signals', 'in_file')
                                             ]),
                (confound_wf, ef_wm, [('outputnode.wm_roi', 'in_file')]),
                (confound_wf, ef_csf, [('outputnode.csf_roi', 'in_file')]),
                (confound_wf, ef_acc, [('outputnode.acc_roi', 'in_file')])
                ])
    wf.run()


def init_confound_wf(t1, t1_mask, wm_tpm, csf_tpm, bold, bold_mask, tr,
                     skipvols):
    '''
    Initialize the confound extraction workflow
    '''

    inputnode = pe.Node(niu.IdentityInterface(fields=[
        'bold', 'bold_mask', 't1w_mask', 't1w', 'wm_tpm', 'csf_tpm', 'tpms'
    ]),
                        name='inputnode')

    inputnode.inputs.bold = bold
    inputnode.inputs.bold_mask = bold_mask
    inputnode.inputs.t1w_mask = t1_mask
    inputnode.inputs.t1w = t1
    inputnode.inputs.wm_tpm = wm_tpm
    inputnode.inputs.csf_tpm = csf_tpm
    inputnode.inputs.tpms = [wm_tpm, csf_tpm]
    inputnode.inputs.skip_vols = skipvols

    # WM Inputs
    wm_roi = pe.Node(TPM2ROI(erode_prop=0.6, mask_erode_prop=0.6**3),
                     name='wm_roi')
    wm_msk = pe.Node(niu.Function(function=_maskroi0, name='wm_msk'))
    resample_wm_roi = pe.Node(ResampleTPM(), name='resampled_wm_roi')

    # CSF inputs
    csf_roi = pe.Node(TPM2ROI(erode_mm=0, mask_erode_mm=30), name='csf_roi')
    csf_msk = pe.Node(niu.Function(function=_maskroi), name='csf_msk')
    resample_csf_roi = pe.Node(ResampleTPM(), name='resampled_csf_roi')

    # Nodes for aCompCor
    merge_label = pe.Node(niu.Merge(2),
                          name='merge_rois',
                          run_without_submitting=True)

    # Set up aCompCor
    acc_tpm = pe.Node(AddTPMs(indices=[0, 2]), name='tpms_add_csf_wm')
    acc_roi = pe.Node(TPM2ROI(erode_prop=0.6, mask_erode_prop=0.6**3),
                      name='acc_roi')
    resample_acc_roi = pe.Node(ResampleTPM(), name='resampled_acc_roi')
    acc_msk = pe.Node(niu.Function(function=_maskroi), name='acc_msk')
    acompcor = pe.Node(ACompCor(components_file='acompcor.tsv',
                                header_prefix='a_comp_cor_',
                                pre_filter='cosine',
                                repetition_time=tr,
                                save_pre_filter=True),
                       name='acompcor')

    signals_class_labels = ["white_matter", "csf"]
    signals = pe.Node(SignalExtraction(class_labels=signals_class_labels),
                      name="signals")

    # Nodes to join signal extraction and aCompCor components

    outputnode = pe.Node(
        niu.IdentityInterface(fields=['signals', 'wm_roi', 'csf_roi']),
        name='outputnode')

    wf = pe.Workflow(name='confound_wf')
    wf.config['execution']['crashfile_format'] = 'txt'

    # ACC workflow
    wf.connect([(inputnode, acc_tpm, [('tpms', 'in_files')]),
                (inputnode, acc_roi, [('t1w_mask', 'in_mask')]),
                (acc_tpm, acc_roi, [('out_file', 'in_tpm')]),
                (inputnode, resample_acc_roi, [('bold_mask', 'fixed_file')]),
                (acc_roi, resample_acc_roi, [('roi_file', 'moving_file')]),
                (inputnode, acc_msk, [('bold_mask', 'in_mask')]),
                (resample_acc_roi, acc_msk, [('out_file', 'roi_file')]),
                (acc_msk, acompcor, [('out', 'mask_files')]),
                (inputnode, acompcor, [('bold', 'realigned_file')]),
                (inputnode, acompcor, [('skip_vols', 'ignore_initial_volumes')
                                       ])])

    # WM workflow
    wf.connect([(inputnode, wm_roi, [('wm_tpm', 'in_tpm'),
                                     ('t1w_mask', 'in_mask')]),
                (inputnode, resample_wm_roi, [('bold_mask', 'fixed_file')]),
                (wm_roi, resample_wm_roi, [('roi_file', 'moving_file')]),
                (inputnode, wm_msk, [('bold_mask', 'in_mask')]),
                (resample_wm_roi, wm_msk, [('out_file', 'roi_file')])])

    # CSF workflow
    wf.connect([(inputnode, csf_roi, [('csf_tpm', 'in_tpm'),
                                      ('t1w_mask', 'in_mask')]),
                (inputnode, resample_csf_roi, [('bold_mask', 'fixed_file')]),
                (csf_roi, resample_csf_roi, [('roi_file', 'moving_file')]),
                (inputnode, csf_msk, [('bold_mask', 'in_mask')]),
                (resample_csf_roi, csf_msk, [('out_file', 'roi_file')])])

    # Signal extraction workflow
    wf.connect([(wm_msk, merge_label, [('out', 'in1')]),
                (csf_msk, merge_label, [('out', 'in2')]),
                (inputnode, signals, [('bold', 'in_file')]),
                (merge_label, signals, [('out', 'label_files')]),
                (signals, outputnode, [('out_file', 'signals')]),
                (wm_roi, outputnode, [('roi_file', 'wm_roi')]),
                (csf_roi, outputnode, [('roi_file', 'csf_roi')])])

    # Join ACC and WM/CSF signal extraction workflow TSVs

    return wf


def _maskroi(in_mask, roi_file):

    roi = nib.load(roi_file)
    roidata = roi.get_data().astype(np.uint8)
    msk = nib.load(in_mask).get_data().astype(bool)
    roidata[~msk] = 0
    roi.set_data_dtype(np.uint8)

    out = fname_presuffix(roi_file, suffix='_boldmsk')
    roi.__class__(roidata, roi.affine, roi.header).to_filename(out)
    return out


if __name__ == '__main__':
    main()
