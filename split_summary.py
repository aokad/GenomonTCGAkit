# -*- coding: utf-8 -*-
"""
Created on Wed Nov 11 16:47:03 2015

@brief:  (1) Split TCGA summary.tsv and manifest.xml. Per diseases, per 200 persons.<br>
         (2) Remove the bams which has no pair.
         
@author: okada

$Id: split_summary.py 83 2015-12-11 06:53:14Z aokada $
$Rev: 83 $

# run
@code
split_summary.py {output_dir} {summary file} {manifest file}
@endcode
"""

from xml.etree import ElementTree
from xml.dom import minidom
import numpy
import pandas
import os
import sys
import datetime
import argparse

output_summary_cols = ["person", "study", "barcode", "disease", "disease_name", "sample_type", "sample_type_name", \
                    "analyte_type", "library_type", "center", "center_name", "platform", "platform_name", "assembly", \
                    "filename", "files_size", "checksum", "analysis_id", "aliquot_id", "participant_id", "sample_id", \
                    "tss_id", "sample_accession", "published", "uploaded", "modified", "state", "reason"]

def main():
    name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    
    # get args
    parser = argparse.ArgumentParser(prog = name)
    
    parser.add_argument("--version", action = "version", version = name + "-1.0.0")
    parser.add_argument('output_dir', help = "output root directory", type = str)
    parser.add_argument('summary', help = "summary file download from TCGA", type = str)
    parser.add_argument('manifest', help = "manifest file download from TCGA", type = str)
    args = parser.parse_args()
    
    # get args
    output_dir = os.path.abspath(args.output_dir)
    summary = os.path.abspath(args.summary)
    manifest = os.path.abspath(args.manifest)

    split_persons = 200
    
    output_download = output_dir + "/download_list.csv"
    output_summary = output_dir + "/summary/"
    output_manifest = output_dir + "/manifest/"
    
    if os.path.exists(output_dir) == False:
        os.makedirs(output_dir)

    if os.path.exists(output_summary) == False:
        os.makedirs(output_summary)

    if os.path.exists(output_manifest) == False:
        os.makedirs(output_manifest)

    # read
    data_org = pandas.read_csv(summary, sep = "\t")

    # add person column
    tmp = []
    for i in range(len(data_org)):
        split = data_org["barcode"][i].split("-")
        tmp.append(split[0] + "-" + split[1] + "-" + split[2])
        
    df_addition_col = pandas.DataFrame([tmp]).T
    df_addition_col.columns =["person"]
    data_cat = pandas.concat([df_addition_col, data_org], axis=1)
    
    data_sort = data_cat.sort(columns=["person"])
    
    
    ### ----- screate download list -----
    # get tumor-normal pair
    data = data_sort

    person_list = data["person"][(data["person"].duplicated() == False)]
    print "Input summary all persons: %d" % len(person_list)

    download_list = pandas.DataFrame([])
        
    for person in person_list:
        one = data[(data["person"] == person)]

        tumor = False
        normal = False
        tmp = pandas.DataFrame([])
        for j in range(len(one)):
            sample_type = one.iloc[j]["sample_type_name"]

            # apply barcode duplicate
            if sample_type >= 1 and sample_type <= 9:
                tmp = tmp.append(one.iloc[j])
                tumor = True
            if sample_type >= 10 and sample_type <= 19:
                tmp = tmp.append(one.iloc[j])
                normal = True

        if tumor == True and normal == True:
            download_list = download_list.append(tmp)
        else:
            print "[{disease}] remove from the list: {person}".format(disease = one.iloc[0]["disease"], person = person)
            
    download_list.to_csv(output_download, index = False, mode = "w", columns = output_summary_cols)
    
    
    ### ----- split summary & manifest -----
    data = download_list
    
    # create disease list
    data_tmp = data.sort(columns=["disease"])
    disease_list = data_tmp["disease"][(data_tmp["disease"].duplicated() == False)]

    # read manifest
    f = open(manifest)
    lines = f.readlines()
    f.close()
    # remove white-spaces and LRs
    manifest_text = ""
    for line in lines:
        manifest_text += line.strip().rstrip()
    root = ElementTree.fromstring(manifest_text)    
    
    # loop each disease
    for disease in disease_list:
        
        # extract data per disease
        data_di = data[(data["disease"] == disease)]
        
        # create person list
        data_tmp = data_di.sort(columns=["person"])
        person_list = data_tmp["person"][(data_tmp["person"].duplicated() == False)]
        
        split_sizes = split_list(len(person_list), persons = split_persons)
        print ("disease: " + disease + ", all persons: " + str(len(person_list)))

        # extract data for one file
        
        num_file = 0
        sum_persons = 0
        for split_size in split_sizes:

            counter = 0
            block = pandas.DataFrame([])
            
            for person in person_list[sum_persons:(sum_persons + split_size)]:
                
                block = block.append(data_di[(data_di["person"] == person)])
                counter += 1
                sum_persons += 1
            
            print ("disease: " + disease + ", index: " + str(num_file) + ", person number: " + str(split_size) + ", data lines: " + str(len(block)))
            
            ### split summary
            block.to_csv(output_summary + "/summary_" + disease + "_" + "%03d" % (num_file) + ".csv", index = False, mode = "w", columns = output_summary_cols)
            
            ### split manifest
            sp = split_manifest(root, block["analysis_id"])

            # shape to write format
            rough_string = ElementTree.tostring(sp, 'utf-8')
            reparsed = minidom.parseString(rough_string)
    
            # remove top "<?xml * ?>" line
            xml_text = reparsed.toprettyxml(indent="  ")
            first_lf = xml_text.find("\n")
            if len(xml_text) > 5:
                if (xml_text[0:5] == "<?xml") and (xml_text[(first_lf-2):first_lf] == "?>"):
                    xml_text = xml_text[(first_lf + 1):len(xml_text)]
            
            # write xml document
            f = open(output_manifest + "/manifest_" + disease + "_" + "%03d" % (num_file) + ".xml", "w")
            f.write(xml_text)
            f.close()

            num_file += 1
    
def split_manifest(root, analysis_list):
    
    now = datetime.datetime.now()
    t = "{0:0>4d}-{1:0>2d}-{2:0>2d} {3:0>2d}:{4:0>2d}:{5:0>2d}".format(now.year, now.month, now.day, now.hour, now.minute, now.second)

    top = ElementTree.Element('ResultSet')
    top.set('date', t)
    
    hits = ElementTree.Element('Hits')
    hits.text = str(len(analysis_list))
    top.append(hits)
    
    counter = 1
    for analysis in analysis_list:

        for result in root.findall('Result'):
            if result.find('analysis_id').text == analysis:
                top.append(result)
                counter += 1
                break
            
    return top


def split_list(leng, persons = 0, files = 0, persons_min = 0):
    """
    example1. leng = 12, persons = 5 -> return [6, 6]
    example2. leng = 12, files = 5 -> return [3, 3, 2, 2, 2]
    example2. leng = 12, files = 5, persons_min = 3 -> return [3, 3, 3, 3]
    """

    if persons == 0 and files == 0:
        return numpy.ones(1) * leng
        
    if files == 0:
        files = int(leng/persons)
        if files == 0:
            files = 1
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
