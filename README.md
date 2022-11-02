# docomo mail to GMail Transfer tool
NTT docomoのキャリアメールであるドコモメールを、フォルダごとすべてGMailへ吸い出します。

# 新着通知
GMailはIMAPでメールを投入してもスマホに新着通知を送ってくれないので、以下2種類の通知を実装しています。
どちらもオプションで、設定がなければ行いません。

- Outlook.com に転送して、[Androidアプリ](https://play.google.com/store/apps/details?id=com.microsoft.office.outlook)に通知を飛ばしてもらう。
- Slackのincoming webhookを叩く

Outlook.comのAndroidアプリは新着通知がなぜかINBOXフォルダ(受信トレイ)しか飛ばないので、
ドコモメール側でどのフォルダに振り分けていてもOutlook.comのメールアカウントでは受信トレイに転送されます。

# 動かし方
Python3.5以上で動くはずです。`requirements.txt`を参考にパッケージを入れてください。

systemdで動かす際のServiceとTimerのUnit fileを参考までに添付してあります。

## コンテナでの起動

コンテナでは設定ファイルが`/conf/config.ini`に存在し、状態ファイルを`/state/laststate.json`に書きこめると期待して起動します。

`docker run -it --mount type=bind,source="$(pwd)"/conf,target=/conf,readonly --mount type=bind,source="$(pwd)"/state,target=/state ghcr.io/walkure/dgmtx:1.0.0`

# GMailのログイン情報について
GMailのIMAP接続は普通の`USER/PASS`ではログインできず、OAUTHBEARERを使う必要があります。
そのため、事前にGoogle Cloud PlatformでOAuth2.0認証情報を取得しておいてください。

cf. [OAuth2.0を使用してGoogleAPIにアクセスする](https://developers.google.com/identity/protocols/oauth2)

# 状態ファイルについて
終了時に、次回起動に備えて状態ファイルを保存します。ここにはドコモメールIMAPフォルダを何処まで読んだかの情報と、GMailへのアクセストークンが入っています。

# 参照
[ドコモメールをSIMフリースマホで使う - (｡･ω･｡)ノ･☆':*;':* ](http://www2.hatenadiary.jp/entry/2021/06/03/022857)

# AUTHOR
walkure at 3pf.jp

# LICENSE
MIT
