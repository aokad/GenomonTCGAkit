# -*- coding: utf-8 -*-
"""
Created on Wed Nov 11 16:47:03 2015

@brief:  Create sample sheet from TCGA summary.tsv for Genomon.
@author: okada

# run
create_samplesheet.py {output_file} {summary file} {path to bam dir} {bam check_result file} --config_file {option: config file}
"""

import numpy
import pandas
import os
import sys
import ConfigParser
import argparse

skip_template = "[analysis_id = {id}] is skipped, because of {reason}."

def main():
    name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    
    # get args
    parser = argparse.ArgumentParser(prog = name)
    
    parser.add_argument("--version", action = "version", version = name + "-1.0.0")
    parser.add_argument('output_file', help = "output file, please input with format NAME.csv", type = str)
    parser.add_argument('summary', help = "summary file download from TCGA", type = str)
    parser.add_argument('bam_dir', help = "bam downloaded directory", type = str)
    parser.add_argument('--check_result', help = "check_result file", type = str, default = "")
    parser.add_argument("--config_file", help = "config file", type = str, default = "")
    args = parser.parse_args()
    
    if os.path.exists(args.summary) == False:
        print "This path is not exists." + args.summary
        return

    if len(args.check_result) > 0 and os.path.exists(args.check_result) == False:
        print "This path is not exists." + args.check_result
        return

    if os.path.exists(args.bam_dir) == False:
        print "This path is not exists." + args.bam_dir
        return
    
    output_file = os.path.abspath(args.output_file)
    if os.path.splitext(output_file)[1].lower() != ".csv":
        print "Input output file path with format NAME.csv"
        return

    if os.path.exists(os.path.dirname(output_file)) == False:
        os.makedirs(os.path.dirname(output_file))

    summary = os.path.abspath(args.summary)
        
    if len(args.check_result) > 0:
        check_result = os.path.abspath(args.check_result)
        
    bam_dir = os.path.abspath(args.bam_dir)
    
    if len(args.config_file) > 0:
        config_file = os.path.abspath(args.config_file)
    else:
        config_file = os.path.splitext(os.path.abspath(sys.argv[0]))[0] + ".cfg"
        
    # read config file
    config = ConfigParser.RawConfigParser()
    config.read(config_file)
    debug = False
    if config.has_option("MAIN", "debug_mode") == True:
        debug = config.getboolean("MAIN", "debug_mode")
        
    # read summary
    ext = os.path.splitext(summary)[1]
    if ext.lower() == ".tsv":
        data_org = pandas.read_csv(summary, sep = "\t")
    elif ext.lower() == ".csv":
        data_org = pandas.read_csv(summary, sep = ",")
    else:
        print (ext + " file is not support")
        return

    if len(data_org) < 1:
        print ("no summary data.")
        return
        
    # multiple diseases?
    di1 = data_org.sort(["disease"])
    di2 = di1["disease"][(di1["disease"].duplicated() == False)]
    if (len(di2) > 1):
        print ("WARNING!!! Mixture of diseases.")
        
    # read result
    if len(args.check_result) > 0:
        result = pandas.read_csv(check_result, sep = ",")
        
    # add person column, if not exists
    tmp = []
    for i in range(len(data_org)):
        split = data_org["barcode"][i].split("-")
        tmp.append(split[0] + "-" + split[1] + "-" + split[2])

    add_sample = pandas.DataFrame([tmp]).T
    add_sample.columns =["sample"]            

    if ("person" in data_org.columns) == False:
        add_person = pandas.DataFrame([tmp]).T
        add_person.columns =["person"]

        data_tmp = pandas.concat([add_sample, add_person, data_org], axis=1)
    else:
        data_tmp = pandas.concat([add_sample, data_org], axis=1)
    
    # sort
    data = data_tmp.sort(columns=["person", "published", "modified"], ascending=[1, 0, 0])
    
    # get tumor-normal pair
    person_list = data["person"][(data["person"].duplicated() == False)]

    tumor_list = pandas.DataFrame([])
    normal_list = pandas.DataFrame([])
        
    for person in person_list:

        one = data[(data["person"] == person)]

        tmp_tumor = pandas.DataFrame([])
        tmp_normal = pandas.DataFrame([])
        
        for j in range(len(one)):
            if len(args.check_result) > 0:
                rst = result[(result["analysis_id"] == one.iloc[j]["analysis_id"])]
                
                if len(rst) == 0:
                    print ("WARNING!!! [analysis_id = {id}] cannot find result data in bamcheck file.".format(id = one.iloc[j]["analysis_id"]))
                    continue
                if len(rst.shape) > 1:
                    rst = rst.iloc[0]

                if (rst["single_lines"] == -1) and (rst["total_lines"] == -1):
                    print (skip_templete.format(id = one.iloc[j]["analysis_id"], reason = "find result -1 in bamcheck file."))
                    continue

                if float(rst["single_lines"])/float(rst["total_lines"]) > 0.2:
                    print (skip_templete.format(id = one.iloc[j]["analysis_id"], reason = "number of single read id over the threshold."))
                    continue
            
            sample_type = one.iloc[j]["sample_type_name"]

            # apply barcode duplicate
            if sample_type >= 1 and sample_type <= 9:
                tmp_tumor = append_list(tmp_tumor, one.iloc[j], config, True)
                
            if sample_type >= 10 and sample_type <= 19:
                tmp_normal = append_list(tmp_normal, one.iloc[j], config, False)

        if len(tmp_tumor) > 0 and len(tmp_normal) > 0:
            tumor_list = tumor_list.append(tmp_tumor)
            normal_list = normal_list.append(tmp_normal)
        else:
            for i in range(len(tmp_tumor)):
                print (skip_template.format(id = tmp_tumor.iloc[i]["analysis_id"], reason = "'not have normal'"))
            for i in range(len(tmp_normal)):
                print (skip_template.format(id = tmp_normal.iloc[i]["analysis_id"], reason = "'not have tumor'"))

    # write sample sheet
    f = open(output_file, "w")
    f.write("[bam_tofastq]\n")
    f.write(bamlist_totext(tumor_list, bam_dir, debug))
    f.write(bamlist_totext(normal_list, bam_dir, debug))
    f.close()

    # make control_panel
    t1 = tumor_list.sort(["sample"])
    t2 = t1["sample"][(t1["sample"].duplicated() == False)]
    n1 = normal_list.sort(["sample"])
    n2 = n1["sample"][(n1["sample"].duplicated() == False)]
    if (len(t2) != len(n2)):
        print ("ERROR!!! It is not match normal sample's number and tumor's.")
        return
    
    if len(n2) < 20:
        print ("ERROR!!! Too few normal sample's number.[%d]" % len(n2))
        return
           
    if len(n2) >= 30 and len(n2) < 40:
        print ("Sorry... It is not support to this normal sample's number.[%d]" % len(n2))
        return
        
    list_num = split_list(len(n2), persons = 20, persons_min = 20)
    control = []
    for i in range(len(list_num)):
        control.append(range(i, i + len(list_num) * list_num[i], len(list_num)))

    # write sample sheet
    text = pairlist_totext(t2, n2, control)
    f = open(output_file, "a")
    f.write("\n[mutation_call]\n")
    f.write(text)
    f.write("\n[sv_detection]\n")
    f.write(text)
    f.write("\n[controlpanel]\n")
    f.write(contrlpanel_totext(n2, control))
    f.close()
    
    print "written sample sheet. %d persons." % len(t2)
    
def pairlist_totext(tumor_list, normal_list, control):
    text = ""
    li_idx = 0
    for i in range(len(tumor_list)):
        
        text += tumor_list.iloc[i] + "," + normal_list.iloc[i] + ","
        if (i in control[li_idx]) == True:
            li_idx = (li_idx + 1) % len(control)
            
        text += "List%02d" % li_idx
        
        t_check = tumor_list.iloc[i].split("-")
        n_check = normal_list.iloc[i].split("-")
        if t_check[0] != n_check[0] or t_check[1] != n_check[1] or t_check[2] != n_check[2]:
            print ("ERROR!!! It is not match normal sample's human and tumor's. [" + \
                    tumor_list.iloc[i] + "," + normal_list.iloc[i] + "]")
            text += ",ERROR\n"
        else:
            text += "\n"
            
        li_idx = (li_idx + 1) % len(control)
    return text
    
def contrlpanel_totext(normal_list, control):
    text = ""
    counter = 0
    for items in control:
        text += "List%02d" % counter
        for item in items:
            text += "," + normal_list.iloc[item]

        text += "\n"
        counter += 1
    
    return text
        
def bamlist_totext(bam_list, bam_dir, debug):

    bam_template = "{bam_dir}/{analysis}/{file_name}"

    text = ""
    last = ""
    for i in range(len(bam_list)):

        bam_path = bam_template.format(bam_dir = bam_dir, 
                    analysis = bam_list.iloc[i]["analysis_id"], file_name = bam_list.iloc[i]["filename"])

        if os.path.exists(bam_path) == False and debug == False:
            print ("ERROR!!! This bam path is not exists.[" + bam_path + "], \nplease check arg bam_dir.")
            return text

        if last == bam_list.iloc[i]["sample"]:
            text += ("," + bam_path)

        else:
            if (len(text) > 0):
                text += ("\n")
            text += (bam_list.iloc[i]["sample"])
            text += ("," + bam_path)
        
        last = bam_list.iloc[i]["sample"]
    
    if (len(text) > 0):
        text += "\n"
        
    return text
    
def append_list(li, data, cfg, tumor):
    section = data["disease"]
    if cfg.has_section(section) == False:
        section = "DEFAULT"
    
    if tumor == True:
        priority = cfg.get(section, 'priority_tumor').split(",")
    else:
        priority = cfg.get(section, 'priority_normal').split(",")
        
    merge_list = cfg.get(section, 'merge').split(",")
    merge = False
    if (tumor == False) and (len(merge_list) == 0):
        if (data["sample_type"] in merge_list) == True:
            merge = True
    
    no_use = cfg.get(section, 'no_use').split(",")

    data["sample"] = data["sample"] + "-" + "%02d" % data["sample_type_name"]
    
    # no use
    if (data["sample_type"] in no_use) == True:
        print (skip_template.format(id = data["analysis_id"], reason = "'no use'"))
        return li
    
    # same sample_type
    if len(li) > 0 and merge == True:
        tmp = li[(li["sample_type"] == data["sample_type"])]
        if len(tmp):
            print (skip_template.format(id = data["analysis_id"], reason = "'sample type duplicate'"))
            return li
        
    # priority
    if len(li) == 0:
        return li.append(data)
        
    pri_data = 99
    if (data["sample_type"] in priority) == True:
        pri_data = priority.index(data["sample_type"])

    pri_li = 99
    for i in range(len(li)):
        if (li.iloc[i]["sample_type"] in priority) == True:
            pri = priority.index(li.iloc[i]["sample_type"])
            if pri < pri_li:
                pri_li = pri
    
    if pri_data == pri_li:
        if merge == True:
            return li.append(data)
        else:
            print (skip_template.format(id = data["analysis_id"], reason = "'sample type duplicate'"))
            return li
            
    if pri_data < pri_li:
        li = pandas.DataFrame([])
        return li.append(data)

    else:
        print (skip_template.format(id = data["analysis_id"], reason = "'priority'"))
        
    return li


def split_list(leng, persons = 0, files = 0, persons_min = 0):

    if persons == 0 and files == 0:
        return numpy.ones(1) * leng
        
    if files == 0:
        files = int(leng/persons)
    
    cols = numpy.zeros(0)
    
    while(1):
        if files < 1:
            break
        
        cols = _split_list(leng, files)
        if numpy.min(cols) >= persons_min:
            break
        
        files -= 1

    return cols

def _split_list(leng, size):
       
    cols = numpy.ones(size, dtype=numpy.int32) * (leng/size)
    mod = leng % size
    
    for i in range(mod):
        cols[i] += 1

    return cols


if __name__ == "__main__":

    main()
  