# genomon toolkit

注意：このツールはCGHub専用です。

[genomon](https://github.com/Genomon-Project/GenomonPipeline)を使用するにあたって前準備を行うツール群です。

上から順に実行されることを想定していますが、単独でも動作可能です。

 1. [split_summary.py](#split_summary)    ............ summary.tsvとmanifest.xmlを分割します。
 2. [gt_surveillance.py](#gt_surveillance) ........... bamをダウンロードします。
 3. [check_singlebam.py](#check_singlebam)     ....... ダウンロードしたbamをテストします。
 4. [create_samplesheet.py](#create_samplesheet)   ... genomonで使用するsample sheetを作成します。
 
詳細は wiki [https://github.com/aokad/GenomonToolkit/wiki](https://github.com/aokad/GenomonToolkit/wiki) 参照
