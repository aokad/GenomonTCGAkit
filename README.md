# genomon TCGA toolkit

注意：このツールはGenomic Data Commons - Data Portal専用です。

[genomon](https://github.com/Genomon-Project/GenomonPipeline)を使用するにあたって前準備を行うツール群です。

上から順に実行されることを想定していますが、単独でも動作可能です。

 1. check_bam.py      ........ ダウンロードしたbamをテストします。
 2. create_samplesheet.py       .... genomonで使用するsample sheetを作成します。
 
詳細は wiki [https://github.com/aokad/GenomonToolkit/wiki](https://github.com/aokad/GenomonToolkit/wiki) 参照

# check_bam.py

Genomic Data Commons - Data Portalからダウンロードしたbamファイルをテストします。

詳細は wiki [https://github.com/aokad/GenomonToolkit/wiki/2.1_check_bam](https://github.com/aokad/GenomonToolkit/wiki/2.1_check_bam) 参照

## インストール方法

このリポジトリをダウンロードします。インストールは必要ありません。

## 使い方

以下のように実行します。

```
python ckeck_bam.py {metadata.json} {bamのディレクトリ} {出力ディレクトリ}
```

bamのディレクトリは以下bamダウンロード時のルートパスを指定してください。

## チェック結果

以下に出力されます。

{出力ディレクトリ}/TCGA-ACC2/result/result_check_bam_{実行した日付}.csv

1ファイルにつき、1行の結果で、先頭が判定結果です。使用OKであれば、"OK"と表示されます。
それ以外はNGです。

# create_samplesheet.py

必要なもの

 - python 2.7.x
 - numpy
 - pandas

genomonで使用するsample sheetを作成します。

作業中です。
