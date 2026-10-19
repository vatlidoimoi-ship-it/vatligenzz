(() => {
  'use strict';
  const root = document.getElementById('video-studio');
  if (!root) return;
  const el = id => document.getElementById(id);
  const base = '/teacher/videos';
  let current = null, timer = null, revision = 0;
  let previewUrl = null;
  function scriptPayload() {
    return {design_template:el('video-theme').value,
      steps:Array.from(el('video-steps').children).map(fieldset => Object.fromEntries(Array.from(fieldset.querySelectorAll('textarea')).map(node => [node.name,node.value])))};
  }
  const active = new Set(['queued_draft', 'drafting', 'queued', 'processing']);
  const labels = {queued_draft:'Chờ tạo kịch bản',drafting:'Đang tạo kịch bản',script_ready:'Chờ duyệt',queued:'Chờ dựng',processing:'Đang dựng',complete:'Hoàn tất',error:'Chưa hoàn tất'};
  const message = text => { el('video-message').textContent = text; };
  async function api(path, data) {
    const response = await fetch(base + path, data === undefined ? {} : {
      method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':root.dataset.csrf},body:JSON.stringify(data)
    });
    const result = await response.json().catch(() => ({error:'Không đọc được phản hồi máy chủ.'}));
    if (!response.ok) throw new Error(result.error || 'Không xử lý được yêu cầu.');
    return result;
  }
  function editor(script) {
    el('video-steps').replaceChildren();
    el('video-preview-step').replaceChildren();
    el('video-slide-preview').hidden = true;
    el('video-theme').value = script.design_template || 'studio';
    script.steps.forEach((step, i) => {
      const option = document.createElement('option'); option.value = i; option.textContent = `Bước ${i + 1}: ${step.title || ''}`;
      el('video-preview-step').append(option);
      const fieldset = document.createElement('fieldset');
      fieldset.style.cssText = 'margin:18px 0;padding:16px;border:1px solid #cad5e2;border-radius:12px';
      const legend = document.createElement('legend'); legend.textContent = `Bước ${i + 1}`; fieldset.append(legend);
      for (const [key, label, limit] of [['title','Tiêu đề',180],['slide_text','Chữ trên slide',1400],['narration','Lời thuyết minh',2200],['latex','Công thức LaTeX (nếu có)',1400]]) {
        const node = document.createElement('textarea');
        node.name = key; node.value = step[key] || ''; node.rows = key === 'title' ? 1 : 3;
        node.maxLength = limit; node.required = key === 'narration'; node.style.width = '100%';
        node.id = `video-step-${i}-${key}`;
        const caption = document.createElement('label'); caption.htmlFor = node.id; caption.textContent = label;
        fieldset.append(caption,node);
      }
      el('video-steps').append(fieldset);
    });
  }
  function show(job, resetEditor = true) {
    current = job;
    el('video-current').hidden = false;
    el('video-job-title').textContent = labels[job.status] || job.status;
    el('video-job-note').textContent = job.note || '';
    el('video-progress').value = job.progress || 0;
    el('video-progress').hidden = !active.has(job.status);
    const editable = ['script_ready','error'].includes(job.status) && job.script;
    el('video-editor').hidden = !editable;
    if (editable && resetEditor) editor(job.script);
    el('video-output').hidden = job.status !== 'complete';
    el('video-publication').hidden = job.status !== 'complete';
    if (job.status === 'complete') {
      el('teacher-result-video').src = job.video_url;
      el('video-download').href = job.video_url;
      const publication = job.publication || {};
      el('video-publish-title').value = publication.title || (job.problem || '').slice(0, 180);
      el('video-publish-grade').value = publication.grade || '';
      el('video-publish-group').value = publication.group || '';
      el('video-publish-description').value = publication.description || '';
      el('video-publication-status').textContent = publication.published ? 'Đã xuất bản cho học sinh.' : 'Video riêng, học sinh chưa xem được.';
      el('video-publish-button').textContent = publication.published ? 'Lưu thay đổi' : 'Xuất bản';
      el('video-unpublish').hidden = !publication.published;
      el('video-published-link').hidden = !publication.published;
      if (job.lesson_url) el('video-published-link').href = job.lesson_url;
    }
    clearTimeout(timer);
    if (active.has(job.status)) poll(job.id, revision);
  }
  function poll(id, expectedRevision) {
    timer = setTimeout(async () => {
      try {
        const result = await api(`/jobs/${id}`);
        if (revision !== expectedRevision) return;
        show(result.job);
        if (!active.has(result.job.status)) history();
      } catch (error) {
        if (revision !== expectedRevision) return;
        message(error.message + ' Đang thử kết nối lại…');
        poll(id, expectedRevision);
      }
    }, 4000);
  }
  async function history() {
    try {
      const result = await api('/jobs');
      const container = el('video-history'); container.replaceChildren();
      if (!result.items.length) container.textContent = 'Bạn chưa tạo video nào.';
      result.items.forEach(job => {
        const button = document.createElement('button'); button.type = 'button'; button.className = 'btn btn-secondary';
        button.style.cssText = 'display:block;text-align:left;margin:10px 0;width:100%';
        button.textContent = `${labels[job.status] || job.status}${job.publication?.published ? ' · Đã xuất bản' : ''} · ${(job.problem || '').slice(0,100)}`;
        button.addEventListener('click', async () => {
          revision++; clearTimeout(timer); const selectedRevision = revision;
          try { const data = await api(`/jobs/${job.id}`); if (revision === selectedRevision) show(data.job); }
          catch (error) { message(error.message); }
        });
        container.append(button);
      });
    } catch (error) { el('video-history').textContent = error.message; }
  }
  for (const [formId, submit] of [
    ['video-create', () => api('/jobs', {problem:el('video-problem').value})],
    ['video-editor', () => api(`/jobs/${current.id}/render`, {
      design_template:el('video-theme').value,
      steps:Array.from(el('video-steps').children).map(fieldset => Object.fromEntries(Array.from(fieldset.querySelectorAll('textarea')).map(node => [node.name,node.value])))
    })]
  ]) {
    el(formId).addEventListener('submit', async event => {
      event.preventDefault(); const button = event.target.querySelector('[type=submit]'); button.disabled = true;
      try { const data = await submit(); revision++; show(data.job); message('Đã nhận tác vụ. Bạn có thể quay lại xem trong lịch sử.'); history(); }
      catch (error) { message(error.message); }
      finally { button.disabled = false; }
    });
  }
  el('video-sound').addEventListener('click', async () => {
    const video = el('teacher-result-video'); video.muted = false; video.volume = 1;
    try { await video.play(); message('Đã bật tiếng.'); }
    catch (error) { message('Không phát được. Thử mở / tải MP4 bằng nút bên cạnh.'); }
  });
  el('video-preview-button').addEventListener('click', async () => {
    const button = el('video-preview-button'); button.disabled = true;
    const selectedJob = current.id;
    try {
      message('Đang tạo ảnh xem trước…');
      const response = await fetch(`${base}/jobs/${selectedJob}/preview`, {method:'POST',
        headers:{'Content-Type':'application/json','X-CSRF-Token':root.dataset.csrf},
        body:JSON.stringify({...scriptPayload(),preview_index:Number(el('video-preview-step').value)})});
      if (!response.ok) { const data = await response.json(); throw new Error(data.error || 'Không tạo được preview.'); }
      const blob = await response.blob();
      if (current.id !== selectedJob) return;
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      previewUrl = URL.createObjectURL(blob); el('video-slide-preview').src = previewUrl;
      el('video-slide-preview').hidden = false; message('Đây là bố cục với nội dung hiện tại. Bạn có thể sửa rồi xem lại.');
    } catch (error) { message(error.message); }
    finally { button.disabled = false; }
  });
  async function publishVideo(published) {
    const jobId = current.id;
    const selectedRevision = revision;
    const buttons = el('video-publication').querySelectorAll('button');
    buttons.forEach(button => button.disabled = true);
    try {
      const data = await api(`/jobs/${jobId}/publication`, {
        published, title: el('video-publish-title').value,
        grade: el('video-publish-grade').value, group: el('video-publish-group').value,
        description: el('video-publish-description').value
      });
      if (revision === selectedRevision) {
        show(data.job);
        message(published ? 'Video đã xuất hiện trong kho học sinh.' : 'Đã gỡ khỏi kho học sinh. Bản video riêng vẫn được giữ.');
      }
      history();
    } catch (error) { message(error.message); }
    finally { buttons.forEach(button => button.disabled = false); }
  }
  el('video-publication').addEventListener('submit', event => {
    event.preventDefault();
    if (!el('video-publish-button').disabled) publishVideo(true);
  });
  el('video-unpublish').addEventListener('click', () => {
    if (confirm('Gỡ video này khỏi kho học sinh?')) publishVideo(false);
  });
  history();
})();
