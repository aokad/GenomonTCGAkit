# genomon toolkit

注意：このツールはGenomic Data Commons Data Portal専用です。

[genomon](https://github.com/Genomon-Project/GenomonPipeline)を使用するにあたって前準備を行うツール群です。

上から順に実行されることを想定していますが、単独でも動作可能です。

 1. <s>split_summary.py    ............ summary.tsvとmanifest.xmlを分割します。</s>
 2. <s>gt_surveillance.py  ............ bamをダウンロードします。</s>
 3. check_bam.py      ........ ダウンロードしたbamをテストします。
 4. create_samplesheet.py       .... genomonで使用するsample sheetを作成します。
 
詳細は wiki [https://github.com/aokad/GenomonToolkit/wiki](https://github.com/aokad/GenomonToolkit/wiki) 参照
