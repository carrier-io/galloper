(function () {
  let advices = document.querySelectorAll(".advices tr");
  let advicesArr = Array.prototype.slice.call(advices);

  advicesArr.forEach(advice => addListener(advice, 'click', (e) => {
      let target = e.currentTarget;
      const isToggleHeader = target.classList.contains('header') && target.getElementsByClassName('toggle').length;
      if (isToggleHeader) {
        target.classList.toggle('show');
      }
    })
  );

  const frames = document.getElementById('frames_container');
  addListener(frames, 'click', openFull);

  function addListener(el, eventName, handler) {
    el.removeEventListener(eventName, handler.bind(el));
    el.addEventListener(eventName, handler.bind(el));
  }
})();
