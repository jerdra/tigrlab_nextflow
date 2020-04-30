nextflow.preview.dsl = 2

usage = file("${workflow.scriptFile.getParent()}/usage/recalculate_confounds")
engine = new groovy.text.SimpleTemplateEngine()

bindings = ["fmriprep": params.fmriprep,
            "fmriprep_img": params.fmriprep_img,
            "subjects": params.subjects,
            "rewrite": params.rewrite,
            "fmriprep_img":params.fmriprep_img
            ]

toprint = engine.createTemplate(usage.text).make(bindings)
printhelp = params.help

req_param = ["--fmriprep": params.fmriprep]
missing_arg = req_param.grep{ (it.value == null || it.value == "") }
if (missing_arg){
    log.error("Missing required arguments(s)!")
    missing_arg.each{ log.error("Missing ${it.key}") }
    printhelp = true
}
if (printhelp){
    print(toprint)
    System.exit(0)
}

process denoise_image{

    label 'fmriprep'

    input:
    tuple val(sub), path(t1w), path(mask)

    output:
    tuple val(sub), path("${sub}_desc-denoised.nii.gz"), emit: denoised

    shell:
    '''
    DenoiseImage -d 3 -i !{t1w} -x !{mask} -o !{sub}_desc-denoised.nii.gz
    '''

}

process apply_mask{

    label 'fmriprep'

    input:
    tuple val(sub), path(t1w), path(mask)

    output:
    tuple val(sub), path("${sub}_desc-masked.nii.gz"), emit: masked

    shell:
    '''
    fslmaths !{t1w} -mas !{mask} !{sub}_desc-masked.nii.gz
    '''
}


process fast{

    label 'fmriprep'

    input:
    tuple val(sub), path(t1w)

    output:
    tuple val(sub),\
    path("${sub}_desc-prob_2.nii.gz"), path("${sub}_desc-prob_0.nii.gz"), emit: tpm

    shell:
    '''
    fast -p -g --nobias -o t1 !{t1w}
    rename "s/t1_/!{sub}_desc-/g" t1*
    '''

}

process gen_confounds{

    label 'fmriprep'
    stageInMode 'copy'
    publishDir path: "$params.fmriprep/$sub/$ses/func",\
               pattern: "*confounds.tsv",\
               saveAs: { f -> "${base}_desc-confounds_regressors_fixed.tsv" },\
               mode: 'copy'

    input:
    tuple val(sub), val(ses),\
    path(t1), path(t1_bm),\
    path(wm), path(csf),\
    path(func), path(func_bm),\
    val(base)

    output:
    tuple val(sub), path("${base}_confounds.tsv"), emit: confounds
    tuple val(sub), path("${base}_wm_roi.nii.gz"), emit: wm
    tuple val(sub), path("${base}_csf_roi.nii.gz"), emit: csf

    shell:
    '''
    PYTHONPATH=/scripts
    /scripts/confounds.py $(pwd)/!{t1} $(pwd)/!{t1_bm} $(pwd)/!{wm} $(pwd)/!{csf} \
                         $(pwd)/!{func} $(pwd)/!{func_bm} --workdir $(pwd) \
                         $(pwd)/!{base}
    '''

}

// Implement logic to filter subjects
input_channel = Channel.fromPath("$params.fmriprep/sub-*", type: "dir")
                    .map{ i -> [i.getBaseName(), i] }

// Filter subjects
if (params.subjects){

    subjects_channel = Channel.fromPath(params.subjects)
                            .splitText(){it.strip()}
    input_channel = input_channel.join(subjects_channel)
}


def remove_desc = ~/_desc.*/
def remove_space = ~/_space-\p{Alnum}+_?/
def ses_from_bids = ~/(?<=_)ses-.*?(?=_)/
workflow {

    // Structural inputs
    t1_channel = input_channel.map{i,f -> [i,"$f/anat/${i}_desc-preproc_T1w.nii.gz"]}
    mask_channel = input_channel.map{i,f -> [i,"$f/anat/${i}_desc-brain_mask.nii.gz"]}

    // Denoise the image, yielding a denoised T1 unmasked
    i_denoise_image = t1_channel.join(mask_channel)
    denoise_image(i_denoise_image)

    // Apply mask to denoised image
    i_apply_mask = denoise_image.out.denoised.join(mask_channel)
    apply_mask(i_apply_mask)

    // Run fast
    fast(apply_mask.out.masked)

    // Put together inputs for running confound calculation
    i_gen_confounds = input_channel
                        .join(denoise_image.out.denoised)
                        .join(mask_channel)
                        .join(fast.out.tpm)
                        .map{s,f,t,tbm,wm,csf ->
                            [ s,f,t,tbm,wm,csf,
                            file("${f}/ses-*/func/${s}_*space-T1w*{preproc,mask}*.nii.gz")]}
                        .transpose()
                        .map{s,f,t,tbm,wm,csf,fmri ->
                            [s,t,tbm,wm,csf,fmri.getName() - remove_desc, fmri]
                            }
                        .groupTuple(by: [0,1,2,3,4,5], size: 2)
                        .map{sub,t,tbm,wm,csf,k,fmri->
                            [sub,
                            (k =~ ses_from_bids)[0],
                            t,tbm,wm,csf,
                            fmri.sort{a,b -> b.getBaseName()<=>a.getBaseName()},
                            k - remove_space].flatten()
                            }

    gen_confounds(i_gen_confounds)

}
