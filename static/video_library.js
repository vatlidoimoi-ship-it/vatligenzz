(() => {
  const filter = document.getElementById('lesson-filter');
  const grade = document.getElementById('lesson-grade');
  function filterLessons() {
    let visible = 0;
    document.querySelectorAll('.lesson-card').forEach(card => {
      card.hidden = Boolean((filter.value && card.dataset.group !== filter.value) || (grade?.value && card.dataset.grade !== grade.value));
      if (!card.hidden) visible++;
    });
    document.getElementById('lesson-empty').hidden = visible > 0;
  }
  if (filter) filter.addEventListener('change', filterLessons);
  if (grade) grade.addEventListener('change', filterLessons);
  const video = document.getElementById('lesson-player');
  if (!video) return;
  const status = document.getElementById('lesson-status');
  document.getElementById('lesson-play').addEventListener('click', async () => {
    status.textContent = '';
    if (!video.src || video.error) video.src = video.dataset.source;
    video.muted = false;
    video.volume = 1;
    try { await video.play(); }
    catch (_) { status.textContent = 'Chưa phát được. Bạn thử lại hoặc chọn Mở MP4 nhé.'; }
  });
  video.addEventListener('error', () => {
    status.textContent = 'Không tải được video. Bạn nhấn Phát video để lấy lại liên kết.';
  });
})();
