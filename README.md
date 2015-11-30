# genomon toolkit

注意：このツールはCGHub専用です。

[genomon](https://github.com/Genomon-Project/GenomonPipeline)を使用するにあたって前準備を行うツール群です。

上から順に実行されることを想定していますが、単独でも動作可能です。

 1. [split_summary.py](#split_summary)    ............ summary.tsvとmanifest.xmlを分割します。
 2. [gt_surveillance.py](#gt_surveillance) ........... bamをダウンロードします。
 3. [check_singlebam.py](#check_singlebam)     ....... ダウンロードしたbamをテストします。
 4. [create_samplesheet.py](#create_samplesheet)   ... genomonで使用するsample sheetを作成します。
 
--------------------

# split_summary

CGHubからダウンロードしたsummary.tsvとmanifest.xmlを分割します。

diseaseごと、200人ごとに分割します。分割後のサンプル数は1人が持つサンプルの数によりますが、tumorとnormalが必ず存在するため、最少で400、最大で1000程度です。

※サンプル数が少ない場合等、この処理は必須ではありません。

## Dependency

python >= 2.7

## install

```
git clone {git PATH}
```

## Run

```
python {install path}/split_summary.py {output_dir} {summary file} {manifest file}
```

## Output directory

<pre>
{output root path}
 |-- /summary                  # 分割したサマリ
 |-- /manifest                 # 分割したマニフェスト
 |-- download_list.csv         # ダウンロード対象一覧
</pre>

PAADの実行例

<pre>
{output root path}
 |-- download_list.csv
 |-- manifest
 |     |-- manifest_PAAD_000.xml
 |     |-- manifest_PAAD_001.xml
 |     |-- manifest_PAAD_002.xml
 |     |-- manifest_PAAD_003.xml
 |-- summary
       |-- summary_PAAD_000.csv
       |-- summary_PAAD_001.csv
       |-- summary_PAAD_002.csv
       |-- summary_PAAD_003.csv
</pre>

download_list.csvの例

出力されるsummaryを全て結合したものです。

<pre>
person,study,barcode,disease,disease_name,sample_type,sample_type_name,analyte_type,library_type,center,center_name,platform,platform_name,assembly,filename,files_size,checksum,analysis_id,aliquot_id,participant_id,sample_id,tss_id,sample_accession,published,uploaded,modified,state,reason
TCGA-2J-AAB1,TCGA,TCGA-2J-AAB1-01A-11D-A40W-08,PAAD,Pancreatic adenocarcinoma,TP,1.0,DNA,WXS,BI,BI,ILLUMINA,Illumina,HG19_Broad_variant,C546.TCGA-2J-AAB1-01A-11D-A40W-08.1.bam,66304988253.0,9ff0af012e2fbbf2edd7c9bd443bf202,ea927d07-8129-4dcb-a0dc-bc86e33bca6c,3654586b-e1d2-42e7-8560-b339bd5e3488,75119d1a-93e5-4ae7-9d60-69ee929a0772,b83d846d-1b92-430c-a98e-352fcd24c0ab,2J, ,2015-02-12,2015-02-12,2015-04-14,Live,
TCGA-2J-AAB1,TCGA,TCGA-2J-AAB1-10A-01D-A40W-08,PAAD,Pancreatic adenocarcinoma,NB,10.0,DNA,WXS,BI,BI,ILLUMINA,Illumina,HG19_Broad_variant,C546.TCGA-2J-AAB1-10A-01D-A40W-08.2.bam,9382758709.0,b657e7af13dd1505844c9608456a554b,beec1eee-2b7a-4b06-ae40-eff0a84c7265,8a1fecb6-04f4-413a-bed8-63fce4ac7072,75119d1a-93e5-4ae7-9d60-69ee929a0772,17846bf5-52cf-413d-b028-5cba69d1309e,2J, ,2015-02-12,2015-02-12,2015-06-24,Live,
(略)
</pre>

--------------------

# gt_surveillance

download bam files from CGHub.

## Dependency

python >= 2.7

Python packages

 - drmaa

External script or binary.

 - gtdownload
 - xmlsplitter.pl

## install

```
git clone https://github.com/aokad/gt_surveillance.git
```

## Run

注意：通信が多くなるので、lmemで実行しましょう。

```
qlogin -l lmem
もしくは
ssh scl05 (or scl06)

export DRMAA_LIBRARY_PATH=/geadmin/N1GE/lib/lx-amd64/libdrmaa.so.1.0
python {install path}/gt_surveillance.py {output root path} {key file} {manifest download from CGHub}
```

## Output directory

<pre>
{output root path}
 |-- /data                  # downloaded bam files
 |-- /log                   # log files
 |-- /manifests             # manifests splitted 1
 |-- /scripts               # running scripts
</pre>

※ dataディレクトリについては、[TCGAのbamディレクトリ構成について](#about_bam_directory) 参照

<br />

--------------------

# check_singlebam

CGHubからダウンロードしたbamがシングルリードかどうかチェックします。

## Dependency

python >= 2.7

Python packages

 - drmaa

External script or binary.

 - samtools

## install

```
git clone {git PATH}
```

## Run

```
export DRMAA_LIBRARY_PATH=/geadmin/N1GE/lib/lx-amd64/libdrmaa.so.1.0
python {install path}/check_singlebam.py {path to working dir} {TCGA summary file} {path to bam dir} --config_file {option: config file}
```

※1: {TCGA summary file} … サマリーファイルについて 参照

※2: {path to bam dir} … [TCGAのbamディレクトリ構成について](#about_bam_directory) 参照

<br />

## Output directory

<pre>
{output root path}
 |-- /log                   # log files
 |-- /result                # チェック結果
 |-- /scripts               # running scripts
</pre>

<br />

## about_summary_file

サマリーファイルについて

CGHubからダウンロードしたファイルもしくはsplit_summaryで作成したファイルを指定しますが、以下フォーマットであれば使用できます。

<br />

|analysis_id|&nbsp;|filename|
|:-:|:-:|:-:|
|cebdbc7e-7063-4761-9fad-a79d3edbd8d1|&nbsp;|C317.TCGA-AB-2802-03B-01W-0728-08.1.bam|
|4495149d-5e25-43d4-b071-12e58c242e7d|&nbsp;|C317.TCGA-AB-2803-03B-01W-0728-08.1.bam|
|6bd3d988-ba8e-41b5-bcb9-8ad5014e2df5|&nbsp;|C317.TCGA-AB-2804-03B-01W-0728-08.2.bam|

<br />

 - ヘッダ必要
 - 列の並び順は不同
 - 上記内容をタブ区切り(.tsv)、もしくはカンマ [,] 区切り(.csv)で保存

--------------------

# create_samplesheet

genomonで使用するsummaryシートを作成します。

このとき、check_singlebamの結果ファイルを渡すと使用するbamを選別しますが、なければ選別しません。

## Dependency

python >= 2.7

## install

```
git clone {git PATH}
```

## Run

```
python {install path}/create_samplesheet.py {output_file} {summary file} {path to bam dir} {bam check_result file} --config_file {option: config file}
```

※1: {summary file} … サマリーファイルについて 参照

※2: {path to bam dir} … [TCGAのbamディレクトリ構成について](#about_bam_directory) 参照

<br />

## Output directory

<pre>
{output root path}
 |-- {sample sheet}          # sample sheet (csv format)
</pre>

<br />

## about_summary_csv

サマリーファイルについて

CGHubからダウンロードしたファイルもしくはsplit_summaryで作成したファイルを指定しますが、以下フォーマットであれば使用できます。

<br />

|barcode|disease|sample_type|sample_type_name|filename|analysis_id|published|modified|
|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
|TCGA-2J-AAB1-01A-11D-A40W-08|PAAD|TP|1|C546.TCGA-2J-AAB1-01A-11D-A40W-08.1.bam|ea927d07-8129-4dcb-a0dc-bc86e33bca6c|2015-02-12|2015-04-14|
|TCGA-2J-AAB1-10A-01D-A40W-08|PAAD|NB|10|C546.TCGA-2J-AAB1-10A-01D-A40W-08.2.bam|beec1eee-2b7a-4b06-ae40-eff0a84c7265|2015-02-12|2015-06-24|
|TCGA-2J-AAB4-10A-01D-A40W-08|PAAD|NB|10|C546.TCGA-2J-AAB4-10A-01D-A40W-08.1.bam|e26763b7-74ae-4c00-8bae-b8cc22648e99|2015-02-12|2015-06-11|

<br />

 - ヘッダ必要
 - 列の並び順は不同
 - 上記内容をタブ区切り(.tsv)、もしくはカンマ [,] 区切り(.csv)で保存


--------------------

# about_bam_directory

TCGAのbamディレクトリ構成について

CGHubからダウンロードしたbamは以下のディレクトリ構成になっています。

上記ツールでbamディレクトリを指定する際は以下の <font color=FF0099>{bam root path}</font> を指定してください。

<pre>
<font color=FF0099>{bam root path}</font>
 |-- {analysis_id 1}
 |     |-- {filename 1}
 |     |-- {filename 1}.bai
 |
 |-- {analysis_id 1}.gto
 |
 |-- {analysis_id 2}
 |     |-- {filename 2}
 |     |-- {filename 2}.bai
 |
 |-- {analysis_id 2}.gto
 |
 |-- {analysis_id 3}
 |     |-- {filename 3}
 |     |-- {filename 3}.bai
 |
 |-- {analysis_id 3}.gto
 </pre>

例

<pre>
<font color=FF0099>~/TCGA_SKCM/data/</font>
 |-- 09f5e55c-3c3f-47b6-8329-d0d83e40f69d
 |     |-- C828.TCGA-BF-A1PX-01A-12D-A19A-08.2.bam
 |     |-- C828.TCGA-BF-A1PX-01A-12D-A19A-08.2.bam.bai
 |
 |-- 09f5e55c-3c3f-47b6-8329-d0d83e40f69d.gto
 |
 |-- 0cb7ee60-c7b6-457a-a987-77a66daa05ba
 |     |-- C828.TCGA-BF-A1Q0-01A-21D-A19A-08.2.bam
 |     |-- C828.TCGA-BF-A1Q0-01A-21D-A19A-08.2.bam.bai
 |
 |-- 0cb7ee60-c7b6-457a-a987-77a66daa05ba.gto
 |
 |-- 108649a6-855e-4785-a8c6-c2eae09302ec
 |     |-- C828.TCGA-BF-A3DN-10A-01D-A20D-08.1.bam
 |     |-- C828.TCGA-BF-A3DN-10A-01D-A20D-08.1.bam.bai
 |
 |-- 108649a6-855e-4785-a8c6-c2eae09302ec.gto
</pre>

<br />

--------------------

# [infomation] sample code

https://tcga-data.nci.nih.gov/datareports/codeTablesReport.htm?codeTable=Sample%20type

|Code|Short Letter Code|Definition|
|:--:|:---------------:|:--------:|
|   1|  TP|Primary solid Tumor|
|   2|  TR|Recurrent Solid Tumor|
|   3|  TB|Primary Blood Derived Cancer - Peripheral Blood|
|   4|TRBM|Recurrent Blood Derived Cancer - Bone Marrow|
|   5| TAP|Additional - New Primary|
|   6|  TM|Metastatic|
|   7| TAM|Additional Metastatic|
|   8|THOC|Human Tumor Original Cells|
|   9| TBM|Primary Blood Derived Cancer - Bone Marrow|
|  10|  NB|Blood Derived Normal|
|  11|  NT|Solid Tissue Normal|
|  12| NBC|Buccal Cell Normal|
|  13|NEBV|EBV Immortalized Normal|
|  14| NBM|Bone Marrow Normal|
|  20|CELLC|Control Analyte|
|  40| TRB|Recurrent Blood Derived Cancer - Peripheral Blood|
|  50|CELL|Cell Lines|
|  60|  XP|Primary Xenograft Tissue|
|  61| XCL|Cell Line Derived Xenograft Tissue|


