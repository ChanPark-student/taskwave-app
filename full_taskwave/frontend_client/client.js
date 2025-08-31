(()=> {
  const WEEKDAY_KO_TO_INT = {
    '월':0, '화':1, '수':2, '목':3, '금':4, '토':5, '일':6,
    '월요일':0, '화요일':1, '수요일':2, '목요일':3, '금요일':4, '토요일':5, '일요일':6,
  };
  const INT_TO_KO = {0:'월',1:'화',2:'수',3:'목',4:'금',5:'토',6:'일'};

  // 고정 패턴: 과목/주차(2자리)/요일_월-일
  const FIXED_PATTERN = "{SUBJECT}/주차{WEEK2}/{WEEKDAY_KO}_{MM}-{DD}";

  const $ = (sel) => document.querySelector(sel);
  const inputText = $('#inputText');
  const startDate = $('#startDate');
  const endDate   = $('#endDate');
  const holidays  = $('#holidays');
  const writeMeta = $('#writeMeta');
  const errors    = $('#errors');
  const preview   = $('#preview');

  function parseTime(text) {
    const s = text.trim();
    let hh = 0, mm = 0;
    if (s.includes(':')) {
      const [h,m] = s.split(':').map(x => x.trim());
      hh = parseInt(h, 10);
      mm = parseInt(m, 10);
    } else {
      if (s.length === 4) { hh = parseInt(s.slice(0,2),10); mm = parseInt(s.slice(2),10); }
      else if (s.length === 3) { hh = parseInt(s.slice(0,1),10); mm = parseInt(s.slice(1),10); }
      else throw new Error(`시간 포맷 오류: ${text}`);
    }
    if (!(0 <= hh && hh <= 23 && 0 <= mm && mm <= 59)) throw new Error(`시간 범위 오류: ${text}`);
    return {hh, mm};
  }

  function parseEntries(text) {
    const out = [];
    const lines = text.split('\n');
    for (const raw of lines) {
      const line = raw.trim();
      if (!line || line.startsWith('#')) continue;
      const parts = line.split(',').map(p => p.trim());
      if (parts.length !== 3) throw new Error(`3개 항목(과목, 요일, 시간)이 필요: ${line}`);
      const [subject, day, tspan] = parts;
      if (!(day in WEEKDAY_KO_TO_INT)) throw new Error(`알 수 없는 요일: ${day}`);
      if (!tspan.includes('-')) throw new Error(`시간 구간은 '시작-끝' 형식: ${tspan}`);
      const [sStr, eStr] = tspan.split('-').map(x => x.trim());
      const s = parseTime(sStr); const e = parseTime(eStr);
      if (e.hh < s.hh || (e.hh === s.hh && e.mm <= s.mm)) throw new Error(`끝시간이 시작보다 이전/같음: ${tspan}`);
      out.push({ subject, weekday: WEEKDAY_KO_TO_INT[day], start: s, end: e });
    }
    return out;
  }

  function toDate(iso) {
    const [Y,M,D] = iso.split('-').map(x => parseInt(x,10));
    return new Date(Y, M-1, D);
  }

  function f2(n) { return (n < 10 ? '0' : '') + n; }

  function inRangeDates(start, end) {
    const arr = [];
    for (let d = new Date(start); d <= end; d.setDate(d.getDate()+1)) {
      arr.push(new Date(d));
    }
    return arr;
  }

  function parseHolidays(s) {
    if (!s.trim()) return new Set();
    const out = new Set();
    for (const piece of s.split(',').map(x => x.trim()).filter(Boolean)) {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(piece)) throw new Error(`휴일 형식(YYYY-MM-DD) 오류: ${piece}`);
      out.add(piece);
    }
    return out;
  }

  function weeksSince(semStart, d) {
    const oneDay = 24 * 60 * 60 * 1000;
    const deltaDays = Math.floor((d - semStart) / oneDay);
    return Math.floor(deltaDays / 7) + 1; // 1부터 시작
  }

  function applyPattern(pat, entry, d, semStart) {
    const YYYY = d.getFullYear().toString();
    const MM = f2(d.getMonth()+1);
    const DD = f2(d.getDate());
    const WEEKDAY_KO = INT_TO_KO[entry.weekday];
    const SUBJECT = entry.subject;
    const WEEK = String(weeksSince(semStart, d));
    const WEEK2 = f2(weeksSince(semStart, d));

    return pat
      .replaceAll('{YYYY}', YYYY)
      .replaceAll('{MM}', MM)
      .replaceAll('{DD}', DD)
      .replaceAll('{WEEKDAY_KO}', WEEKDAY_KO)
      .replaceAll('{SUBJECT}', SUBJECT)
      .replaceAll('{WEEK}', WEEK)
      .replaceAll('{WEEK2}', WEEK2);
  }

  function buildPlan() {
    errors.hidden = true;
    errors.textContent = '';
    preview.textContent = '';
    try {
      const entries = parseEntries(inputText.value);
      const s = toDate(startDate.value);
      const e = toDate(endDate.value);
      if (e < s) throw new Error('종료일이 시작일보다 앞');
      const hol = parseHolidays(holidays.value);

      const dates = inRangeDates(s, e);
      const items = [];
      for (const d of dates) {
        for (const entry of entries) {
          // JS Date.getDay(): 0=일,1=월,… / entry.weekday: 0=월,… => 보정
          if (d.getDay() === ((entry.weekday + 1) % 7)) {
            const ymd = `${d.getFullYear()}-${f2(d.getMonth()+1)}-${f2(d.getDate())}`;
            if (hol.has(ymd)) continue;
            items.push({ entry, date: new Date(d) });
          }
        }
      }
      return { entries, items, pattern: FIXED_PATTERN };
    } catch (err) {
      errors.hidden = false;
      errors.textContent = err.message || String(err);
      return null;
    }
  }

  function doPreview() {
    const plan = buildPlan();
    if (!plan) return;
    const { items, pattern } = plan;
    const semStart = toDate(startDate.value);
    const first = items.slice(0, 60); // limit preview
    const lines = first.map(({entry, date:d}) => applyPattern(pattern, entry, d, semStart));
    let text = lines.join('\n');
    if (items.length > first.length) {
      text += `\n... 외 ${items.length - first.length}개`;
    }
    preview.textContent = text || '(생성 결과 없음)';
  }

  async function doDownload() {
    const plan = buildPlan();
    if (!plan) return;
    const { items, pattern } = plan;
    if (items.length === 0) {
      errors.hidden = false;
      errors.textContent = '생성할 항목이 없습니다.';
      return;
    }
    const semStart = toDate(startDate.value);

    const zip = new JSZip();
    for (const {entry, date:d} of items) {
      let folderPath = applyPattern(pattern, entry, d, semStart)
        .replaceAll('\\','/')
        .replace(/^\/+|\/+$/g, '');
      if (!folderPath) continue;

      const folder = zip.folder(folderPath);
      if (writeMeta.checked) {
        const meta = [
          `subject: ${entry.subject}`,
          `weekday: ${entry.weekday}`,
          `date: ${d.getFullYear()}-${f2(d.getMonth()+1)}-${f2(d.getDate())}`,
          `start: ${f2(entry.start.hh)}:${f2(entry.start.mm)}`,
          `end: ${f2(entry.end.hh)}:${f2(entry.end.mm)}`
        ].join('\n');
        folder.file('_meta.txt', meta);
      }
    }
    const blob = await zip.generateAsync({type:'blob'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'generated_folders.zip';
    a.click();
    URL.revokeObjectURL(a.href);
  }

  document.querySelector('#btnPreview').addEventListener('click', doPreview);
  document.querySelector('#btnDownload').addEventListener('click', doDownload);
  doPreview();
})();
