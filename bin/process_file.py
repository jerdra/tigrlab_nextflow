import os
import argparse
from nipype import Workflow
from nipype.interfaces.io import DataSink
from nipype.interfaces import utility as niu
from nipype.interfaces.ants import N4BiasFieldCorrection
from nipype.pipeline import engine as pe
from nipype.interfaces.fsl.maths import ApplyMask

from niworkflows.anat.ants import init_brain_extraction_wf
from niworkflows.interfaces import SimpleBeforeAfter


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("t1", help="Input T1 file", type=str)
    parser.add_argument("bspline", help="Bspline distance for N4", type=int)
    parser.add_argument("niter",
                        help="Number of iterations, will be multipled"
                        "by [niter]*5",
                        type=int)
    args = parser.parse_args()

    t1 = args.t1
    bspline = args.bspline
    niter = args.niter

    # Standard input
    workdir = os.getcwd()
    t1 = os.path.join(workdir, t1)

    # Initialize workflow
    wf = Workflow(name="bias_field")
    wf.base_dir = os.getcwd()

    # Set up input node of list type
    input_node = pe.Node(niu.IdentityInterface(fields=['in_files']),
                         name='inputnode')
    input_node.inputs.in_files = [t1]

    # Set up input node of value type
    single_file_buf = pe.Node(niu.IdentityInterface(fields=['input_file']),
                              name='inputfile')
    single_file_buf.inputs.input_file = t1

    # Initial skullstrip
    ants_wf = init_brain_extraction_wf(in_template='OASIS30ANTs',
                                       atropos_use_random_seed=False,
                                       normalization_quality='precise')

    # Apply N4 bias field correction
    # Iterate over:
    # bspline fitting distances
    # number of iterations
    n4 = pe.Node(N4BiasFieldCorrection(dimension=3,
                                       save_bias=True,
                                       copy_header=True,
                                       convergence_threshold=1e-7,
                                       shrink_factor=4,
                                       bspline_fitting_distance=bspline,
                                       n_iterations=[niter] * 5),
                 name='n4')

    outputnode = pe.Node(
        niu.IdentityInterface(fields=['corrected_t1', 'orig_t1']), name='out')

    datasink = pe.Node(DataSink(base_directory=workdir, container='n4_wf'),
                       name='sink')

    datasink.inputs.substitutions = [('_bspline_fitting_distance_',
                                      'bspline-'), ('n_iterations_', 'niter-')]

    wf.connect([[input_node, ants_wf, [('in_files', 'inputnode.in_files')]],
                [single_file_buf, n4, [('input_file', 'input_image')]],
                [ants_wf, n4, [('outputnode.out_mask', 'mask_image')]],
                [n4, outputnode, [('output_image', 'corrected_t1')]],
                [single_file_buf, outputnode, [('input_file', 'orig_t1')]],
                [
                    outputnode, datasink,
                    [('corrected_t1', 'corrected_img.@corrected'),
                     ('orig_t1', 'corrected_img.@orig')]
                ]])
    wf.run()


if __name__ == '__main__':
    main()
