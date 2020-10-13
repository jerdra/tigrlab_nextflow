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

    input:
    tuple val(sub), val(ses),\
    path(t1), path(t1_bm),\
    path(wm), path(csf),\
    path(func), path(func_bm), path(func_json),\
    val(base)

    output:
    tuple val(sub), val(base),  path("${base}_new_confounds.tsv"), emit: confounds
    tuple val(sub), val(base),  path("${base}_new_confounds.json"), emit: confounds_metadata
    tuple val(sub), val(base),  path("${base}_wm_roi.nii.gz"), emit: wm
    tuple val(sub), val(base),  path("${base}_csf_roi.nii.gz"), emit: csf
    tuple val(sub), val(base),  path("${base}_acc_roi.nii.gz"), emit: acc

    shell:
    '''
    PYTHONPATH=/scripts
    /scripts/confounds.py $(pwd)/!{t1} $(pwd)/!{t1_bm} $(pwd)/!{wm} $(pwd)/!{csf} \
                         $(pwd)/!{func} $(pwd)/!{func_bm} $(pwd)/!{func_json} \
                         --workdir $(pwd) $(pwd)/!{base}
    rename 's/_confounds/_new_confounds/g' *confounds*
    '''

}

process update_confounds{

    label 'fmriprep'

    input:
    tuple val(sub), val(base), val(ses),\
    path(new_confounds), path(confounds)

    output:
    tuple val(sub), val(base), val(ses),\
    path("${base}_merged_confounds.tsv"), emit: confounds

    shell:
    '''
    #!/usr/bin/env python
    import numpy as np
    import pandas as pd

    # Load in TSV files
    old_tsv = pd.read_csv("!{confounds}", delimiter="\t")
    new_tsv = pd.read_csv("!{new_confounds}", delimiter="\t")

    # Rename headers in new and drop in old
    cols = new_tsv.columns
    new_tsv.columns = ["{}_fixed".format(c) for c in cols]

    # Drop columns in old tsv
    old_tsv.drop(columns = cols, inplace=True)
    out = old_tsv.merge(new_tsv, left_index=True, right_index=True)
    out.to_csv("!{base}_merged_confounds.tsv", sep="\\t")

    '''
}

process update_metadata{

    label 'fmriprep'

    input:
    tuple val(sub), val(base), val(ses),\
    path(new_meta), path(meta)

    output:
    tuple val(sub), val(base), val(ses),\
    path("${base}_merged_confounds.json"), emit: metadata

    shell:
    '''
    #!/usr/bin/env python

    import json

    with open("!{meta}", "r") as f:
        meta = json.load(f)

    with open("!{new_meta}", "r") as f:
        new_meta = json.load(f)

    # Remove columns being replaced
    cleaned_meta = {k: v for k,v in meta.items() if not (("a_comp" in k) or ("dropped" in k))}
    out_meta = {**cleaned_meta, **new_meta}

    with open("!{base}_merged_confounds.json", "w") as f:
        json.dump(out_meta, f, indent=2)
    '''
}

process write_to_fmriprep{

    label 'fmriprep'
    stageInMode 'copy'

    publishDir path: "$params.fmriprep/$sub/$ses/func",\
               pattern: "*tsv",\
               saveAs: { f -> "${base}_desc-confounds_fixedregressors.tsv" },\
               mode: 'copy'

    publishDir path: "$params.fmriprep/$sub/$ses/func",\
               pattern: "*json",\
               saveAs: { f -> "${base}_desc-confounds_fixedregressors.json" },\
               mode: 'copy'

    input:
    tuple val(sub), val(base), val(ses),\
    path(confounds), path(metadata)

    output:
    tuple path(confounds), path(metadata)

    shell:
    '''
    echo "Writing confounds to !{params.fmriprep}/!{sub}/!{ses}/func/!{base}_desc-confound_fixedregressors.tsv"
    echo "Writing confounds to !{params.fmriprep}/!{sub}/!{ses}/func/!{base}_desc-confound_fixedregressors.json"
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

    // There's probably a better way to gather inputs for the confounds file

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
                        .map{sub,ses,t,tbm,wm,csf,fmri,fbm,base ->
                            [
                                sub,ses,t,tbm,wm,csf,fmri,fbm,
                                fmri.toString().replaceFirst(/nii.gz/, "json"),
                                base
                            ]}

    gen_confounds(i_gen_confounds)

    // Operations to pull off:
    // 1 - A tag identification mark

    // Next extract the confounds file
    basenames = i_gen_confounds.map{sub,ses,t,tbm,wm,csf,fmri,fbm,js,base ->
                                            [sub,base,ses,
                                            "${params.fmriprep}/${sub}/${ses}/func/"]
                                   }

    i_update_confounds = basenames.join(gen_confounds.out.confounds, by: [0,1])
                                  .map{sub,base,ses,funcp,conf ->
                                  [sub,base,ses,conf,
                                  "${funcp}/${base}_desc-confounds_regressors.tsv"
                                  ]}
    update_confounds(i_update_confounds)

    i_update_metadata = basenames.join(gen_confounds.out.confounds_metadata, by: [0,1])
                                  .map{sub,base,ses,funcp,meta ->
                                  [sub,base,ses,meta,
                                  "${funcp}/${base}_desc-confounds_regressors.json"
                                  ]}
    update_metadata(i_update_metadata)

    i_write_to_fmriprep = update_confounds.out.confounds
                            .join(update_metadata.out.metadata, by: [0,1,2])
    write_to_fmriprep(i_write_to_fmriprep)

}
