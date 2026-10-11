const imageInput=document.getElementById("imageInput");
const ocrButton=document.getElementById("ocrButton");
const ocrStatus=document.getElementById("ocrStatus");
const MAX_IMAGE_BYTES=12*1024*1024;
ocrButton.addEventListener("click",async()=>{
 const file=imageInput.files&&imageInput.files[0];
 if(!file){ocrStatus.textContent="画像を選択してください。";return;}
 if(!file.type.startsWith("image/")){ocrStatus.textContent="画像ファイルを選択してください。";return;}
 if(file.size>MAX_IMAGE_BYTES){ocrStatus.textContent="画像は12MB以下にしてください。";return;}
 if(!window.Tesseract){ocrStatus.textContent="文字認識ライブラリを読み込めませんでした。ネット接続を確認してください。";return;}
 ocrButton.disabled=true;ocrStatus.textContent="画像を読み取っています。初回は少し時間がかかります。";
 let worker;
 try{
  worker=await Tesseract.createWorker("eng",1,{logger:m=>{if(m.status==="recognizing text")ocrStatus.textContent="文字認識中 "+Math.round((m.progress||0)*100)+"%";}});
  const data=await worker.recognize(file);
  const extracted=(data.data.text||"").trim();
  if(!extracted)throw new Error("英文を検出できませんでした。鮮明な画像で再試行してください。");
  textarea.value=extracted;textarea.dispatchEvent(new Event("input"));
  ocrStatus.textContent="読み取り完了。誤字や改行を確認・修正してから「英文を解析」を押してください。";
 }catch(error){ocrStatus.textContent="読み取りに失敗しました："+error.message;}
 finally{if(worker)await worker.terminate();ocrButton.disabled=false;}
});
textarea.addEventListener("input",()=>{parsedSentences=[];result.replaceChildren();chosen.hidden=true;diagnosis.hidden=true;status.textContent="英文を編集しました。解析を実行してください。";});
const button=document.getElementById("analyzeButton");
const textarea=document.getElementById("sentence");
const status=document.getElementById("status");
const result=document.getElementById("result");
const chosen=document.getElementById("chosen");
const chosenText=document.getElementById("chosenText");
const REQUEST_TIMEOUT_MS=90000;
let parsedSentences=[];
function sentenceText(s){return (s.text||s.original_text||((s.tokens||[]).map(t=>t.text).join(" "))).trim();}
function showCandidates(){
  result.replaceChildren();chosen.hidden=true;diagnosis.hidden=true;
  const mode=document.querySelector('input[name="selectionMode"]:checked').value;
  const candidates=parsedSentences.map((sentence,index)=>({sentence,index,text:sentenceText(sentence)})).filter(x=>x.text);
  if(mode==="auto") candidates.sort((a,b)=>Array.from(b.text).length-Array.from(a.text).length||a.index-b.index);
  const displayed=mode==="auto"?candidates.slice(0,5):candidates;
  status.textContent=parsedSentences.length+"文を解析しました。"+(mode==="auto"?"長い順に最大5文を表示しています。":"すべての文を原文順に表示しています。");
  displayed.forEach(({index,text})=>{
    const choice=document.createElement("button");choice.type="button";choice.className="sentence-choice";
    choice.textContent=(index+1)+". "+text;
    choice.addEventListener("click",()=>{result.querySelectorAll(".sentence-choice").forEach(x=>x.classList.remove("selected"));choice.classList.add("selected");chosenText.textContent=text;chosen.hidden=false;diagnosis.hidden=true;});
    result.appendChild(choice);
  });
}
document.querySelectorAll('input[name="selectionMode"]').forEach(r=>r.addEventListener("change",()=>{if(parsedSentences.length)showCandidates();}));
button.addEventListener("click",async()=>{
 const text=textarea.value.trim();diagnosis.hidden=true;if(!text){status.textContent="英文を入力してください。";result.replaceChildren();chosen.hidden=true;return;}
 button.disabled=true;parsedSentences=[];result.replaceChildren();chosen.hidden=true;status.textContent="解析中...";
 const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),REQUEST_TIMEOUT_MS);
 try{
  const response=await fetch("/api/analyze",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text}),signal:controller.signal});
  const raw=await response.text();let data;try{data=JSON.parse(raw);}catch{throw new Error("解析結果を取得できませんでした（HTTP "+response.status+"）。");}
  if(!response.ok)throw new Error(data.error||"解析に失敗しました。");
  parsedSentences=Array.isArray(data.sentences)?data.sentences:[];
  if(!parsedSentences.length)throw new Error("英文が検出されませんでした。");
  showCandidates();
 }catch(error){status.textContent=error.name==="AbortError"?"解析が90秒以内に完了しませんでした。":error.message;}
 finally{clearTimeout(timer);button.disabled=false;}
});
const diagnosis=document.getElementById("diagnosis");
const diagnosisStatus=document.getElementById("diagnosisStatus");
const diagnosisWords=document.getElementById("diagnosisWords");
const unknownWords=document.getElementById("unknownWords");
const rolesPanel=document.getElementById("rolesPanel");
const roleWords=document.getElementById("roleWords");
const rolePrompt=document.getElementById("rolePrompt");
const selectedRanges=document.getElementById("selectedRanges");
const summary=document.getElementById("diagnosisSummary");
let diagnosticData=null, unknown=new Set(), roleIndex=0, anchor=null, pending=[], selected=new Set(), answers=[];
const roleNames=["主語 S","動詞 V","目的語 O","補語 C"];
function makeWordButtons(container,tokens,callback){
 container.replaceChildren();
 tokens.filter(t=>t.upos!=="PUNCT").forEach(t=>{
  const b=document.createElement("button");b.type="button";b.className="word-button";
  b.textContent=t.text;b.dataset.index=t.index;b.addEventListener("click",()=>callback(t.index));container.appendChild(b);
 });
}
function paint(container,ids){container.querySelectorAll("button").forEach(b=>b.classList.toggle("selected",ids.has(Number(b.dataset.index))));}
document.getElementById("startDiagnosis").addEventListener("click",async()=>{
 diagnosis.hidden=false;rolesPanel.hidden=true;summary.hidden=true;diagnosisStatus.textContent="診断の準備中...";
 diagnosticData=null;unknown=new Set();answers=[];roleIndex=0;diagnosisWords.replaceChildren();unknownWords.textContent="";
 try{
  const res=await fetch("/api/diagnose/prepare",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text:chosenText.textContent})});
  const data=await res.json();if(!res.ok)throw new Error(data.error||"準備できませんでした。");
  diagnosticData=data;
  makeWordButtons(diagnosisWords,data.tokens,id=>{if(unknown.has(id))unknown.delete(id);else unknown.add(id);paint(diagnosisWords,unknown);unknownWords.textContent="未知語："+(data.tokens.filter(t=>unknown.has(t.index)).map(t=>t.text).join("、")||"なし");});
  unknownWords.textContent="未知語：なし";diagnosisStatus.textContent="分からない単語を選んでください。";
 }catch(e){diagnosisStatus.textContent=e.message;}
});
document.getElementById("beginRoles").addEventListener("click",()=>{
 if(!diagnosticData){diagnosisStatus.textContent="まず診断を準備してください。";return;}
 const count=diagnosticData.tokens.filter(t=>t.upos!=="PUNCT").length;
 if(unknown.size>=Math.max(3,Math.ceil(count*0.4))){diagnosisStatus.textContent="未知語が多いため、構文診断を中断します。まず語彙を確認しましょう。";return;}
 diagnosisStatus.textContent="構文診断中（自動採点は試験版）";
 rolesPanel.hidden=false;roleIndex=0;answers=[];renderRole();
});
function renderRole(){
 if(roleIndex>=4){finishRoles();return;}
 anchor=null;pending=[];selected=new Set();rolePrompt.textContent=roleNames[roleIndex]+"を選択してください";
 makeWordButtons(roleWords,diagnosticData.tokens,id=>{
  if(anchor===null){anchor=id;selected=new Set([id]);}
  else{const low=Math.min(anchor,id),high=Math.max(anchor,id);pending.push(...diagnosticData.tokens.filter(t=>t.index>=low&&t.index<=high&&t.upos!=="PUNCT").map(t=>t.index));selected=new Set(pending);anchor=null;}
  paint(roleWords,selected);selectedRanges.textContent="選択："+diagnosticData.tokens.filter(t=>selected.has(t.index)).map(t=>t.text).join(" ");
 });
 selectedRanges.textContent="まだ選択されていません。";
}
document.getElementById("addRange").addEventListener("click",()=>{if(anchor!==null){pending.push(anchor);anchor=null;}selected=new Set(pending);paint(roleWords,selected);selectedRanges.textContent="選択："+diagnosticData.tokens.filter(t=>selected.has(t.index)).map(t=>t.text).join(" ");});
document.getElementById("noRole").addEventListener("click",()=>{anchor=null;pending=[];selected=new Set();paint(roleWords,selected);selectedRanges.textContent="なしを選択";});
document.getElementById("submitRole").addEventListener("click",()=>{
 if(anchor!==null){pending.push(anchor);anchor=null;}
 if(!pending.length&&selectedRanges.textContent!=="なしを選択"){selectedRanges.textContent="範囲を選択するか「なし」を押してください。";return;}
 const role="SVOC"[roleIndex];const expected=new Set(diagnosticData.roles[role].flatMap(e=>e.token_ids));
 const actual=new Set(pending);
 const correct=expected.size===actual.size&&[...expected].every(x=>actual.has(x));
 answers.push({role,correct,expected:diagnosticData.roles[role].map(x=>x.text).join(" / ")||"なし"});
 roleIndex++;renderRole();
});
function finishRoles(){
 rolesPanel.hidden=true;summary.hidden=false;summary.replaceChildren();
 const h=document.createElement("h3");h.textContent="仮診断結果";summary.appendChild(h);
 const p=document.createElement("p");p.textContent="一致："+answers.filter(a=>a.correct).length+" / 4（試験版・解析の曖昧性は未検証）";summary.appendChild(p);
 answers.forEach(a=>{const line=document.createElement("p");line.textContent=a.role+"："+(a.correct?"一致":"要確認")+" ／ 解析上の候補："+a.expected;summary.appendChild(line);});
 const note=document.createElement("p");note.textContent="この結果だけで弱点は確定しません。追加問題による確認が必要です。";summary.appendChild(note);
}
