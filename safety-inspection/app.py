import io,json,os,re,sqlite3,uuid,zipfile
from datetime import date
from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from xml.etree import ElementTree as ET
BASE=Path(__file__).parent
DATA=BASE/'data';DATA.mkdir(exist_ok=True)
def db():
 c=sqlite3.connect(DATA/'inspection.db');c.row_factory=sqlite3.Row
 c.execute('CREATE TABLE IF NOT EXISTS reports(id TEXT PRIMARY KEY, site TEXT, day TEXT, filename TEXT, text TEXT, findings TEXT)')
 return c
def extract(name,raw):
 ext=Path(name).suffix.lower()
 if ext=='.pdf':
  from pypdf import PdfReader
  reader=PdfReader(io.BytesIO(raw))
  return '\n'.join(f'[페이지 {i+1}]\n{p.extract_text() or ""}' for i,p in enumerate(reader.pages))
 if ext=='.xlsx':
  from openpyxl import load_workbook
  w=load_workbook(io.BytesIO(raw),read_only=True,data_only=True)
  lines=[]
  for s in w:
   for i,row in enumerate(s.iter_rows(values_only=True),1):
    if any(v is not None for v in row):lines.append(f'[{s.title}!{i}] '+' | '.join('' if v is None else str(v) for v in row))
  w.close();return '\n'.join(lines)
 if ext=='.hwpx':
  with zipfile.ZipFile(io.BytesIO(raw)) as z:
   if sum(i.file_size for i in z.infolist())>50*1024*1024:raise ValueError('압축 해제 크기가 너무 큽니다.')
   return '\n'.join(f'[{n}] '+' '.join(ET.fromstring(z.read(n)).itertext()) for n in sorted(z.namelist()) if re.fullmatch(r'Contents/section\d+\.xml',n))
 raise ValueError('XLSX, HWPX, PDF 파일을 지원합니다. 구형 XLS/HWP는 변환해 주세요.')
class Handler(BaseHTTPRequestHandler):
 def reply(self,status,obj):
  raw=json.dumps(obj,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
 def do_GET(self):
  if self.path=='/api/reports':
   with db() as c: rows=[dict(r) for r in c.execute('SELECT * FROM reports ORDER BY day DESC')]
   for r in rows:r['findings']=json.loads(r['findings'])
   return self.reply(200,rows)
  if self.path not in ['/','/index.html']:return self.reply(404,{'error':'찾을 수 없습니다.'})
  raw=(BASE/'static/index.html').read_bytes();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(raw)
 def do_POST(self):
  try:
   size=int(self.headers.get('Content-Length','0'))
   if size<=0 or size>16*1024*1024:raise ValueError('파일은 15MB 이하로 업로드해 주세요.')
   body=self.rfile.read(size)
   if self.path=='/api/upload':
    from urllib.parse import unquote
    name=Path(unquote(self.headers.get('X-Filename',''))).name
    site=unquote(self.headers.get('X-Site','')).strip();day=self.headers.get('X-Day','')
    if not site or len(site)>100:raise ValueError('현장명을 입력해 주세요.')
    date.fromisoformat(day)
    text=extract(name,body)
    if len(text)>1000000:raise ValueError('추출 텍스트가 너무 큽니다.')
    rid=uuid.uuid4().hex
    with db() as c:c.execute('INSERT INTO reports VALUES(?,?,?,?,?,?)',(rid,site,day,name,text,'[]'))
    return self.reply(201,{'id':rid,'warning':None if text.strip() else '텍스트가 없습니다. 스캔 PDF는 OCR 처리가 필요합니다.'})
   if self.path.startswith('/api/reports/'):
    rid=self.path.rsplit('/',1)[-1];payload=json.loads(body);findings=payload['findings']
    if not isinstance(findings,list) or len(findings)>500:raise ValueError('지적사항 형식을 확인해 주세요.')
    clean=[]
    for f in findings:
     item={k:str(f.get(k,''))[:2000] for k in ['description','risk','status','owner','due','source']}
     if item['risk'] not in ['상','중','하'] or item['status'] not in ['미조치','진행중','완료']:raise ValueError('위험도 또는 조치상태를 확인해 주세요.')
     if not item['description'].strip():raise ValueError('지적내용을 입력해 주세요.')
     clean.append(item)
    with db() as c:
     cur=c.execute('UPDATE reports SET findings=? WHERE id=?',(json.dumps(clean,ensure_ascii=False),rid))
     if cur.rowcount==0:return self.reply(404,{'error':'보고서가 없습니다.'})
    return self.reply(200,{'saved':True})
   return self.reply(404,{'error':'찾을 수 없습니다.'})
  except Exception as e:self.reply(400,{'error':str(e) if isinstance(e,ValueError) else '문서를 처리할 수 없습니다. 파일 형식을 확인해 주세요.'})
if __name__=='__main__':
 db().close();ThreadingHTTPServer(('127.0.0.1',int(os.environ.get('PORT','3100'))),Handler).serve_forever()
