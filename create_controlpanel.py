# -*- coding: utf-8 -*-
"""
Created on Wed Nov 11 16:47:03 2015

@brief:  Create sample sheet from TCGA metadata.json for Genomon.
@author: okada

$Id: create_samplesheet.py 127 2016-01-22 02:17:18Z aokada $
$Rev: 127 $

@code
create_samplesheet.py {TCGA metadata.json} {path to bam dir} {path to output_sample.csv} --check_result {bam check_result file} --config_file {option: config file}
@endcode
"""
rev = " $Rev: 127 $"

import numpy

#############
#  samples
#############
# samplesはtumorとnormalの組み合わせのオブジェクト配列
# 以下オブジェクトで構成されていること
# {"sample": name, "person": id}
#
# personは同一人物で一意な文字列（もしくは数値） 
# 同一人物のnormalサンプルをcontrolpanelとして使用しないために用いる
#
# 例
# samples = [
#     {"sample": SAMPLE01_t, "person": sample01},
#     {"sample": SAMPLE02_t, "person": sample02},
#     {"sample": SAMPLE03_t, "person": sample03},
# ]

##############
#  controls
##############
# controlsはノーマルサンプルのオブジェクト配列
# samplesに入っているnormalでも、このリストに入っていないとコントロールパネルとして使用されない
# 最低20以上ないとエラー
# {"sample": name, "person": id}
#
# personはsamplesと同様
#
# 例
# controls = [
#     {"sample": SAMPLE01_n, "person": sample01},
#     {"sample": SAMPLE02_n, "person": sample02},
#     {"sample": SAMPLE03_n, "person": sample03},
# ]
#

#####################
#  return object
#####################
#
# 失敗したときはNone
#
# controlpanelは作成したコントールパネル
# tumor_controlpanelはtumorと作成したリストの対応
#
# 例：tumor4サンプルに対して、normal 21サンプル(ペア以外)設定したときの作成例
#
# {
#   'controlpanel': [
#     {'index': 0, 'samples': ['normal1', 'normal3', 'normal5', 'normal7', 'normal9', 'normal11', 'normal13', 'normal15', 'normal17', 'normal19', 'normal21', 'normal2', 'normal4', 'normal6', 'normal8', 'normal10', 'normal12', 'normal14', 'normal16', 'normal18']}, 
#     {'index': 1, 'samples': ['normal3', 'normal5', 'normal7', 'normal9', 'normal11', 'normal13', 'normal15', 'normal17', 'normal19', 'normal21', 'normal2', 'normal4', 'normal6', 'normal8', 'normal10', 'normal12', 'normal14', 'normal16', 'normal18', 'normal20']}
#   ], 
#   'tumor_controlpanel': {'tumor1': 0, 'tumor3': 0, 'tumor2': 1, 'tumor4': 1}
# }
#
def create_controlpanel(input_samples, input_controls):
    
    # samplesの重複確認
    sample_tmp = []
    control_tmp = []
    
    for sample in input_samples :
        sample_tmp.append(sample["sample"])
    
    for control in input_controls:
        control_tmp.append(control["sample"])
    
    sample_num = len(list(set(sample_tmp)))
    control_num = len(list(set(control_tmp)))
    
    if len(sample_tmp) != sample_num:
        print ("ERROR!!! Sample-name is duplicate. input samples num. = %d, non duplicate samples num. = %d" % (len(sample_tmp), sample_num))
        return None
   
    if len(control_tmp) != control_num:
        print ("ERROR!!! Control-name is duplicate. input controls num. = %d, non duplicate controls num. = %d" % (len(control_tmp), control_num))
        return None
    
    tmp = []
    tmp.extend(sample_tmp)
    tmp.extend(control_tmp)
    if (sample_num + control_num) != len(list(set(tmp))):
        print ("ERROR!!! Sample-name and control-name is duplicate.")
        return None
        
    # controlの数で処理を割りふる
    if control_num < 20:
        print ("ERROR!!! Too few control number.[%d]" % control_num)
        return None
        
    list_num = 0
    shift_range = 0
    if control_num == 20:
        list_num = 1
        shift_range = 0
        
    elif control_num < 40:
        list_num = 2
        shift_range = control_num-20

    else: # control_num >= 40
        capacity_list = split_list(control_num, persons = 20)
        list_num = len(capacity_list)
        shift_range = 20

    mix_samples = tools_mixturelist(input_samples, list_num)
    mix_controls = tools_mixturelist(input_controls, list_num)
    max_member = max(split_list(sample_num, files = list_num))
    return_obj = controlpanel_method2(mix_samples, mix_controls, max_member, shift_range)
    
    print ("written sample sheet. %d persons, %d controlpanel lists" % (len(input_samples), len(return_obj["controlpanel"])))
    print (return_obj)
    
    return return_obj

#
# コントールパネル作成　method2
#
# すでに作成したコントールパネルで満足できないか確認する
# 満足できないとき（自分を含む、定員オーバー）だけ自分を含まないコントールパネルを作る
# なるべくいろいろなサンプルを使うようにコントールパネルには定員を設け、新しいコントールパネルを作成するときは少しずらしてコントロールサンプルを使用開始する
# コントールの構成によっては定員を超えることもある
def controlpanel_method2(input_samples, input_controls, max_member, shift_range):

    create_controls = []
    panel_index = 0
    shift = 0
    tumor_panel = {}
    
    for tumor in input_samples:
        
        along = tools_alonglist(tumor, create_controls, max_member)
        if along != None:
            along["uses"] += 1
            tumor_panel[tumor["sample"]] = along["index"]
                
        else:
            already = None
            for retry in range(3):
                # 自分用のリストを作る
                new_obj = tools_selftlist(tumor, input_controls, shift)
    
                # 失敗したら終了
                if new_obj == None:
                    return None
    
                # 作ったリストが既存のものにないかチェック
                already = tools_samelist(new_obj, create_controls)
                if already == None:
                    break
                
                # 既存だったら1つシフトしてリトライ
                shift += 1
                if shift >= len(input_controls):
                    shift = shift - len(input_controls)
                
            if already == None:
                new_obj["index"] = panel_index
                new_obj["uses"] = 1    
                create_controls.append(new_obj)
                tumor_panel[tumor["sample"]] = panel_index
                panel_index += 1
                #print (new_obj);
                
            else:
                already["uses"] += 1
                tumor_panel[tumor["sample"]] = already["index"]
                
            shift += shift_range
            if shift >= len(input_controls):
                shift = shift - len(input_controls)
    
    return tools_format_obj(tumor_panel, create_controls)
    
#
# コントールパネル作成　method1
#
# とにかく自分を含まないコントールパネルを作る
# それで他のと被っていれば一緒にする
# なるべくいろいろなサンプルを使うようにサンプル毎に開始位置を1つずつシフトする
def controlpanel_method1(input_samples, input_controls):
    
    create_controls = []
    panel_index = 0
    shift = 0
    tumor_panel = {}

    for tumor in input_samples:
        
        # 自分用のリストを作る
        new_obj = tools_selftlist(tumor, input_controls, shift)
        
        # 失敗したら終了
        if new_obj == None:
            return None
        
        # 作ったリストが既存のものにないかチェック
        already = tools_samelist(new_obj, create_controls)
        if already != None:
            already["uses"] += 1
            tumor_panel[tumor["sample"]] = already["index"]
        
        else:
            new_obj["index"] = panel_index
            new_obj["uses"] = 1    
            create_controls.append(new_obj)
            tumor_panel[tumor["sample"]] = panel_index
            panel_index += 1
            print (new_obj);

        shift += 1
        if shift >= len(input_controls):
            shift = 0
    
    return_obj = {"tumor_controlpanel": tumor_panel, "controlpanel": create_controls}
    
    return return_obj

#
# コントールパネル作成　共通関数
#
# 自分を含まないコントールパネルを作る
def tools_selftlist(tumor, input_controls, shift):
    
    new_obj = {"index": -1, "samples": [], "persons": [], "uses": 0}
    for c in range(len(input_controls)):
        cs = shift + c
        if cs >= len(input_controls):
            cs = cs - len(input_controls)
        control = input_controls[cs]
        
        if tumor["person"] != control["person"]:
            new_obj["samples"].append(control["sample"])
            new_obj["persons"].append(control["person"])

        if len(new_obj["samples"]) >= 20:
            break
     
    # 作ったリストのメンバーが20未満の時は失敗
    if len(new_obj["samples"]) < 20:
        print ("ERROR!!! Too few control to this tumor: %s: person = %s, control num. = %d" % (tumor["sample"], tumor["person"], len(new_obj["samples"])))
        return None

    return new_obj

#
# コントールパネル作成　共通関数
#
# 作ったコントールパネルが既存のものにないかチェック
def tools_samelist(new_obj, create_controls):
    
    for li in create_controls:
        if sorted(list(set(new_obj["samples"]))) == sorted(list(set(li["samples"]))):
            return li
    
    return None        

#
# コントールパネル作成　共通関数
#
# 作ったコントールパネルが自分を受け入れられるかチェック
## 自分を含まないか
## 定員オーバーしていないか
def tools_alonglist(tumor, create_controls, max_member):
    
    for obj in create_controls:
        if tumor["person"] in obj["persons"]:
            continue
        if obj["uses"] >= max_member:
            continue
        
        return obj
    
    return None

#
# コントールパネル作成　共通関数
#
# コントールを渡された順に使用すると偏りが出るので、まんべんなく使用するように混ぜる
def tools_mixturelist(input_controls, list_num):
    
    import math
    
    # ex.作成するコントロールパネル数が3の時
    # [0,1,2,3,4,5,6,7,8,9,10,11]
    # -> [[0,3,6, 9]
    #      1,4,7,10]
    #      2,5,8,11]]
    # -> [0,3,6,9,1,4,7,10,2,5,8,11]
    
    control_num = len(input_controls)
    member = int(math.ceil(float(control_num) / float(list_num)))
    arr = numpy.arange(member * list_num).reshape((member, list_num)).T
    
    new_controls = []
    for row in arr:
        for i in row:
            #print i
            if i < control_num:
                new_controls.append(input_controls[i])
    
    return new_controls

#
# コントールパネル作成　共通関数
#
# 作成したコントールパネルを戻り値として整形する
def tools_format_obj(tumor_panel, create_controls):
    
    return_obj = { "tumor_controlpanel": tumor_panel }
    
    return_controls = []
    
    for obj in create_controls:
        return_controls.append({"index": obj["index"], "samples": obj["samples"]})
    
    return_obj["controlpanel"] = return_controls
    
    return return_obj
    
#
# コントールパネル作成　共通関数
#
# いいかんじに定員を割り振る
# leng 全構成数
#
# 以下2つはオプションでどちらか一つを指定する
#
# persons: 最小定員（要素の値）この数以上になるように分割する
#          要素数がいくつになるかはわからない
# files:   要素数がこの数になるよう分割する
#          定員がいくつになるかはわからない
#
# 定員に縛りがある場合
# split_list(103, persons = 20)
# -> array([21, 21, 21, 20, 20])
#
# 要素数に縛りがある場合
# split_list(103, files=2)
# -> array([52, 51])
#
def split_list(leng, persons = 0, files = 0):
    
    if persons == 0 and files == 0:
        return numpy.ones(1) * leng
        
    if files == 0:
        files = int(leng/persons)
    
    cols = numpy.zeros(0)
    
    while(1):
        if files < 1:
            break
        
        cols = _split_list(leng, files)
        if numpy.min(cols) >= persons:
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
    
    samples = [
        {"sample":"tumor1", "person": "p1"},
        {"sample":"tumor2", "person": "p2"},
        {"sample":"tumor3", "person": "p3"},
        {"sample":"tumor4", "person": "p4"},
    ] 

    controls = [
        {"sample":"normal1", "person": "pp1"},
        {"sample":"normal2", "person": "pp2"},
        {"sample":"normal3", "person": "pp3"},
        {"sample":"normal4", "person": "pp4"},
        {"sample":"normal5", "person": "pp5"},
        {"sample":"normal6", "person": "pp6"},
        {"sample":"normal7", "person": "pp7"},
        {"sample":"normal8", "person": "pp8"},
        {"sample":"normal9", "person": "pp9"},
        {"sample":"normal10", "person": "pp10"},
        {"sample":"normal11", "person": "pp11"},
        {"sample":"normal12", "person": "pp12"},
        {"sample":"normal13", "person": "pp13"},
        {"sample":"normal14", "person": "pp14"},
        {"sample":"normal15", "person": "pp15"},
        {"sample":"normal16", "person": "pp16"},
        {"sample":"normal17", "person": "pp17"},
        {"sample":"normal18", "person": "pp18"},
        {"sample":"normal19", "person": "pp19"},
        {"sample":"normal20", "person": "pp20"},
        {"sample":"normal21", "person": "pp21"},
    ]
    
    create_controlpanel(samples, controls)
    

