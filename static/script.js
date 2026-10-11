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
textarea.addEventListener("input",()=>{parsedSentences=[];result.replaceChildren();chosen.hidden=true;status.textContent="英文を編集しました。解析を実行してください。";});
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
  result.replaceChildren();chosen.hidden=true;
  const mode=document.querySelector('input[name="selectionMode"]:checked').value;
  const candidates=parsedSentences.map((sentence,index)=>({sentence,index,text:sentenceText(sentence)})).filter(x=>x.text);
  if(mode==="auto") candidates.sort((a,b)=>Array.from(b.text).length-Array.from(a.text).length||a.index-b.index);
  const displayed=mode==="auto"?candidates.slice(0,5):candidates;
  status.textContent=parsedSentences.length+"文を解析しました。"+(mode==="auto"?"長い順に最大5文を表示しています。":"すべての文を原文順に表示しています。");
  displayed.forEach(({index,text})=>{
    const choice=document.createElement("button");choice.type="button";choice.className="sentence-choice";
    choice.textContent=(index+1)+". "+text;
    choice.addEventListener("click",()=>{result.querySelectorAll(".sentence-choice").forEach(x=>x.classList.remove("selected"));choice.classList.add("selected");chosenText.textContent=text;chosen.hidden=false;});
    result.appendChild(choice);
  });
}
document.querySelectorAll('input[name="selectionMode"]').forEach(r=>r.addEventListener("change",()=>{if(parsedSentences.length)showCandidates();}));
button.addEventListener("click",async()=>{
 const text=textarea.value.trim();if(!text){status.textContent="英文を入力してください。";result.replaceChildren();chosen.hidden=true;return;}
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