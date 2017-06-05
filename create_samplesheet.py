# -*- coding: utf-8 -*-
"""
Created on Wed Nov 11 16:47:03 2015

@brief:  Create sample sheet from TCGA metadata.json for Genomon.
@author: okada

$Id: create_samplesheet.py 127 2016-01-22 02:17:18Z aokada $
$Rev: 127 $

@code
create_samplesheet.py {path to output_sample.csv} {TCGA metadata.json} {path to bam dir} --check_result {bam check_result file} --config_file {option: config file}

@endcode
"""
rev = " $Rev: 127 $"

import numpy
import pandas
import os
import sys
import ConfigParser
import argparse

import subcode

skip_template = "[analysis_id = {id}] is skipped, because of {reason}."

def main():
    name = os.path.splitext(os.path.basename(sys.argv[0]))[0]

    # get args
    parser = argparse.ArgumentParser(prog = name)
    
    parser.add_argument("--version", action = "version", version = name + rev)
    parser.add_argument('output_file', help = "output file, please input with format NAME.csv", type = str)
    parser.add_argument('metadata', help = "metadata file download from TCGA", type = str)
    parser.add_argument('bam_dir', help = "bam downloaded directory", type = str)
    parser.add_argument('--check_result', help = "check_result file", type = str, default = "")
    parser.add_argument("--config_file", help = "config file", type = str, default = "")
    args = parser.parse_args()

    # read config file    
    if len(args.config_file) > 0:
        config_file = os.path.abspath(args.config_file)
    else:
        config_file = os.path.splitext(os.path.abspath(sys.argv[0]))[0] + ".cfg"

    config = ConfigParser.RawConfigParser()
    config.read(config_file)
        
    # path check
    if _is_debug(config) == False:
        if os.path.exists(args.metadata) == False:
            print "This path is not exists." + args.metadata
            return
      
        if len(args.check_result) > 0 and os.path.exists(args.check_result) == False:
            print "This path is not exists." + args.check_result
            return
            
        if os.path.exists(args.bam_dir) == False:
            print "This path is not exists." + args.bam_dir
            return
    
    # get path    
    bam_dir = os.path.abspath(args.bam_dir)
    
    output_file = os.path.abspath(args.output_file)
    if os.path.splitext(output_file)[1].lower() != ".csv":
        print "Input output file path with format NAME.csv"
        return

    if os.path.exists(os.path.dirname(output_file)) == False:
        os.makedirs(os.path.dirname(output_file))
        
    # read metadata
    if _is_debug(config):
        loaded = subcode.load_metadata(args.metadata, check_result=args.check_result)
    else:
        loaded = subcode.load_metadata(args.metadata, bam_dir=bam_dir, check_result=args.check_result)
        
    data_org = subcode.json_to_pandas(loaded["data"])
    for row in loaded["invalid"]:
        print skip_template.format(id = row[0], reason = row[1])
        
    # multiple diseases?
    di1 = data_org.sort(["disease"])
    di2 = di1["disease"][(di1["disease"].duplicated() == False)]
    if (len(di2) > 1):
        print ("WARNING!!! Mixture of diseases.")
        
    # add sample column, person column, if not exists
    #
    # for example.
    # original barcode    TCGA-3H-AB3K-10A-01D-A39U-32
    #  ---> sample        TCGA-3H-AB3K-10
    #  ---> person        TCGA-3H-AB3K
    col_sample = []
    col_person = []
    for i in range(len(data_org)):
        split = data_org["barcode"][i].split("-")
        col_sample.append("%s-%s-%s-%s" % (split[0], split[1], split[2], split[3][0:2]))
        col_person.append("%s-%s-%s" % (split[0], split[1], split[2]))
    
    if ("sample" in data_org.columns) == False:
        add_sample = pandas.DataFrame([col_sample]).T
        add_sample.columns =["sample"]            

    if ("person" in data_org.columns) == False:
        add_person = pandas.DataFrame([col_person]).T
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
                print (skip_template.format(id = tmp_tumor.iloc[i]["analysis_id"], reason = "not have normal"))
            for i in range(len(tmp_normal)):
                print (skip_template.format(id = tmp_normal.iloc[i]["analysis_id"], reason = "not have tumor"))

    # write sample sheet
    f = open(output_file, "w")
    f.write("[bam_tofastq]\n")
    f.write(bamlist_totext(tumor_list, bam_dir, config))
    f.write(bamlist_totext(normal_list, bam_dir, config))
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
    pair_text = pairlist_totext(t2, n2, control)
    normal_text = normallist_totext(n2)
    
    f = open(output_file, "a")
    f.write("\n[mutation_call]\n")
    f.write(pair_text)
    f.write(normal_text)
    f.write("\n[sv_detection]\n")
    f.write(pair_text)
    f.write(normal_text)
    f.write("\n[qc]\n")
    f.write(samplelist_totext(t2))
    f.write(samplelist_totext(n2))
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

def normallist_totext(li):
    text = ""
    for sample in li:
        text += sample + ",None,None\n"
    return text

def samplelist_totext(li):
    text = ""
    for sample in li:
        text += sample + "\n"
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
        
def bamlist_totext(bam_list, bam_dir, config):

    bam_template = "{bam_dir}/{analysis}/{file_name}"

    text = ""
    last = ""
    for i in range(len(bam_list)):

        bam_path = bam_template.format(bam_dir = bam_dir, 
                    analysis = bam_list.iloc[i]["analysis_id"], file_name = bam_list.iloc[i]["filename"])

        if os.path.exists(bam_path) == False and _is_debug(config) == False:
            print ("ERROR!!! This bam path is not exists.[" + bam_path + "], \nplease check arg bam_dir.")
            return text

        # case of bam merge
        if last == bam_list.iloc[i]["sample"]:
            text += (";" + bam_path)

        # case of new sample
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
    

    if data['analysis_id'] == "6c5a8a1d-790e-447f-9bde-91b271dbe9f0":
        pass
    
    # no use ?
    no_use = cfg.get(section, 'no_use').split(",")
    
    if (data["sample_type"] in no_use) == True:
        print (skip_template.format(id = data["analysis_id"], reason = "no use. sample_type=%s" % data["sample_type"]))
        return li
    
    # first data
    if len(li) == 0:
        return li.append(data)
        
    # duplicate barcode ?
    tmp = li[(li["barcode"] == data["barcode"])]
    if len(tmp) > 0:
        print (skip_template.format(id = data["analysis_id"], reason = "barcode duplicate. barcode=%s" % data["barcode"]))
        return li

    # merge ?
    merge_list = cfg.get(section, 'merge').split(",")
    merge = False
    if (tumor == False) and (len(merge_list) > 0):
        if (data["sample_type"] in merge_list) == True:
            merge = True
            
    # priority            
    pri_data = 99       # priority of now
    if (data["sample_type"] in priority) == True:
        pri_data = priority.index(data["sample_type"])

    pri_li = 99         # priority of registered
    for i in range(len(li)):
        if (li.iloc[i]["sample_type"] in priority) == True:
            pri = priority.index(li.iloc[i]["sample_type"])
            if pri < pri_li:
                pri_li = pri
                
    if pri_data == pri_li:   # even
        if merge == True:
            print ("[analysis_id = %s] is merged. sample_type=%s" % (data["analysis_id"], data["sample_type"]))
            return li.append(data)
        else:
            print (skip_template.format(id = data["analysis_id"], reason = "sample type duplicate. sample_type=%s" % data["sample_type"]))
            return li 
            
    elif pri_data < pri_li:   # win
        li = pandas.DataFrame([])
        return li.append(data)

    else:                     # lost
        print (skip_template.format(id = data["analysis_id"], reason = "priority. sample_type=%s" % data["sample_type"]))
        
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

def _is_debug(config):
    
    debug = False
    if config.has_option("MAIN", "debug_mode") == True:
        debug = config.getboolean("MAIN", "debug_mode")
    
    return debug
    
if __name__ == "__main__":

    main()
  
