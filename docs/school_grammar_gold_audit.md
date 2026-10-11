# 高校英文法に基づく暫定正解データの監査（第1回）

対象：A由来 G001–G040 / T041–T060 / T061–T070。H071–H080 は英文のみで gold 未登録。
**本書はレビュー記録であり、既存の gold JSON は変更していない。**
判定基準：高校英語の五文型を基本に、主節の中心語（名詞修飾の節・句は除外）、助動詞を含むV、等位接続・省略・形式主語/目的語・従属節は別注記。品詞依存解析の出力を文法的正解と同一視しない。

## まず確認した問題・留保（確定goldへの昇格は保留）
| ID | 現行暫定値 | 論点と要対応 |
|---|---|---|
| G038 | V=opened; O=the door | **確定規約：SVO + VO の述部等位接続**。She を共有し、(opened, the door) と (entered, the room) を and が接続。CONJ は SVOCM に含めない。 |
| G039 | C=smart | **確定規約：SVC + C の補語等位接続**。smart と careless を but が接続。sometimes は careless を修飾する副詞。CONJ は SVOCM に含めない。 |
| G040 | C=surprisingly difficult to understand | 「C全体」と「Cの核（difficult）」の境界を分ける。surprisingly は副詞、to understand は形容詞を補う不定詞。 |
| T051 | She was given a beautiful necklace | 受動態の SVO/O の扱いは高校文法で説明が分かれる。能動態の間接目的語が受動態主語になり、残る a beautiful necklace を O とする分析を採用するか、受動態の残存目的語として別ラベルにするか要規約。 |
| T048, T064 | It was John/the proposal that ... | 強調構文（cleft）の It を形式的 S、焦点名詞句を C とする分析は**教育上の便宜的分析**。強調構文と単純な SVC を同一視しない。焦点と元の文の文法役割を別記録。 |
| G026–G027 | There are/was ... ; S=後続名詞句 | 存在構文の there は形式上の主語とする記述もある。アプリでは意味上のS=後続名詞句とする独自規約を明記し、形式上の there を保持。 |
| G028–G030, T062, T065, T068 | It が S/O | 形式主語・形式目的語と、後続する真主語・真目的語（内容節／不定詞）の対応関係を明記。G029/T068の that 節を未記録のままにしない。 |
| T063 | C=examine the system | have + O + 原形不定詞を OC とみなす場合、Cの核=examine と、C全体=examine the system immediately を区別。 |
| T066 | C=complicated; M=far, less, than ... | 比較級 less complicated を C全体に含めるか、C核=complicated＋程度修飾とするか統一。『far less complicated』の構造と than 節の係り先を記録。 |
| T070 | C=the possibility | 後続 that 節は possibility の内容を示す同格節。C核とC全体の違い、関係詞節との区別を記録。 |

## 確認すべき共通ルール
1. **役割と範囲を別フィールドにする**：S/O/C は中心部の連続範囲と、修飾語を含む句全体の双方を保存。採点用の許容範囲を明示する。
2. **等位接続**：同一主語の複数V、複数O、複数Cを保存。G038/G039 を回帰テストにする。
3. **節階層**：主節のSVOCと従属節内部のSVOCを別々に採点。主節に含めない修飾節を捨てずに関連付ける。
4. **準動詞**：to不定詞・動名詞・分詞は高校文法上の名詞/形容詞/副詞用法を記録。動詞の語彙的補部（decide to do など）の学校文法上の扱いを固定。
5. **形式語**：形式主語/形式目的語、存在 there、強調構文を独立タグとして保存。表面上のSと意味上の主語を混同しない。
6. **副詞**：CやOの核に含めず、句全体には必要に応じて含める。否定語 not のVへの含め方を別規約として統一。
7. **曖昧性**：文法書によって分析が分かれる場合、正解を一つに強制せず「採用規約」「代替分析」「判定保留」を記録する。
8. **品質状態**：unreviewed / reviewed_with_convention / disputed / verified のように段階管理。現段階では「高校文法と照合済み」でも、独立監修済みとは呼ばない。

## 次回監査
残りの各文について S/V/O/C/M と節・修飾語の位置を逐語照合し、IDごとに判定・根拠・修正案を残す。合意が得られるまで既存goldを書き換えない。

## 確定した接続詞の出力規約（ユーザー承認）
- 接続詞は **CONJ** として独立表示し、S/V/O/C/M のいずれにも含めない。
- 接続種別（等位・従属）、接続語の文字列・token範囲、接続する左右の対象（役割・token範囲・節ID等）を保存する。
- 共通のSやVなど、省略・共有される要素を明示する。接続対象が曖昧なら推測で確定せず review にする。
- G038: `She opened the door and entered the room.` → `S + (V1 O1 and V2 O2)`。and は述部同士を接続、S=She を共有。
- G039: `He is smart but sometimes careless.` → `S V + (C1 but C2)`。but は補語同士を接続、sometimes は careless にかかる副詞。
- 出力構造の例：`conjunctions: [{text, type, left:{role,token_ids}, right:{role,token_ids}, shared_roles, status}]`。この例は仕様案であり、現行コード実装済みとは限らない。

## 確定規約：前置・後置修飾と分詞（ユーザー承認、補足付き）
1. **前置修飾**：名詞の前に置かれる形容詞・分詞などは名詞句の一部として、S/O/Cの中心範囲に含める（例：the **sleeping** baby）。
2. **後置修飾**：名詞を後ろから限定・説明する関係詞節、分詞句、前置詞句、不定詞句などは、S/O/Cの中心範囲から除外し、修飾句・修飾節として独立保存する。修飾先を記録する。
3. **補語としての分詞**：S/Oの状態や動作を叙述する分詞はCに分類する（例：I saw the baby **sleeping** → O=the baby, C=sleeping）。「後置にある」「修飾先が見当たらない」だけではCとしない。OとCの叙述関係などを確認する。
4. **動詞句としての分詞**：進行形・受動態を作る分詞は助動詞と合わせVとして扱う（例：The baby **was sleeping** → V=was sleeping）。
5. **判定保留**：後置修飾かCか複数分析が成立する場合は一意に決めず、曖昧性を保存し診断問題から除外する。
6. **正解範囲と情報保持**：修飾句を中心範囲から除外しても、修飾関係そのものは破棄しない。中心範囲と句全体を区別して保存する。

適用例：G002（The tall boy）、G011–G015（関係詞節）、G036–G037（後置分詞）、T053（知覚動詞+O+C）、T061/T067（関係詞節を含むO/S）など。これらのgold本体は監査完了まで変更しない。


## 確定規約：形式主語・形式目的語（ユーザー承認）
- 形式主語構文は表面上の主節 S = `It` として採点し、後続の真主語（to不定詞句・that節・whether節など）を **別フィールド** に保持する。例：`It is important to learn English.` → S=It, V=is, C=important, real_subject=to learn English。
- 形式目的語構文は主節 O = `it` として採点し、後続の真目的語（不定詞句・節など）を **別フィールド** に保持する。例：`We found it difficult to solve the problem.` → S=We, V=found, O=it, C=difficult, real_object=to solve the problem。
- 形式語と真の内容の対応関係を `formal_real_links` のような構造に保持する。真主語・真目的語を追加の主節 S/O として二重計上しない。
- ただし、すべての `It` を形式主語とみなさない。天候・時間・距離などの非人称it、通常の代名詞it、強調構文のitを区別する。真主語・真目的語が特定できない場合は review。
- 該当例：G028, G029, G030, T056, T062, T065, T068。強調構文 G048（実際はT048）, T064 は別規約で監査する。
- 既存のgold JSONはこの記録段階では変更しない。


## 確定規約：準動詞と O/C（ユーザー承認）
高校英文法の五文型をアプリ内の採点規約として採用する（文法書により異なる分析があり得る）。
- `I want to leave.` → S=I, V=want, O=to leave（主節SVO）。
- `He decided to leave early.` → S=He, V=decided, O=to leave early（主節SVO）。
- `I enjoy playing tennis.` → S=I, V=enjoy, O=playing tennis（主節SVO）。
- `She made him clean the room.` → S=She, V=made, O=him, C中心=clean, C全体=clean the room。the room はC内の不定詞相当の動詞句のOとして保存する。
- `I saw him running.` → S=I, V=saw, O=him, C=running。
- `She wants him to study.` → S=She, V=wants, O=him, C=to study。
- **階層を分離**：主節のS/V/O/Cと、準動詞句内部のS（意味上の主語）・V・O・C・修飾語を混同しない。Cの中心語とC全体の範囲を別々に保持する。
- **自動適用の条件**：不定詞を常にOにしない。動詞の語法・文型で判定し、名詞修飾・副詞的用法・補語用法等は区別する。曖昧な例はreviewとし採点対象から除外する。
- 監査候補：G019, G031, G033, G034, T052, T053, T059, T063, T067。該当可否・既存goldとの差分は各例を読んで確定する。現段階ではgold JSON本体を変更しない。


## 確定規約：倒置・疑問文の語順（ユーザー承認）
- **SVOCは語順ではなく文法機能で決める**。疑問文、否定語倒置、only句倒置、仮定法の倒置などでも、主語・述語動詞の機能を優先する。
- 例：`Never have I seen such a beautiful view.` → S=I, V=have seen, O=such a beautiful view。never は否定副詞、倒置の誘因。
- 助動詞と本動詞が離れて現れる場合、Vを **複数token範囲** として記録する（例：have / seen）。英文上の非連続語を一つの連続範囲としてタップさせない。
- 疑問文例：`What did she buy?` → S=she, V=did buy, O=What（疑問詞は文頭でもO）。語順と役割を別管理する。
- **診断UI**：非連続のVは複数範囲の選択を認めるか、当該問題を出題保留にする。連続範囲しか選択できない現行UIを前提に誤答扱いしない。
- 倒置かどうか不確かな構文はreviewとし、確定正解として使わない。構文検出結果はSVOC採点と独立保存する。
- 監査候補：否定語・限定表現の倒置、仮定法倒置、疑問文等。各データセットの該当IDは全文照合後に確定する。gold JSON本体とmainは変更しない。


## 確定規約：主節と従属節（ユーザー承認）
- **節ごとにS/V/O/Cを独立記録**し、主節と従属節を混在させない。各節にID、種別（main/subordinate）、親節、接続詞・関係詞、修飾・補充先の参照を持たせる。
- 例：`When I arrived home, my mother was cooking dinner.` → 主節 S=my mother, V=was cooking, O=dinner。従属副詞節 `When I arrived home` 内は S=I, V=arrived。when は節を導く接続詞として記録する。
- 従属節全体の機能（名詞節・形容詞節・副詞節）を記録し、主節内の役割・修飾先を明示する。**名詞節が主節O/S/Cとなる場合は、節全体の主節役割と節内部のSVOCを別階層に記録する**（単に主節から一律除外しない）。
- 既決の後置修飾規約と整合させ、関係詞節等が名詞を修飾する場合は名詞句の中心範囲から除外し、修飾関係を別保存する。
- 節の境界・主従関係が一意でない場合はreview。既存gold JSON本体およびmainは変更しない。


## 確定規約：存在構文 There is / are（ユーザー承認）
- 存在構文の導入語 `there` は **Sに含めない**。存在を表すbe動詞（必要なら助動詞も）はV、後続の存在物を表す名詞句をSとして記録する。
- 例：`There are three books on the desk.` → introductory_there=There, V=are, S=three books, M=on the desk（場所を表す修飾句）。
- 例：`There is a book that I bought yesterday.` → S=a book, V=is、`that I bought yesterday` は book を修飾する後置関係詞節として別保存する。節内部のSVOCも別記録。
- `there` が場所を指す副詞の場合は存在構文の導入語と混同しない。文型や名詞句境界が曖昧な場合はreview。
- 監査対象候補：G026, G027。既存gold JSON本体とmainは変更しない。


## 確定規約：受動態と残存目的語（ユーザー承認）
- 受動態の助動詞・be動詞と過去分詞をまとめてVとする。
- **受動態でも、動詞の後ろに目的語が残る場合は主節Oとして記録する**。例：`He was given a book.` → S=He, V=was given, O=a book。
- 目的語が残らない受動態ではOを補わない。例：`The book was written by her.` → S=The book, V=was written, O=なし、`by her` は動作主を示す前置詞句として別保存する。
- 受動態の種類や動詞の語法を踏まえて判定し、過去分詞の形だけで受動態と断定しない。曖昧な場合はreview。
- 監査候補：T051ほか。既存gold JSON本体とmainは変更しない。


## 確定規約：比較・強調・特殊構文（ユーザー承認）
- 特殊構文でも**主節のSVOCを明示**し、比較・強調・相関・倒置などの構文種別と、対応する構成要素・範囲を別フィールドに記録する。一般的なSVOCだけでは構造を説明しきれない場合は、その限界を明示する。
- 強調構文の例：`It was John who broke the window.` → 学習用の表面分析 S=It, V=was, C=John とし、`who broke the window` を強調構文の節として別保存する。通常のSVCと同一視せず、強調対象 John と強調構文であることを必須記録する。
- 比較構文では、比較の程度・比較対象・比較の範囲と、対応する語句・節の関係を保存する。比較表現を安易に主節O/Cへ割り当てない。
- `the more ..., the more ...`、`no sooner ... than ...` など、複数部分の対応で成立する構文は、構成要素を別々に識別し関連付ける。解析が曖昧な場合はreviewとして採点対象から除外する。
- 監査候補：T048, T064（強調）、T066（比較）、T070（同格節など別構文との区別）、その他該当文。gold JSON本体・main・本番は変更しない。


## 追加確定規約：G029・G040および構造参照（ユーザー承認）

承認範囲：**この監査文書への記録のみ**。既存の `tests/data/parser_gold_40.json` を含む gold JSON、実験A/B、main、本番アプリは変更しない。以下は採用する学校文法上の注釈規約であり、現行解析器の実装済み機能を意味しない。

### G029 — It seems that he is honest.
- 主節：S=`It`（形式主語として扱う）、V=`seems`、C=なし。
- `that he is honest` を真主語相当の内容節として別フィールドに保存する。節内部は S=`he`、V=`is`、C=`honest`。
- `It seems that ...` の that 節を内容節として分析する別解もあるため、これは**本アプリの学校文法上の採用規約**であり、普遍的な唯一解とはしない。代替分析・採用規約の識別を保存する。
- 既存goldの `main.S=It`、`main.V=seems`、`main.C=null` はこの段階で書き換えない。

### G040 — The book that my teacher recommended yesterday was surprisingly difficult to understand.
- 主節：S中心=`The book`、V=`was`、C中心=`difficult`、C全体=`surprisingly difficult to understand`。
- `surprisingly` は `difficult` を修飾する程度副詞。`to understand` は形容詞 `difficult` を補う不定詞句として別保存する。
- `that my teacher recommended yesterday` は `book` を修飾する関係詞節で、主節Sの中心範囲には含めない。
- `understand` の意味上の目的語は主節Sの `the book` と対応するため、欠落要素と先行詞の参照関係を保存する。
- 既存goldのC全体の文字列はこの段階で書き換えない。

### 追加共通ルール 1：欠落要素の参照
- 関係詞節・不定詞句などの内部で表面上現れないS/O等について、文法的に同定できる場合のみ、役割・参照先・根拠を記録する（例：G040 `understand` のO ↔ `the book`）。
- 一意に確定できない場合は推測で補わずreviewとする。表面上の主節SVOCに欠落要素を重複追加しない。

### 追加共通ルール 2：修飾先の明示
- 副詞・前置詞句・分詞句等の修飾要素は、表面範囲、修飾先の語句または節、修飾関係を別保存する。
- S/O/Cの中心範囲と句全体の区別を保つ。修飾先が曖昧ならreviewとする。

### 追加共通ルール 3：共有要素の明示
- 等位接続で共有される主語・動詞等と、準動詞句の意味上の主語を**別種の関係**として記録する。
- 例：G038の `She` は二つの述部で共有される主語。一方、不定詞句等の意味上の主語は、その句の内部構造との関係として記録する。
- 接続詞自体は既定どおりCONJとして独立保持し、SVOCMには混入させない。

**状態：規約承認済み／gold本体未修正／実装・自動テスト未検証。**


## G001–G040 逐文監査：承認規約に基づく改訂候補（gold本体は未変更）

**監査の読み方**：以下の「維持」は現行 `main.S/V/O/C` の文字列が採用規約と整合することを意味し、全構造の記録完了や独立監修済みを意味しない。「追加」は別階層の節・修飾語・参照関係等が必要なこと、「構造修正」は現行主節の役割配列では必要な並列要素が欠落することを意味する。全40件の `review_status` は現行goldでは `pending` のまま。以下は**文書上の監査提案**であり、goldの更新・実装・テスト結果ではない。

| ID | 判定 | 現行主節SVOCの照合と必要な記録・理由 |
|---|---|---|
| G001 | 維持 | She/is/happy の SVC。追加必須事項なし。 |
| G002 | 追加 | S=The tall boy（前置形容詞 tall を含む）、V=runs は維持。fast は runs を修飾する副詞M。 |
| G003 | 維持 | I/read/a book の SVO。 |
| G004 | 維持 | She/gave/me/a book の SVOO。間接O=me、直接O=a book を区別。 |
| G005 | 維持 | I/found/the book/useful の SVOC。OとCの叙述関係を記録。 |
| G006 | 追加 | S=The dog、V=barked は維持。loudly をV修飾のMとして記録。 |
| G007 | 維持 | My father/is/a doctor の SVC。 |
| G008 | 維持 | We/watched/the movie の SVO。 |
| G009 | 維持 | They/elected/him/president の SVOC。OとCの叙述関係を記録。 |
| G010 | 維持 | The teacher/showed/us/a picture の SVOO。間接Oと直接Oを区別。 |
| G011 | 追加 | 主節S=The man、V=leftを維持。who smiled はmanを修飾する関係節、節内S=who、V=smiled。 |
| G012 | 追加 | 主節S=The boy、V=runs。who lives here はboyを修飾し、節内S=who、V=lives、here=M。主節fastもM。 |
| G013 | 追加 | 主節S=The book、V=was、C=expensive。関係節that I bought yesterdayはbookを修飾し、S=I、V=bought、O=that（先行詞book参照）、yesterday=M。 |
| G014 | 追加 | 主節S=The woman、V=is、C=a scientist。関係節whom we met yesterdayはwomanを修飾し、S=we、V=met、O=whom（先行詞woman参照）、yesterday=M。 |
| G015 | 追加 | 主節S=The house、V=has disappeared。where I grew up はhouseを修飾し、S=I、V=grew up、whereは場所を表す関係副詞。 |
| G016 | 追加 | 主節S=my mother、V=was cooking、O=dinner。When I arrived home は時の副詞節、節内S=I、V=arrived、home=場所M、When=従属接続詞。 |
| G017 | 追加 | 主節S=we、V=stayed、inside=M。Because it was raining は理由節、S=it、V=was raining、Because=従属接続詞。 |
| G018 | 追加 | 主節S=you、V=will improve。If you study hard は条件節、S=you、V=study、hard=M、If=従属接続詞。 |
| G019 | 追加 | 主節S=he、V=continued、O=workingを維持。Although he was tired は譲歩節（S=he、V=was、C=tired）。workingは動名詞Oで、意味上の動作主は主節he。 |
| G020 | 追加 | 主節S=I、V=will call、O=you。after I finish my homework は時の副詞節、S=I、V=finish、O=my homework、after=従属接続詞。 |
| G021 | 追加 | 主節S=I、V=think、O=that she is right。Oの名詞節内部はS=she、V=is、C=right。thatは節導入要素として別記録。 |
| G022 | 追加 | 主節S=What he said（名詞節全体）、V=surprised、O=everyone。節内部S=he、V=said、O=What。 |
| G023 | 追加 | 主節S=I、V=know、O=where she lives。節内部S=she、V=lives、whereは場所を表す疑問副詞。 |
| G024 | 追加 | 主節S=That he passed the exam（名詞節全体）、V=is、C=surprising。節内部S=he、V=passed、O=the exam。 |
| G025 | 追加 | 主節S=She、V=asked、O=whether I was ready。節内部S=I、V=was、C=ready、whetherは節導入要素。 |
| G026 | 追加 | 存在構文：導入thereはSに含めず、S=many books、V=areを維持。on the deskは場所M。 |
| G027 | 追加 | 存在構文：導入thereはSに含めず、S=a problem、V=wasを維持。with the plan はproblemの後置修飾として別記録（主節S中心には含めない）。 |
| G028 | 追加 | S=It、V=is、C=importantを維持。to learn Englishを真主語として関連付け、内部V=learn、O=Englishを保存。 |
| G029 | 追加・承認済み | S=It、V=seems、C=なしを維持。that he is honestを真主語相当の内容節として別保存、内部S=he、V=is、C=honest。代替分析がある旨を残す。 |
| G030 | 追加 | S=It、V=was、C=difficultを維持。for me to answerを真主語相当の不定詞句として別保存、意味上の主語=me、V=answer。 |
| G031 | 追加 | S=She、V=wants、O=to become a doctorを維持。不定詞内部V=become、C=a doctor、意味上の主語=She。 |
| G032 | 追加 | S=To read books、V=is、C=enjoyableを維持。主語の不定詞句内部V=read、O=books。 |
| G033 | 追加 | S=He、V=decided、O=to leave earlyを維持。不定詞内部V=leave、early=M、意味上の主語=He。 |
| G034 | 追加 | S=I、V=enjoy、O=playing tennisを維持。動名詞句内部V=playing、O=tennis、意味上の主語=I。 |
| G035 | 追加 | S=Swimming in the sea、V=is、C=funを維持。動名詞句内部V=Swimming、in the sea=M。 |
| G036 | 追加 | 主節S=The girl、V=is、C=my sisterを維持。sitting by the windowはgirlの後置分詞修飾、by the windowは分詞句内のM。 |
| G037 | 追加 | 主節S=The letter、V=was、C=difficultを維持。written in Englishはletterの後置過去分詞修飾、in Englishは句内M。 |
| G038 | **構造修正** | S=Sheを共有。V1=opened/O1=the door と V2=entered/O2=the room をandが接続。現行goldはV2/O2が欠落。andはCONJ。 |
| G039 | **構造修正** | S=He、V=isを共有。C1=smart と C2=careless をbutが接続。sometimesはcarelessのM。現行goldはC2が欠落。butはCONJ。 |
| G040 | 追加・承認済み | 主節S=The book、V=was、C中心=difficult、C全体=surprisingly difficult to understand。surprisinglyは程度M、to understandは形容詞を補う不定詞。関係節that my teacher recommended yesterdayはbookを修飾し、節内S=my teacher、V=recommended、O=that（book参照）、yesterday=M。understandの意味上のOもbook参照。 |

### 集計と実装上の留意
- **主節の既存SVOCを維持できるもの：38/40**。ただし多くは節内部・M・関係リンク等の**追加注釈が必要**。G038・G039は並列要素の欠落により主節構造の拡張が必要。
- この表の「維持」は**追加必須事項が少ない**という意味で、全ての意味関係やtoken範囲を検証済みとはしない。SVOOの間接/直接OやSVOCの叙述関係は構造化する。
- 関係代名詞のO（G013/G014/G040）と不定詞の意味上のO（G040）は、**異なる節・句内の役割**としてそれぞれ参照を保存する。
- `G015 grew up` のような句動詞・前置詞/副詞の境界や、`G030 for me to answer` の内部階層はtokenレベルで別途精査する。
- この監査ではgold JSONの `review_status` を変更していない。承認規約への文書上の照合と、正式goldの確定・採点実装は別工程である。
