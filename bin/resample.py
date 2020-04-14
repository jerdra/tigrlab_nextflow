"""Image tools interfaces."""
from nilearn.image import resample_to_img
import numpy as np
import nibabel as nb
from nipype.utils.filemanip import fname_presuffix
from nipype import logging
from nipype.interfaces.base import (traits, TraitedSpec,
                                    BaseInterfaceInputSpec, SimpleInterface,
                                    File)

LOGGER = logging.getLogger('nipype.interface')


class _ResampleTPMInputSpec(BaseInterfaceInputSpec):
    moving_file = File(exists=True,
                       mandatory=True,
                       desc='Eroded Tissues probability map file in T1 space')
    fixed_file = File(exists=True,
                      mandatory=True,
                      desc=' timeseries mask in BOLD space')


class _ResampleTPMOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='output Resampled WM file')


class ResampleTPM(SimpleInterface):
    """
    Resample all white matter tissue prob mask to BOLD space.
    """
    input_spec = _ResampleTPMInputSpec
    output_spec = _ResampleTPMOutputSpec

    # def _run_interface(self,runtime):
    #     self._results['out_file'] = resample_WM(
    #         self.inputs.moving_file,
    #         self.inputs.fixed_file,
    #         newpath=runtime.cwd
    #     )
    #     return runtime
    def _run_interface(self, runtime):

        out_file = _TPM_2_BOLD(
            self.inputs.moving_file,
            self.inputs.fixed_file,
            newpath=runtime.cwd,
        )
        self._results['out_file'] = out_file
        return runtime


def _TPM_2_BOLD(moving_file, fixed_file, newpath=None):
    """
    Resample the input white matter tissues probability using resample_to_img from nilearn.
    """

    out_file = fname_presuffix(moving_file,
                               suffix='_resampled',
                               newpath=newpath)

    resample_wm = resample_to_img(source_img=moving_file,
                                  target_img=fixed_file,
                                  interpolation='nearest')
    resample_wm.to_filename(out_file)
    return out_file
