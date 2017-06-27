# -*- coding: utf-8 -*-
"""
Created on Thu Nov 05 16:44:30 2015

@brief:  Common functions
@author: okada

$Id: subcode.py 120 2016-01-08 04:44:28Z aokada $
$Rev: 120 $
"""

# �t�@�C�������邩�`�F�b�N
def path_check(path, config):
    
    if config != None and config.has_option("MAIN", "path_check"):
        if config.getboolean("MAIN", "path_check") == False:
            return True
    
    import os
    return os.path.exists(path)

# ���ݎ����ŕ��������� (yyyy/mm/dd_HH/MM/SS)
def date_str():
    import datetime
    now = datetime.datetime.now()
    return "%04d%02d%02d_%02d%02d%02d" % (now.year, now.month, now.day, now.hour, now.minute, now.second)

# ���O�t�@�C����������
#   path    ���O�t�@�C���̃p�X
#   mode    �t�@�C���I�[�v�����[�h("w","a")
#   text    �o�͂�����������
#   date    (True/False) True�̎��͌��ݎ�����擪�ɂ���
#   printer (True/False) True�̎��̓R���\�[���ɂ��o�͂���

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

# config�̃��^�f�[�^�ݒ�l�ƈ�v���邩�`�F�b�N
#   config ConfigParser
#   option config�̃I�v�V�����Asection��METADATA�Œ�
#   value  ���݂̒l

def conf_match(config, option, value):

    # �ݒ荀�ڂ��Ȃ��ꍇ��True�ŕԂ�
    if config == None:
        return True
    if not config.has_option("METADATA", option):
        return True
    if config.get("METADATA", option) == "":
        return True
    
    # �ݒ�l����������ꍇ��,�ŋ�؂��ē��͂��Ă���
    # �ǂꂩ��ƈ�v�����True�ŕԂ�
    if value in config.get('METADATA', option).split(","):
        return True
    
    # �ݒ�l�������Ɛݒ肵�Ă���A��v���Ȃ��ꍇ�̂�False�ŕԂ�
    return False

# meta�f�[�^��ǂݍ���
# ���̂Ƃ��A�`�F�b�N���X�g��`�F�b�N���ڂ����킹�݂�
# OK�̂��̂�"data"�ŁANG�̂��̂�"invalid"�ŕԂ�

def load_metadata(metadata, bam_dir=None, config=None, check_result=""):
    import json
    
    # �`�F�b�N���X�gNG��bam���X�g���쐬
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

    read_data = json.load(open(metadata))
    data = []
    invalid = []
    for obj in read_data:
        analysis_id = obj["file_id"]
        
        # metadata �s��v
        if not conf_match(config, 'analyte_type', obj["cases"][0]["samples"][0]["portions"][0]["analytes"][0]["analyte_type"]):
            invalid.append([analysis_id, "analyte_type:%s" % (obj["cases"][0]["samples"][0]["portions"][0]["analytes"][0]["analyte_type"]])
            continue
        if not conf_match(config, 'is_ffpe', obj["cases"][0]["samples"][0]["is_ffpe"]):
            invalid.append([analysis_id, "is_ffpe:%s" % (obj["cases"][0]["samples"][0]["portions"][0]["analytes"][0]["analyte_type"]]))
            continue
        if not conf_match(config, 'experimental_strategy', obj["experimental_strategy"]):
            invalid.append([analysis_id, "experimental_strategy:%s" % (obj["experimental_strategy"]]))
            continue
        if not conf_match(config, 'platform', obj["platform"]):
            invalid.append([analysis_id, "platform:%s" % (obj["platform"]]))
            continue

        # �t�@�C�������݂��Ȃ�
        if path_check(bam_dir + "/" + analysis_id + "/" + obj["file_name"], config) == False:
            invalid.append([analysis_id, "not exist bam"])
            continue
        
        # �`�F�b�N���X�gNG�̂��̂͏��O
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
        tmp.append([obj["cases"][0]["samples"][0]["portions"][0]["analytes"][0]["aliquots"][0]["submitter_id"],
                    obj["cases"][0]["project"]["project_id"].replace("TCGA-", ""),
                    id_to_samplecode(int(obj["cases"][0]["samples"][0]["sample_type_id"])),
                    int(obj["cases"][0]["samples"][0]["sample_type_id"]),
                    obj["file_name"],
                    obj["file_id"],
                    obj["cases"][0]["samples"][0]["portions"][0]["analytes"][0]["aliquots"][0]["updated_datetime"],
        ])

    pdata = pandas.DataFrame(tmp)
    pdata.columns =["barcode", "disease", "sample_type", "sample_type_id", "filename", "analysis_id", "updated"]

    return pdata

def view1(files):
    import json
    
    for file_path in files:
        for obj in json.load(open(file_path)):
            if len(obj["associated_entities"]) > 1: 
                print ("%s\n" % (len(obj["associated_entities"])))
    
            if len(obj["cases"]) > 1: 
                print ("%s\n" % (len(obj["cases"])))
            if len(obj["cases"][0]["samples"]) > 1: 
                print ("%s\n" % (len(obj["cases"][0]["samples"])))
            if len(obj["cases"][0]["samples"][0]["portions"]) > 1: 
                print ("%s\n" % (len(obj["cases"][0]["samples"][0]["portions"])))
            if len(obj["cases"][0]["samples"][0]["portions"][0]["analytes"]) > 1: 
                print ("%s\n" % (len(obj["cases"][0]["samples"][0]["portions"][0]["analytes"])))
            if len(obj["cases"][0]["samples"][0]["portions"][0]["analytes"][0]["aliquots"]) > 1: 
                print ("%s\n" % (len(obj["cases"][0]["samples"][0]["portions"][0]["analytes"][0]["aliquots"])))
           
            if obj["cases"][0]["samples"][0]["portions"][0]["analytes"][0]["aliquots"][0]["submitter_id"] != obj["associated_entities"][0]["entity_submitter_id"]:
                print ("%s, %s\n" % (obj["cases"][0]["samples"][0]["portions"][0]["analytes"][0]["aliquots"][0]["submitter_id"], obj["associated_entities"][0]["entity_submitter_id"]))

def view2(files, output):
    import json
    
    fw = open(output, "w")
    fw.write("Project_id,barcode,Project,TSS(Tissue source site),Participant,Sample+Vial,Portion+Analyte,Plate,Center,updated,analyte_type,isFFPE,")
    fw.write("composition,created_datetime,current_weight,days_to_collection,days_to_sample_procurement,freezing_method,initial_weight,intermediate_dimension,is_ffpe,longest_dimension,oct_embedded,preservation_method,shortest_dimension,state,time_between_clamping_and_freezing,time_between_excision_and_freezing,tissue_type,tumor_code,tumor_code_id,tumor_descriptor\n")
    for file_path in files:
        for obj in json.load(open(file_path)):
            barcode = obj["associated_entities"][0]["entity_submitter_id"]
            fw.write("%s,%s,%s,%s,%s,%s,%s\n" % (
                       obj["cases"][0]["project"]["project_id"], 
                       barcode, 
                       barcode.replace("-", ","),
                       obj["cases"][0]["samples"][0]["portions"][0]["analytes"][0]["aliquots"][0]["updated_datetime"],
                       obj["cases"][0]["samples"][0]["portions"][0]["analytes"][0]["analyte_type"],
                       obj["cases"][0]["samples"][0]["portions"][0]["is_ffpe"],
                    "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s," % (
                    obj["cases"][0]["samples"][0]["composition"],
                    obj["cases"][0]["samples"][0]["created_datetime"],
                    obj["cases"][0]["samples"][0]["current_weight"],
                    obj["cases"][0]["samples"][0]["days_to_collection"],
                    obj["cases"][0]["samples"][0]["days_to_sample_procurement"],
                    obj["cases"][0]["samples"][0]["freezing_method"],
                    obj["cases"][0]["samples"][0]["initial_weight"],
                    obj["cases"][0]["samples"][0]["intermediate_dimension"],
                    obj["cases"][0]["samples"][0]["is_ffpe"],
                    obj["cases"][0]["samples"][0]["longest_dimension"],
                    obj["cases"][0]["samples"][0]["oct_embedded"],
                    obj["cases"][0]["samples"][0]["preservation_method"],
                    obj["cases"][0]["samples"][0]["shortest_dimension"],
                    obj["cases"][0]["samples"][0]["state"],
                    obj["cases"][0]["samples"][0]["time_between_clamping_and_freezing"],
                    obj["cases"][0]["samples"][0]["time_between_excision_and_freezing"],
                    obj["cases"][0]["samples"][0]["tissue_type"],
                    obj["cases"][0]["samples"][0]["tumor_code"],
                    obj["cases"][0]["samples"][0]["tumor_code_id"],
                    obj["cases"][0]["samples"][0]["tumor_descriptor"],
                    )
                    ))
    fw.close()
    
if __name__ == "__main__":
    pass
    
    #view1(["metadata.all_p1.json","metadata.all_p2.json","metadata.all_p3.json"])
    #view2(["metadata.all_p1.json","metadata.all_p2.json","metadata.all_p3.json"], "./barcodes.csv")
