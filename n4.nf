nextflow.preview.dsl = 2

usage = file("${workflow.scriptFile.getParent()}/usage/n4_usage")
bindings = [ "rewrite":"$params.rewrite",
             "bspline":"$params.bspline",
             "niter":"$params.niter",
             "subjects": "$params.subjects"]
engine = new groovy.text.SimpleTemplateEngine()
toprint = engine.createTemplate(usage.text).make(bindings)
printhelp = params.help

// Input checking and validation
req_param = ["--study": params.study,
             "--out": params.out]

missing_arg = req_param.grep{ (it.value == null || it.value == "") }
if (missing_arg){
    log.error("Missing required argument(s)!")
    missing_arg.each{ log.error("Missing ${it.key}") }
    printhelp = true
}

if (printhelp){
   print(toprint)
   System.exit(0)
}

process apply_n4{

    label 'niworkflows'
    publishDir "$params.out/$params.application/$sub", \
                mode: 'copy', \
                pattern: "${sub}*_corrected.nii.gz", \
                saveAs: { it.replace("_corrected.nii.gz", "_n4.nii.gz") }


    input:
    tuple val(sub), path(t1)

    output:
    tuple val(sub), path("${sub}*_corrected.nii.gz"), emit: n4

    shell:
    '''
    t1=$(basename !{t1})
    sub_w_desc=${t1%.nii.gz}
    python /scripts/process_file.py !{t1} !{params.bspline} !{params.niter}
    mv n4_wf/corrected_img/${sub_w_desc}_corrected.nii.gz .
    '''

}

log.info("Running N4 pipeline...")
log.info("Study: $params.study")
log.info("Output Directory: $params.out")
log.info("BSpline Distance: $params.bspline")
log.info("N-iterations: $params.niter x 5")

// Pull sessions to run
nii_dir = "$params.archive/$params.study/data/nii"
nii_channel = Channel.fromPath("$nii_dir/*", type: "dir")
                     .map{ i -> [i.getBaseName(), i] }
                     .filter{i,p -> !(i.contains("PHA"))}

if (params.subjects){
    subjects_channel = Channel.fromPath(params.subjects)
                                .splitText(){it.strip()}
    nii_channel = nii_channel.join(subjects_channel, by: 0)
}

if (!params.rewrite){
    out_channel = Channel.fromPath("$params.out/$params.application/*", type: "dir")
                        .map{ o -> [o.getBaseName(), "o"] }
                        .ifEmpty(['', "o"])

    nii_channel = nii_channel.join(out_channel, remainder:true)
                             .filter{it.contains(null)}
                             .map { i,p,n -> [i,p] }
}

// Get T1 scans
scan_channel = nii_channel.map{ i,p -> [
                                        i,
                                        new File("$p/").list().findAll{
                                                                it.contains("_T1_") &
                                                                it.contains(".nii.gz")}
                                       ]
                              }
                          .filter { !(it[1].isEmpty()) }
                          .transpose()
                          .map{ i,p -> [i,
                                        new File("$nii_dir/$i/$p").toPath()
                                       ]
                              }

workflow{

    main:
    apply_n4(scan_channel)
}
