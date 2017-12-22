
<!-- README.md is generated from README.Rmd. Please edit that file -->
Salvage @datasci\_blogs's Tweets
================================

データ取得
----------

``` r
library(rtweet)
library(dplyr, warn.conflicts = FALSE)
library(purrr)
library(readr)
library(tidyr)
```

``` r
# 3200 is the limit of the API (c.f. https://developer.twitter.com/en/docs/tweets/timelines/api-reference/get-statuses-user_timeline)
tw <- get_timeline("datasci_blogs", n = 3200)
```

記事URLを取り出す
-----------------

### 記事URLがゼロ個のもの

URLが含まれないツイートは3200件中16件。無視。RSSの設定が間違ってた場合とか？

``` r
tw %>%
  filter(is.na(urls_expanded_url)) %>%
  pull(text)
#>  [1] "hatenablogとIFTTTの連携エラーを修正するために試行錯誤していたところ、登録データを誤って飛ばしてしまいましたので、本アカウントの活動は当面停止します。長らくありがとうございました。"                                     
#>  [2] "【Revolutions】 Estimating mean variance and mean absolute bias of a regression tree by bootstrapping using foreach and rpart packages …"                                                                               
#>  [3] "【Google Research Blog】 Highlights from the Annual Google PhD Fellowship Summit, and Announcing the 2017 Google PhD Fellows …"                                                                                         
#>  [4] "【糞ネット弁慶】 [論文] Modeling Consumer Preferences and Price Sensitivities from Large-Scale Grocery Shopping Transaction Logs (WWW 2017) 読んだ …"                                                                   
#>  [5] "【Blog - Applied Predictive Modeling】 Do Resampling Estimates Have Low Correlation to the Truth? The Answer May Shock You. …"                                                                                          
#>  [6] "【唯物是真 Scaled_Wurm】 A Parser-blocking, cross site (i.e. different eTLD+1) script, 「URL」, is invoked via document.write. …"                                                                                       
#>  [7] "【株式会社ホクソエムのブログ】 /2017/04/08/global-tokyor2/ Global Tokyo.Rに参加しました \n\n2017年4月1日、ドイツのRユーザ henningswayが東京へやって来るということで、Global Tokyo.R#2が開催されました。…"               
#>  [8] "【From Pure Math to Applied Math】 【Recsys2016】Adaptive, Personalized Diversity for Visual Discovery (AmazonStream)に関するメモ …"                                                                                    
#>  [9] "【learn data science - Medium】 Finding Similarities Among California Counties based on 2016 Election Result with dist, mds, and… …"                                                                                   
#> [10] "【suryu.me】 tidyverse脳になって階層構造のあるデータフレームを使いこなそう /post/r_advent_calendar_day3/ \n\nyutannihilationが書いたtidyverseの記事を眠気眼の状態で読んでしまって、眠気も吹き飛んで3時起きし…"          
#> [11] "【suryu.me】 configパッケージで楽々環境変数の管理 /post/r_advent_calendar_day2/ \n\nみなさん、Rの環境変数についてどのように管理されていますか？.Rprofileですか？それも良い方法です。ただ、Rprojectによるプロジェクト単…"
#> [12] "【suryu.me】 extrafont ggplot2で日本語ラベル (ver. 2.2.0 向け) /post/visualization_advent_calendar_day2/ \n\n一人visualizationの2日目（2つめの記事です。アドベントカレンダーとはなん…"                                  
#> [13] "【suryu.me】 Rで方位記号を描く (ggsn版) /post/rgis_advent_calendar_day2/ \n\n読んでいるブログの中でこんな記事を見ました。\n\nRで方位記号を描く\n\nこの記事では{prettymapr}というパッケージが使われているのですが、ちょ…"
#> [14] "【No Free Hunch】 A Challenge to Analyze the World’s Most Interesting Data: The Department of Commerce Publishes its Datasets on Kaggle …"                                                                             
#> [15] "【R code, simulations, and modeling】 R code for fitting a multiple (nonlinear) quantile regression model by means of a copula …"                                                                                       
#> [16] "【Cortana Intelligence and Machine Learning Blog】 Major Breakthroughs from Microsoft Research this Week <U+2013> in Conversational Speech, FPGA Acc…"
```

### 記事URLが1つのもの

そのまま使う

``` r
tw_list <- tw %>%
  select(status_id, created_at, urls_expanded_url, urls_t.co, text) %>%
  filter(!is.na(urls_expanded_url)) %>%
  split(map_int(.$urls_expanded_url, length) > 1)

urls_single <- map_chr(tw_list$`FALSE`$urls_expanded_url, 1)
```

### 記事URLが2つ以上のもの

`text`と照らし合わせて使う。

``` r
urls_double <- tw_list$`TRUE` %>%
  # メインのURLを取り出す
  mutate(urls_main = coalesce(
    stringr::str_match(text, "^【.*】 (https://t.co/[[:alnum:]]+) .*")[,2],
    stringr::str_match(text, "^【.*】 .* (https://t.co/[[:alnum:]]+)")[,2],
    stringr::str_match(text, stringr::regex("^【.*(https://t.co/[[:alnum:]]+)$", dotall = TRUE))[,2]
  )) %>%
  # それに対応するexpanded URLを取り出す
  pmap_chr(function(urls_main, urls_expanded_url, urls_t.co, ...) {
    unique(urls_expanded_url[urls_main == urls_t.co])
  })
```

### 結合して保存

``` r
urls <- c(urls_single, urls_double)
write_lines(urls, "urls.txt")
```

本当のURLを取得
---------------

ここはシェル芸でやった

``` sh
for URL in $(cat urls.txt); do
  curl -s -L -I $URL | \
  awk -v"OFS=," -v"short=$URL" '$1 == "Location:" {real=$2}; END{print short,real}' | \
  tail -1
done | tee real_urls.txt
```

参考までに、たぶんRでやるならこう。

``` r
library(curl)

get_location <- function(url, handle) {
  res <- curl_fetch_memory(url, handle = handle)
  parse_headers_list(res$headers)$location
}

h <- new_handle(followlocation = FALSE,
                customrequest = "HEAD",
                nobody = TRUE)

# WARNING: this takes several tens of minutes
r <- purrr::map(ifttt_urls, purrr::safely(get_location), handle = h)

# confirm there are no errors
purrr::keep(r, ~ !is.null(.$error))

ifttt_urls_table <- purrr::map_chr(r, "result")
```

スクレイピング行為に及ぶ前にURLをもうちょっと眺める
---------------------------------------------------

``` r
urls <- read_csv("real_urls.txt", col_names = c("short", "real"))
#> Parsed with column specification:
#> cols(
#>   short = col_character(),
#>   real = col_character()
#> )

urls_df <- tibble(urls = coalesce(urls$real, urls$short),
                  base_urls = stringr::str_extract(urls, "^https?://[^/]+/?"))

urls_df %>%
  count(base_urls, sort = TRUE) %>%
  filter(n > 1) %>%
  knitr::kable()
```

| base\_urls                                      |    n|
|:------------------------------------------------|----:|
| <http://blog.revolutionanalytics.com/>          |  387|
| <http://d.hatena.ne.jp/>                        |  234|
| <https://qiita.com/>                            |  200|
| <http://notchained.hatenablog.com/>             |  165|
| <https://blogs.technet.microsoft.com/>          |  144|
| <http://andrewgelman.com/>                      |  125|
| <https://research.googleblog.com/>              |  120|
| <https://www.karada-good.net/>                  |  100|
| <http://abrahamcow.hatenablog.com/>             |   94|
| <http://blog.kaggle.com/>                       |   83|
| <https://blog.rstudio.com/>                     |   78|
| <https://xianblog.wordpress.com/>               |   74|
| <http://rpubs.com/>                             |   73|
| <https://blog.exploratory.io/>                  |   72|
| <http://kivantium.hateblo.jp/>                  |   56|
| <https://waterprogramming.wordpress.com/>       |   55|
| <https://healthyalgorithms.com/>                |   53|
| <http://kiito.hatenablog.com/>                  |   49|
| <http://sucrose.hatenablog.com/>                |   46|
| <http://catindog.hatenablog.com/>               |   37|
| <http://dirk.eddelbuettel.com/>                 |   36|
| <http://soqdoq.com/>                            |   30|
| <http://tekenuko.hatenablog.com/>               |   27|
| <http://uribo.hatenablog.com/>                  |   27|
| <https://kazutan.github.io/>                    |   27|
| <http://doingbayesiandataanalysis.blogspot.jp/> |   25|
| <http://r-statistics-fan.hatenablog.com/>       |   25|
| <https://logics-of-blue.com/>                   |   25|
| <http://kamonohashiperry.com/>                  |   24|
| <http://yusuke-ujitoko.hatenablog.com/>         |   23|
| <http://hikaru1122.hatenadiary.jp/>             |   22|
| <http://varianceexplained.org/>                 |   22|
| <https://www.fisproject.jp/>                    |   22|
| <http://kosugitti.net/>                         |   21|
| <http://nonbiri-tereka.hatenablog.com/>         |   21|
| <http://statmodeling.hatenablog.com/>           |   21|
| <http://aidiary.hatenablog.com/>                |   20|
| <https://mrunadon.github.io/>                   |   20|
| <http://yutori-datascience.hatenablog.com/>     |   18|
| <http://id.fnshr.info/>                         |   16|
| <http://ill-identified.hatenablog.com/>         |   14|
| <http://musyoku.github.io/>                     |   14|
| <http://norimune.net/>                          |   14|
| <http://tjo.hatenablog.com/>                    |   14|
| <http://yamaguchiyuto.hatenablog.com/>          |   14|
| <http://www.buildingwidgets.com/>               |   13|
| <https://research.preferred.jp/>                |   13|
| <https://suryu.me/>                             |   13|
| <http://fastml.com/>                            |   12|
| <http://rindai87.hatenablog.jp/>                |   12|
| <http://xiangze.hatenablog.com/>                |   12|
| <http://mathetake.hatenablog.com/>              |   11|
| <http://www.yasuhisay.info/>                    |   11|
| <http://cordea.hatenadiary.com/>                |   10|
| <http://ito-hi.blog.so-net.ne.jp/>              |   10|
| <http://marugari2.hatenablog.jp/>               |   10|
| <https://fisproject.jp/>                        |   10|
| <http://blogs2.datall-analyse.nl/>              |    9|
| <http://estrellita.hatenablog.com/>             |    9|
| <http://rion778.hatenablog.com/>                |    9|
| <http://smrmkt.hatenablog.jp/>                  |    9|
| <http://uncorrelated.hatenablog.com/>           |    9|
| <https://ashibata.com/>                         |    9|
| <http://blog.hoxo-m.com/>                       |    8|
| <http://opisthokonta.net/>                      |    8|
| <https://martynplummer.wordpress.com/>          |    8|
| <http://appliedpredictivemodeling.com/>         |    7|
| <http://kkimura.hatenablog.com/>                |    7|
| <http://nekopuni.holy.jp/>                      |    7|
| <http://skozawa.hatenablog.com/>                |    7|
| <http://www.magesblog.com/>                     |    7|
| <https://darrenjw.wordpress.com/>               |    7|
| <https://mosko.tokyo/>                          |    7|
| <http://blog-jp.treasuredata.com/>              |    6|
| <http://syclik.com/>                            |    6|
| <http://threeprogramming.lolipop.jp/>           |    6|
| <https://wiseodd.github.io/>                    |    6|
| <http://bicycle1885.hatenablog.com/>            |    5|
| <http://nhkuma.blogspot.jp/>                    |    5|
| <http://takeshid.hatenadiary.jp/>               |    5|
| <http://www.unofficialgoogledatascience.com/>   |    5|
| <http://austinrochford.com/>                    |    4|
| <http://blog.gepuro.net/>                       |    4|
| <http://y-uti.hatenablog.jp/>                   |    4|
| <https://blog.albert2005.co.jp/>                |    4|
| <http://aaaazzzz036.hatenablog.com/>            |    3|
| <http://aial.shiroyagi.co.jp/>                  |    3|
| <http://keiku.hatenablog.jp/>                   |    3|
| <http://ktrmnm.github.io/>                      |    3|
| <http://laughing.hatenablog.com/>               |    3|
| <http://leeswijzer.hatenablog.com/>             |    3|
| <http://oscillograph.hateblo.jp/>               |    3|
| <http://pingpongpangpong.blogspot.jp/>          |    3|
| <http://shinaisan.hatenablog.com/>              |    3|
| <http://sinhrks.hatenablog.com/>                |    3|
| <http://takehiko-i-hayashi.hatenablog.com/>     |    3|
| <http://tatabox.hatenablog.com/>                |    3|
| <https://blog.recyclebin.jp/>                   |    3|
| <https://shapeofdata.wordpress.com/>            |    3|
| <http://blog.kz-md.net/>                        |    2|
| <http://blog.shakirm.com/>                      |    2|
| <http://ibisforest.blog4.fc2.com/>              |    2|
| <http://kazoo04.hatenablog.com/>                |    2|
| <http://machine-learning.hatenablog.com/>       |    2|
| <http://mockquant.blogspot.jp/>                 |    2|
| <http://nakhirot.hatenablog.com/>               |    2|
| <http://ouzor.github.io/>                       |    2|
| <http://triadsou.hatenablog.com/>               |    2|
| <http://wafdata.hatenablog.com/>                |    2|
| <http://yamano357.hatenadiary.com/>             |    2|
| <https://elix-tech.github.io/>                  |    2|
| <https://github.com/>                           |    2|
| <https://paintschainer.preferred.tech/>         |    2|

特別対応が必要そうなのは、

-   <http://d.hatena.ne.jp/>
-   <https://qiita.com/>
-   <http://rpubs.com/>

くらい。github.comになってるやつは明らかにミスってるけど、まあ2件だけなので無視。
