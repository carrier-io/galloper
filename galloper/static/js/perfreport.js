function openFull(e) {
  const target = e.target;
  const isFrame = target.classList.contains('frameImg');

  if (!target || !isFrame) {
    return;
  }

  const framesHolder = document.getElementById('frames_container');
  const frames = [...framesHolder.querySelectorAll('.frameImg')];
  const frameNumbers = frames.map(el => +(el.alt.replace(/.*frame(.*?)/, '$1')));

  let current = frameNumbers[frames.indexOf(target)];

  const modal = framesHolder.querySelector(".modal");
  const modalImg = modal.querySelector(".img");
  const captionText = modal.querySelector(".caption");
  const close = modal.querySelector(".close");

  modal.onclick = closeModal;
  modalImg.onclick = prevent;
  captionText.onclick = prevent;

  close.onclick = closeModal;

  window.addEventListener('keydown', handleKey);

  showModal(current);

  function prevent(e) {
    e.stopPropagation();
  }

  function handleKey(e) {
    switch (e.keyCode) {
      case 27: // esc - close modal
        closeModal(e);
        return;
      case 39: // right arrow - next
        if (frameNumbers.includes(current + 1)) {
          current++;
        }
        break;
      case 37: // left arrow - prev
        if (frameNumbers.includes(current - 1)) {
          current--;
        }
        break;
    }

    setModal(current);
  }

  function closeModal() {
    window.removeEventListener('keyup', handleKey);
    modal.classList.remove('show');

    clearModal();
  }

  function clearModal() {
    modalImg.src = '';
    captionText.innerHTML = '';
  }

  function setModal(id) {
    const img = framesHolder.querySelector("#frame_" + id);

    modalImg.src = img.src;
    captionText.innerHTML = img.alt;
  }

  function showModal(id) {
    setModal(id);
    modal.classList.add('show');
  }
}

function createPopUp(data) {
  var popUpBlock = document.getElementById('resPopUp');
  popUpBlock.style.display = "block";

  function grabDomain(string) {
    var regex = /http(?:s)?:\/\/(?:[\w-]+\.)*([\w-]{1,63})(?:\.(?:\w{3}|\w{2}))(?:$|\/)/;
    if (regex.test(string)) {
      return regex.exec(string)[0]
    } else {
      return "can't extract domain"
    }
  }

  document.getElementById('resName').children[1].innerHTML = data.name;
  document.getElementById('resDomain').children[1].innerHTML = grabDomain(data.name);
  document.getElementById('resInitiator').children[1].innerHTML = data.initiatorType;
  document.getElementById('resDuration').children[1].innerHTML = Math.floor(data.duration) + ' ms';
  document.getElementById('resSize').children[1].innerHTML = (data.transferSize / 1000) + ' kb'
}

function closeResPopUp() {
  var e = document.getElementById('resPopUp');
  e.style.display = "none";
}

function setInterval() {
  var elem = document.getElementsByClassName('google-visualization-tooltip-action');
  if (elem.length === 2) {
    elem[0].parentNode.removeChild(elem[0]);
  }
  elem = null
}

function drawGauge(number, element_id, label) {
  const opts = {
    percent: number,
    stroke: 3,
    colorName: getColorName(number)
  };
  createDonut(document.getElementById(element_id), opts, label);
}

function getColorName(number) {
  let color = "green";
  if (number > 60 && 90 > number) {
    color = "yellow"
  } else if (60 > number && number > 0 ) {
    color = "red"
  }  else if (number === 0) {
    color = "gray"
  }
  return color;
}
