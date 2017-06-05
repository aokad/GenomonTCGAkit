# -*- coding: utf-8 -*-
"""
Created on Thu Nov 05 16:44:30 2015

@brief:  Common functions
@author: okada

$Id: check_bam.py 120 2016-01-08 04:44:28Z aokada $
$Rev: 120 $
"""

def date_str():
    import datetime
    now = datetime.datetime.now()
    return "%04d%02d%02d_%02d%02d%02d" % (now.year, now.month, now.day, now.hour, now.minute, now.second)
    
def write_log(path, mode, text, date, printer):
    import datetime
    
    t = ""
    if date == True:
        now = datetime.datetime.now()
        t = "{0:0>4d}/{1:0>2d}/{2:0>2d} {3:0>2d}:{4:0>2d}:{5:0>2d}: ".format(
                                now.year, now.month, now.day, now.hour, now.minute, now.second)

    f = open(path, mode)
    f.write(t + text + "\n")
    f.close()

    if printer == True:
        print (t + text)

def conf_match(config, option, value):
    if config == None:
        return True
    if not config.has_option("METADATA", option):
        return True
    if config.getstr("METADATA", option) == "":
        return True
    if value in config.getstr('METADATA', option).split(","):
        return True
    return False

def load_metadata(metadata, bam_dir=None, config=None, check_result=""):
    import json
    import os
    
    black = []
    reasons = []
    if check_result != "":
        f = open(check_result)
        for row in f.readlines():
            cells = row.split(",")
            if cells[1] != "OK":
                black.append(cells[0])
                reasons.append(cells[1])
        f.close()
        
    read_data = json.load(open(metadata))
    data = []
    invalid = []
    for obj in read_data:
        analysis_id = obj["analysis"]["analysis_id"]
        if not conf_match(config, 'analyte_type', obj["analyte"]["analyte_type"]):
            invalid.append([analysis_id, obj["analyte"]["analyte_type"]])
            continue
        if not conf_match(config, 'experimental_strategy', obj["experimental_strategy"]):
            invalid.append([analysis_id, obj["experimental_strategy"]])
            continue
        if not conf_match(config, 'platform', obj["platform"]):
            invalid.append([analysis_id, obj["platform"]])
            continue
        if bam_dir != None:
            if os.path.exists(bam_dir + "/" + analysis_id + "/" + obj["filename"]) == False:
                invalid.append([analysis_id, "not exist bam"])
                continue
        if analysis_id in black:
            invalid.append([analysis_id, reasons[black.index(analysis_id)]])
            continue
        data.push(obj)
    return {"data": data, "invalid": invalid}

def json_to_pandas(json):
    import pandas
    
    tmp = []    
    for obj in json:
        tmp.append([obj["barcode"], 
                    ])

    data = pandas.DataFrame([])
    data.columns =["barcode", "disease", "sample_type", "sample_type_name", "filename", "analysis_id", "published","modified"]

    return data
            
def test():
    return {"data": [1,2,3,4,5], "err": [12,3,4]}
    
if __name__ == "__main__":
    pass
