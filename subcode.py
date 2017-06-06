# -*- coding: utf-8 -*-
"""
Created on Thu Nov 05 16:44:30 2015

@brief:  Common functions
@author: okada

$Id: check_bam.py 120 2016-01-08 04:44:28Z aokada $
$Rev: 120 $
"""

def path_check(path, config):
    
    if config != None and config.has_option("MAIN", "path_check"):
        if config.getboolean("MAIN", "path_check") == False:
            return True
    
    import os
    return os.path.exists(path)
        
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
    
    black = []
    reasons = []
    if check_result != "":
        f = open(check_result)
        for row in f.readlines():
            cells = row.rstrip("\r\n").split(",")
            if cells[1] != "OK":
                black.append(cells[0])
                reasons.append(cells[1])
        f.close()
    
    # print (black)
    read_data = json.load(open(metadata))
    data = []
    invalid = []
    for obj in read_data:
        analysis_id = obj["file_id"]
        if not conf_match(config, 'analyte_type', obj["cases"][0]["samples"][0]["portions"][0]["analytes"][0]["analyte_type"]):
            invalid.append([analysis_id, obj["analyte"]["analyte_type"]])
            continue
        if not conf_match(config, 'experimental_strategy', obj["experimental_strategy"]):
            invalid.append([analysis_id, obj["experimental_strategy"]])
            continue
        if not conf_match(config, 'platform', obj["platform"]):
            invalid.append([analysis_id, obj["platform"]])
            continue
        if path_check(bam_dir + "/" + analysis_id + "/" + obj["file_name"], config) == False:
            invalid.append([analysis_id, "not exist bam"])
            continue
        if analysis_id in black:
            invalid.append([analysis_id, reasons[black.index(analysis_id)]])
            continue
        data.append(obj)
    return {"data": data, "invalid": invalid}

def id_to_samplecode(id):
    if id == 1: return "TP"
    if id == 2: return "TR"
    if id == 3: return "TB"
    if id == 4: return "TRBM"
    if id == 5: return "TAP"
    if id == 6: return "TM"
    if id == 7: return "TAM"
    if id == 8: return "THOC"
    if id == 9: return "TBM"
    if id == 10:return "NB"
    if id == 11:return "NT"
    if id == 12:return "NBC"
    if id == 13:return "NEBV"
    if id == 14:return "NBM"
    if id == 20:return "CELL"
    if id == 40:return "TRB"
    if id == 50:return "CELL"
    if id == 60:return "XP"
    if id == 61:return "XCL"

    return ""
    
def json_to_pandas(jdata):
    import pandas
    
    tmp = []    
    for obj in jdata:
        tmp.append([obj["associated_entities"][0]["entity_submitter_id"],
                    obj["cases"][0]["project"]["project_id"].replace("TCGA-", ""),
                    id_to_samplecode(int(obj["cases"][0]["samples"][0]["sample_type_id"])),
                    int(obj["cases"][0]["samples"][0]["sample_type_id"]),
                    obj["file_name"],
                    obj["analysis"]["analysis_id"],
                    obj["analysis"]["updated_datetime"],
                    obj["analysis"]["created_datetime"],
        ])

    pdata = pandas.DataFrame(tmp)
    pdata.columns =["barcode", "disease", "sample_type", "sample_type_id", "filename", "analysis_id", "published","modified"]

    return pdata
 
           
#import json
#load(json.load(open("metadata.all_p1.json")))
#load(json.load(open("metadata.all_p2.json")))
#load(json.load(open("metadata.all_p3.json")))

def load(data):
    for item in data:
        if len(item["associated_entities"]) > 1: 
            print ("%s\n" % (len(item["associated_entities"])))

        if len(item["cases"]) > 1: 
            print ("%s\n" % (len(item["cases"])))
        if len(item["cases"][0]["samples"]) > 1: 
            print ("%s\n" % (len(item["cases"][0]["samples"])))
        if len(item["cases"][0]["samples"][0]["portions"]) > 1: 
            print ("%s\n" % (len(item["cases"][0]["samples"][0]["portions"])))
        if len(item["cases"][0]["samples"][0]["portions"][0]["analytes"]) > 1: 
            print ("%s\n" % (len(item["cases"][0]["samples"][0]["portions"][0]["analytes"])))
        if len(item["cases"][0]["samples"][0]["portions"][0]["analytes"][0]["aliquots"]) > 1: 
            print ("%s\n" % (len(item["cases"][0]["samples"][0]["portions"][0]["analytes"][0]["aliquots"])))
       
        if item["cases"][0]["samples"][0]["portions"][0]["analytes"][0]["aliquots"][0]["submitter_id"] != item["associated_entities"][0]["entity_submitter_id"]:
            print ("%s, %s\n" % (item["cases"][0]["samples"][0]["portions"][0]["analytes"][0]["aliquots"][0]["submitter_id"], item["associated_entities"][0]["entity_submitter_id"]))
            
if __name__ == "__main__":
    pass
