# genomon TCGA toolkit

注意：このツールはGenomic Data Commons - Data Portal専用です。

[genomon](https://github.com/Genomon-Project/GenomonPipeline)を使用するにあたって前準備を行うツール群です。

上から順に実行されることを想定していますが、単独でも動作可能です。

 1. check_bam.py      ........ ダウンロードしたbamをテストします。
 2. create_samplesheet.py       .... genomonで使用するsample sheetを作成します。

実行に必要なもの

 - python 2.7.x
 - Genomic Data Commons - Data Portalからダウンロードしたbamファイル
 - metadata.json ファイル（bamファイルをダウンロードする時、合わせて取得してください）

詳細は wiki [https://github.com/aokad/GenomonToolkit/wiki](https://github.com/aokad/GenomonToolkit/wiki) 参照

# check_bam.py

Genomic Data Commons - Data Portalからダウンロードしたbamファイルをテストします。

実行環境

 - python 2.7.x
 - samtools (samtools view が必要)
 - drmaa (DRMAA_LIBRARY_PATHの設定を忘れずに)

## テスト内容

 - md5: チェックサムをメタデータと比較します。
 - リード数：総リード数とシングルリード比率が許容範囲か確認します。
 - メタデータ：メタデータの内容を確認します。 (analyte_type, experimental_strategy, platform)

閾値等設定内容詳細はcheck_bam.cfgファイルを確認ください。

## インストール方法

このリポジトリをどうにかして取得します。

```
git clone https://github.com/aokad/GenomonTCGAkit.git

# もしくは

wget https://github.com/aokad/GenomonTCGAkit/archive/master.zip

# もしくは

wget https://github.com/aokad/GenomonTCGAkit/archive/v2.0.zip (作成予定)
# v1.0.zip はTCGA DataHub専用ですのでData Commonsでは使用できません。
```

圧縮ファイルは解凍します。インストールは必要ありません。

## 使い方

以下のように実行します。

```
python ckeck_bam.py {metadata.json} {bamのディレクトリ} {出力ディレクトリ}
```

設定ファイルは標準でckeck_bam.pyと同じディレクトリにあるcheck_bam.cfgファイルを使用します。

別の設定ファイルを使用する場合は `__config_file {config file}` で指定してください。

bamのディレクトリは以下ルートパスを指定してください。

```
{root}             <--- ココを指定
 ├ analysis_id1
 │ ├ bam file
 │ ├ bam index
 │ └ ...
 └ analysis_id2
    ├ bam file
    ├ bam index
    └ ...
```

metadata.jsonを基準にチェックしますので、metadata.jsonとbamのディレクトリに存在するbamファイルは同じ構成（数）であることが望ましいです。

 - metadata.jsonにないbamはチェックされません。
 - metadata.jsonにあるのに、実際にbamがないとチェック結果がエラーになります。（bamがないエラー）

## チェック結果

以下に出力されます。

{出力ディレクトリ}/TCGA-ACC2/result/result_check_bam_{実行した日付}.csv

1ファイルにつき、1行の結果で、先頭が判定結果です。使用OKであれば、"OK"と表示されます。
それ以外はNGです。

結果の例

```
result,analysis_id,md5_reference,md5_target,total_lines,single_lines,single_rate
0K,{analysis_id1},5a1c91ec6790d6e9472191c6f939c974,98981211,0,0.000
0K,{analysis_id2},4b857f6ef9b189cc1e74b56c25bb78da,105217978,0,0.000
0K,{analysis_id3},ee056fc3166c05699b2b2c5a7c28d824,100317586,0,0.000
```

NGの例

 - "not exist bam".......bamが存在しない
 - "check_error".........サブプロセス実行時の予期しないエラー
 - "unmatch checksum"....チェックサム不一致
 - "too few reads".......総リード数が少なすぎる
 - "single read".........シングルリード率が高すぎる
 - "{その他}"............メタデータの不一致 (analyte_type, experimental_strategy, platform)

# create_samplesheet.py

必要なもの

 - python 2.7.x
 - numpy
 - pandas

genomonで使用するsample sheetを作成します。

作業中です。
