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
