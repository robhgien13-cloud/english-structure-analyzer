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
const button=document.getElementById("analyzeButton");
const textarea=document.getElementById("sentence");
const status=document.getElementById("status");
const result=document.getElementById("result");
const chosen=document.getElementById("chosen");
const chosenText=document.getElementById("chosenText");
const REQUEST_TIMEOUT_MS=90000;
let parsedSentences=[];
let chosenIndices=new Set(),diagnosisQueue=[],diagnosisResults=[],queuePosition=0;
textarea.addEventListener("input",()=>{parsedSentences=[];chosenIndices.clear();diagnosisQueue=[];diagnosisResults=[];result.replaceChildren();chosen.hidden=true;diagnosis.hidden=true;status.textContent="英文を編集しました。解析を実行してください。";});
function sentenceText(s){return (s.text||s.original_text||((s.tokens||[]).map(t=>t.text).join(" "))).trim();}
function showCandidates(){
  result.replaceChildren();chosen.hidden=true;diagnosis.hidden=true;chosenIndices.clear();
  const mode=document.querySelector('input[name="selectionMode"]:checked').value;
  const candidates=parsedSentences.map((sentence,index)=>({sentence,index,text:sentenceText(sentence)})).filter(x=>x.text);
  if(mode==="auto") candidates.sort((a,b)=>Array.from(b.text).length-Array.from(a.text).length||a.index-b.index);
  const displayed=mode==="auto"?candidates.slice(0,5):candidates;
  status.textContent=parsedSentences.length+"文を解析しました。"+(mode==="auto"?"長い順に最大5文を表示しています。":"すべての文を原文順に表示しています。");
  displayed.forEach(({index,text})=>{
    const choice=document.createElement("button");choice.type="button";choice.className="sentence-choice";choice.textContent=(index+1)+". "+text;
    choice.addEventListener("click",()=>{
      if(chosenIndices.has(index))chosenIndices.delete(index);else chosenIndices.add(index);
      choice.classList.toggle("selected",chosenIndices.has(index));
      chosen.hidden=!chosenIndices.size;
      chosenText.textContent=[...chosenIndices].sort((a,b)=>a-b).map(i=>sentenceText(parsedSentences[i])).join("\n");
    });
    result.appendChild(choice);
  });
  document.getElementById("selectionHint").textContent="診断したい文を複数選択できます。選択順ではなく原文順に診断します。";
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
let diagnosticData=null, unknown=new Set(), roleIndex=0, anchor=null, pending=[], selected=new Set(), answers=[], noRoleChosen=false;
const roleNames=["主語 S","動詞 V","目的語 O","補語 C"];
function makeWordButtons(container,tokens,callback){
 container.replaceChildren();
 tokens.filter(t=>t.upos!=="PUNCT" && t.text && t.text.trim()).forEach(t=>{
  const b=document.createElement("button");b.type="button";b.className="word-button";
  b.textContent=t.text;b.dataset.index=t.index;b.addEventListener("click",()=>callback(t.index));container.appendChild(b);
 });
}
function paint(container,ids){container.querySelectorAll("button").forEach(b=>b.classList.toggle("selected",ids.has(Number(b.dataset.index))));}
const startDiagnosisButton=document.getElementById("startDiagnosis");
function setCurrentSentence(){chosenText.textContent=sentenceText(parsedSentences[diagnosisQueue[queuePosition]]);document.getElementById("diagnosisProgress").textContent=(queuePosition+1)+" / "+diagnosisQueue.length+" 文目";}

const beginRolesButton=document.getElementById("beginRoles");
startDiagnosisButton.addEventListener("click",async()=>{
 if(startDiagnosisButton.disabled)return;
 if(!diagnosisQueue.length){diagnosisQueue=[...chosenIndices].sort((a,b)=>a-b);diagnosisResults=[];queuePosition=0;}
 if(!diagnosisQueue.length)return;
 setCurrentSentence();
 diagnosis.hidden=false;rolesPanel.hidden=true;summary.hidden=true;diagnosisStatus.textContent="診断の準備中...";
 document.getElementById("diagnosisOriginal").textContent=chosenText.textContent;
 diagnosticData=null;unknown=new Set();answers=[];roleIndex=0;diagnosisWords.replaceChildren();unknownWords.textContent="";
 startDiagnosisButton.disabled=true;beginRolesButton.disabled=true;
 const controller=new AbortController();
 const timeout=setTimeout(()=>controller.abort(),30000);
 try{
  const res=await fetch("/api/diagnose/prepare",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text:chosenText.textContent}),signal:controller.signal});
  const raw=await res.text();
  let data;try{data=JSON.parse(raw);}catch{throw new Error("診断準備の応答を読み取れませんでした（HTTP "+res.status+"）。");}
  if(!res.ok)throw new Error(data.error||"準備できませんでした（HTTP "+res.status+"）。");
  if(!Array.isArray(data.tokens)||!data.roles)throw new Error("診断データの形式が正しくありません。");
  diagnosticData=data;
  makeWordButtons(diagnosisWords,data.tokens,id=>{if(unknown.has(id))unknown.delete(id);else unknown.add(id);paint(diagnosisWords,unknown);unknownWords.textContent="未知語："+(data.tokens.filter(t=>unknown.has(t.index)).map(t=>t.text).join("、")||"なし");});
  unknownWords.textContent="未知語：なし";diagnosisStatus.textContent="分からない単語を選んでください。";
  beginRolesButton.disabled=false;
 }catch(e){diagnosisStatus.textContent=e.name==="AbortError"?"診断の準備が30秒以内に完了しませんでした。再度お試しください。":"診断の準備に失敗しました："+e.message;}
 finally{clearTimeout(timeout);startDiagnosisButton.disabled=false;}
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
 anchor=null;pending=[];selected=new Set();noRoleChosen=false;
 rolePrompt.textContent=roleNames[roleIndex]+"を選択してください";
 makeWordButtons(roleWords,diagnosticData.tokens,id=>{
  noRoleChosen=false;
  if(selected.has(id))selected.delete(id);else selected.add(id);
  pending=[...selected];
  paint(roleWords,selected);
  selectedRanges.textContent="選択："+(diagnosticData.tokens.filter(t=>selected.has(t.index)).map(t=>t.text).join(" ")||"なし");
 });
 selectedRanges.textContent="まだ選択されていません。";
}
document.getElementById("noRole").addEventListener("click",()=>{anchor=null;pending=[];selected=new Set();noRoleChosen=true;paint(roleWords,selected);selectedRanges.textContent="なしを選択";});
document.getElementById("submitRole").addEventListener("click",()=>{
 if(anchor!==null){pending.push(anchor);anchor=null;}
 if(!pending.length&&!noRoleChosen){selectedRanges.textContent="範囲を選択するか「なし」を押してください。";return;}
 const role="SVOC"[roleIndex];const expected=new Set(diagnosticData.roles[role].flatMap(e=>e.token_ids));
 const actual=new Set(pending);
 const correct=expected.size===actual.size&&[...expected].every(x=>actual.has(x));
 answers.push({role,correct,actualIds:[...actual],expectedIds:[...expected],actual:diagnosticData.tokens.filter(t=>actual.has(t.index)).map(t=>t.text).join(" ")||"なし",expected:diagnosticData.roles[role].map(x=>x.text).join(" / ")||"なし"});
 roleIndex++;renderRole();
});
function groupedRoles(tokens,answerSet){
 const groups=[];let active=null;
 for(const t of tokens){
  const labels="SVOC".split("").filter(role=>answerSet[role]&&answerSet[role].has(t.index));
  const label=labels.join("/");
  if(active&&active.label===label&&active.last===t.index-1){active.text+=" "+t.text;active.last=t.index;}
  else{active={text:t.text,label,last:t.index};groups.push(active);}
 }
 return groups;
}
function renderStructure(parent,tokens,answerSet){
 const row=document.createElement("div");row.className="structure-row";
 groupedRoles(tokens,answerSet).forEach(g=>{
  const box=document.createElement("div");box.className="structure-box";
  const word=document.createElement("strong");word.textContent=g.text;
  const role=document.createElement("small");role.textContent=g.label||"—";
  box.append(word,role);row.appendChild(box);
 });parent.appendChild(row);
}
function renderReport(){
 const report=document.getElementById("combinedReport");report.hidden=false;report.replaceChildren();
 const heading=document.createElement("h2");heading.textContent="全文の診断結果（"+diagnosisResults.length+"文）";report.appendChild(heading);
 for(const item of diagnosisResults){
  const section=document.createElement("section");section.className="report-sentence";
  const title=document.createElement("h3");title.textContent="第"+item.number+"文："+item.text;section.appendChild(title);
  const student=document.createElement("p");student.textContent="生徒の回答";section.appendChild(student);
  renderStructure(section,item.tokens,Object.fromEntries(item.answers.map(a=>[a.role,new Set(a.actualIds)])));
  const engine=document.createElement("p");engine.textContent="解析上の候補（試験版）";section.appendChild(engine);
  renderStructure(section,item.tokens,Object.fromEntries(item.answers.map(a=>[a.role,new Set(a.expectedIds)])));
  const vocab=document.createElement("p");vocab.textContent="未知語："+(item.unknown.join("、")||"なし")+" ／ 一致："+item.answers.filter(a=>a.correct).length+"/4";section.appendChild(vocab);
  report.appendChild(section);
 }
 const caution=document.createElement("p");caution.textContent="解析候補には誤りがあり得ます。不一致だけで生徒の理解不足と確定しません。";report.appendChild(caution);
}
function finishRoles(){
 rolesPanel.hidden=true;summary.hidden=false;summary.replaceChildren();
 diagnosisResults.push({number:diagnosisQueue[queuePosition]+1,text:chosenText.textContent,tokens:diagnosticData.tokens,answers:answers.map(a=>({...a})),unknown:diagnosticData.tokens.filter(t=>unknown.has(t.index)).map(t=>t.text)});
 const h=document.createElement("h3");h.textContent="第"+(queuePosition+1)+"文の仮診断結果";summary.appendChild(h);
 const p=document.createElement("p");p.textContent="一致："+answers.filter(a=>a.correct).length+"/4";summary.appendChild(p);
 renderStructure(summary,diagnosticData.tokens,Object.fromEntries(answers.map(a=>[a.role,new Set(a.actualIds)])));
 const next=document.createElement("button");next.type="button";
 if(queuePosition+1<diagnosisQueue.length){
  next.textContent="次の文を診断する";
  next.addEventListener("click",()=>{queuePosition++;startDiagnosisButton.click();});
 }else{
  next.textContent="全文の診断結果を見る";
  next.addEventListener("click",()=>{renderReport();document.getElementById("combinedReport").scrollIntoView({behavior:"smooth"});});
 }
 summary.appendChild(next);
}
