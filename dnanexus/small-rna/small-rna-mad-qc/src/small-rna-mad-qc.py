#!/usr/bin/env python
# Runs "mean absolute deviation" QC metrics on two long-RNA-seq gene quantifications

import os, subprocess, json
import dxpy

@dxpy.entry_point("main")
def main(quants_a, quants_b, annotations):

    # tool_versions.py --applet $script_name --appver $script_ver
    sw_versions = subprocess.check_output(['tool_versions.py', '--dxjson', 'dnanexus-executable.json'])

    dxfile_a = dxpy.DXFile(quants_a)
    dxfile_b = dxpy.DXFile(quants_b)
    dxfile_anno = dxpy.DXFile(annotations)

    print "* Downloading files..."
    dxpy.download_dxfile(dxfile_a.get_id(), "quants_a.tsv")
    dxpy.download_dxfile(dxfile_b.get_id(), "quants_b.tsv")
    dxpy.download_dxfile(dxfile_anno.get_id(), "annotations.gtf.gz")
    
    print "* Extracting gene ids from annotation..."
    subprocess.check_call(['gunzip', 'annotations.gtf.gz'])
    subprocess.check_call(['gawk', '-f', '/usr/bin/extract_gene_ids.awk', 'annotations.gtf', 'out=srna_gene_ids.txt'])
    
    print "* Generating expression values for "+dxfile_a.name+"..."
    summary_a = subprocess.check_output(['gawk','-f','/usr/bin/sum_srna_expression.awk','srna_gene_ids.txt', \
                                                                                        'quants_a.tsv', 'out=expr_a.tsv'])
    print summary_a

    print "* Generating expression values for "+dxfile_b.name+"..."
    summary_b = subprocess.check_output(['gawk','-f','/usr/bin/sum_srna_expression.awk','srna_gene_ids.txt',\
                                                                                        'quants_b.tsv', 'out=expr_b.tsv'])
    print summary_b
    print subprocess.check_output(['ls', '-l'])
    
    print "* Runnning MAD.R..."
    mad_output = subprocess.check_output(['Rscript', '/usr/bin/MAD.R', 'expr_a.tsv', 'expr_b.tsv'])
    quants_a_name = dxfile_a.name.split('.')
    quants_b_name = dxfile_b.name.split('.')
    filename = quants_a_name[0] + '_' + quants_b_name[0] + '_' + quants_a_name[1] + '_mad_plot.png'
    subprocess.check_call(['mv', "MAplot.png", filename])
    
    print "* package properties..."
    qc_metrics = {}
    qc_metrics["MAD.R"] = json.loads(mad_output)
    meta_string = json.dumps(qc_metrics)
    print json.dumps(qc_metrics,indent=4)
    props = {}
    props["SW"] = sw_versions

    print "* Upload Plot..."
    plot_dxfile = dxpy.upload_local_file(filename,properties=props,details=qc_metrics)
    
    return { "metadata": meta_string, "mad_plot": plot_dxfile }

dxpy.run()
