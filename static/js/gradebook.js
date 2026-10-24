(() => {
  'use strict';
  const form = document.getElementById('gradebookForm');
  if (!form) return;
  const fields = ['tx1', 'midterm', 'final'];
  const labels = ['TX1', 'Giữa kì', 'Cuối kì'];
  const rows = [...form.querySelectorAll('[data-student-id]')];
  const original = new Map(JSON.parse(document.getElementById('gradebookInitial').textContent).map(r => [String(r.student.id), r]));
  const save = document.getElementById('gradebookSave');
  const status = document.getElementById('gradebookStatus');
  let saving = false;
  const parse = value => {
    const text = value.trim().replace(',', '.');
    if (!text) return null;
    if (!/^(?:\d+(?:\.\d)?|\.\d)$/.test(text)) return undefined;
    const n = Number(text);
    return n >= 0 && n <= 10 ? n : undefined;
  };
  const inputs = row => [...row.querySelectorAll('[data-field]')];
  const changed = row => inputs(row).some(input => parse(input.value) !== original.get(row.dataset.studentId).scores[input.dataset.field]);
  const dirty = () => rows.some(changed);
  function history(row, entries) {
    const cell = row.querySelector('[data-history]');
    cell.replaceChildren();
    if (!entries.length) { cell.textContent = 'Chưa có chỉnh sửa'; return; }
    const details = document.createElement('details');
    const summary = document.createElement('summary');
    summary.textContent = `${entries.length} lần lưu`;
    details.append(summary);
    for (const entry of entries) {
      const p = document.createElement('p');
      const when = new Date(entry.at).toLocaleString('vi-VN', {timeZone: 'Asia/Bangkok'});
      p.textContent = `${entry.actor_name} · ${when}. ` + fields.map((f, i) => `${labels[i]}: ${entry.before[f] ?? 'trống'} → ${entry.after[f] ?? 'trống'}`).join('; ');
      details.append(p);
    }
    cell.append(details);
  }
  function update() {
    let count = 0, invalid = false;
    for (const row of rows) {
      const baseline = original.get(row.dataset.studentId);
      const values = inputs(row).map(input => {
        const n = parse(input.value);
        const bad = n === undefined;
        input.setAttribute('aria-invalid', String(bad));
        input.nextElementSibling.textContent = bad ? 'Nhập 0–10, tối đa 1 số lẻ.' : '';
        input.classList.toggle('dirty', n !== baseline.scores[input.dataset.field]);
        invalid ||= bad;
        return n;
      });
      if (changed(row)) {
        count++;
        const complete = values.every(n => n !== null && n !== undefined);
        const weighted = values.reduce((sum, n, i) => sum + Math.round((n ?? 0) * 10) * [1, 2, 3][i], 0);
        row.querySelector('[data-average]').textContent = complete ? (Math.round(weighted / 6) / 10).toFixed(1) : 'Chưa đủ điểm';
        const imported = row.querySelector('[data-imported]');
        if (imported) imported.hidden = true;
      } else {
        row.querySelector('[data-average]').textContent = baseline.average ?? 'Chưa đủ điểm';
        const imported = row.querySelector('[data-imported]');
        if (imported) imported.hidden = !baseline.imported_average;
      }
    }
    document.getElementById('gradebookDirty').textContent = count ? `${count} học sinh có thay đổi chưa lưu` : 'Chưa có thay đổi';
    save.disabled = !count || invalid || saving;
  }
  rows.forEach(row => history(row, original.get(row.dataset.studentId).history));
  form.addEventListener('input', update);
  window.addEventListener('beforeunload', event => { if (dirty()) { event.preventDefault(); event.returnValue = ''; } });
  document.getElementById('gradebookSearch').addEventListener('input', event => {
    const query = event.target.value.trim().toLocaleLowerCase('vi');
    for (const row of rows) row.hidden = !row.dataset.search.toLocaleLowerCase('vi').includes(query);
    document.getElementById('gradebookSearchEmpty').hidden = rows.some(row => !row.hidden);
  });
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (save.disabled || saving) return;
    const changes = rows.filter(changed).map(row => ({student_id: row.dataset.studentId, version: original.get(row.dataset.studentId).version, scores: Object.fromEntries(inputs(row).map(i => [i.dataset.field, parse(i.value)]))}));
    saving = true;
    inputs(form).forEach(i => i.disabled = true);
    update();
    status.className = '';
    status.textContent = 'Đang lưu điểm…';
    try {
      const response = await fetch(form.dataset.saveUrl, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRF-Token': form.dataset.csrf}, body: JSON.stringify({changes})});
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Không lưu được điểm.');
      for (const entry of result.rows) {
        const id = String(entry.student.id);
        original.set(id, entry);
        const row = rows.find(r => r.dataset.studentId === id);
        if (!row) continue;
        inputs(row).forEach(i => i.value = entry.scores[i.dataset.field] ?? '');
        history(row, entry.history);
      }
      status.className = 'success';
      status.textContent = result.message;
    } catch (error) {
      status.className = 'error';
      status.textContent = error instanceof SyntaxError ? 'Chưa xác nhận được kết quả lưu. Giữ lại điểm đang nhập và tải lại trang để kiểm tra.' : error.message;
    } finally {
      saving = false;
      inputs(form).forEach(i => i.disabled = false);
      update();
    }
  });
  update();
})();
