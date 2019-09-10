function toggleRow(toggleElement){
  const rows = toggleElement.nextSibling.getElementsByClassName("u-hideable");
  for (let i = 0; i < rows.length; ++i) {
    const status = rows[i].currentStyle ? rows[i].currentStyle.display :
                            getComputedStyle(rows[i], null).display;
    rows[i].style.display = (status === 'none') ? "table-row" : "none";
  }
}

function openFull(id){
  var modal = document.getElementById("openFull"+"_"+id);
  var img = document.getElementById("frame"+"_"+id);
  var modalImg = document.getElementById("frameModal"+"_"+id);
  var captionText = document.getElementById("caption"+"_"+id);
  img.onclick = function(){
    modal.style.display = "block";
    modalImg.src = this.src;
    captionText.innerHTML = img.alt;
  }
  var span = document.getElementById("close"+"_"+id);
  span.onclick = function() {
    modal.style.display = "none";
  }
}

function drawChart(time_data) {
  var testData = JSON.parse(time_data)
  var container = document.getElementById('timeLine');
  var chart = new google.visualization.Timeline(container);
  var dataTable = new google.visualization.DataTable();

  dataTable.addColumn({ type: 'string', id: 'Term' });
  dataTable.addColumn({ type: 'string', id: 'Phase' });
  dataTable.addColumn({ type: 'number', id: 'Start' });
  dataTable.addColumn({ type: 'number', id: 'End' });
  dataTable.addRows([
    ['1', 'Total Time', testData.navigationStart, testData.loadEventEnd ],
    ['2', 'Network', testData.navigationStart,  testData.fetchStart ],
    ['3', 'Time To First Bite', testData.fetchStart,  testData.requestStart ],
    ['4', 'Request', testData.requestStart,  testData.responseStart ],
    ['5', 'Responce', testData.responseStart,  testData.responseEnd ],
    ['6', 'Dom Processing', testData.domLoading,  testData.domComplete ],
    ['7', 'Load Event', testData.loadEventStart,  testData.loadEventEnd ]]);
    var options = {
        timeline: { showRowLabels: false},
        animation: {
        startup: true,
          duration: 1000,
          easing: 'in'
          },
      avoidOverlappingGridLines: true,
        backgroundColor: '#fff',
        colors: ['#94499C', '#1072BA', '#F2E208', '#F08821','#65B345', '#514b43']
      };
    chart.draw(dataTable, options);
    var e = document.getElementsByTagName('g')
    e[1].parentNode.removeChild(e[1])
}


function drawChartRes(resourcesData) {
  var dataVisualise = JSON.parse(resourcesData)
  var container = document.getElementById('timeLine2');
  var chart = new google.visualization.Timeline(container);
  var dataTable = new google.visualization.DataTable();

  function prepareData(data){
      var collection = []
      var iterator = 1
      for (const resources of data) {
          collection.push( [resources.initiatorType.toString() ,resources.name.substring(0,40), resources.startTime, resources.responseEnd,])
          iterator++
      }
      return collection
  }
  dataTable.addColumn({ type: 'string', id: 'Type' });
  dataTable.addColumn({ type: 'string', id: 'Name' });
  dataTable.addColumn({ type: 'number', id: 'Start' });
  dataTable.addColumn({ type: 'number', id: 'End' });
  dataTable.addRows(prepareData(dataVisualise));

  var options = {
    timeline: {
      showRowLabels: false,
      colorByRowLabel: true,
      groupByRowLabel: false,
      showBarLabels: true
    }
  };

  google.visualization.events.addListener(chart, 'select', function () {
    selection = chart.getSelection();
    if (selection.length > 0) {
      var value = dataVisualise[selection[0].row]
      createPopUp(value)
    }
  });

  chart.draw(dataTable, options);
  var e = document.getElementsByTagName('g')
  e[7].parentNode.removeChild(e[7])
}

function createPopUp(data) {
    var popUpBlock = document.getElementById('resPopUp');
    popUpBlock.style.display = "block"
    function grabDomain(string){
        var regex = /http(?:s)?:\/\/(?:[\w-]+\.)*([\w-]{1,63})(?:\.(?:\w{3}|\w{2}))(?:$|\/)/
        if (regex.test(string)){
            return regex.exec(string)[0]
        }
        else {
            return "can't extract domain"
        }
    }
    document.getElementById('resName').children[1].innerHTML = data.name
    document.getElementById('resDomain').children[1].innerHTML = grabDomain(data.name)
    document.getElementById('resInitiator').children[1].innerHTML = data.initiatorType
    document.getElementById('resDuration').children[1].innerHTML = Math.floor(data.duration) + ' ms'
    document.getElementById('resSize').children[1].innerHTML = (data.transferSize/1000) + ' kb'
}

function closeResPopUp() {
    var e = document.getElementById('resPopUp');
    e.style.display = "none";
}

function setInterval () {
  var elem = document.getElementsByClassName('google-visualization-tooltip-action');
  if(elem.length == 2) {elem[0].parentNode.removeChild(elem[0]);}
  elem = null
};


function drawGauge(number, element_id) {
    var color = "#3D9C06"
    if (number > 60 && 90 > number) {
        color = "#DEBC14"
    } else if (60 > number) {
        color = "#A03232"
    }
    var opts = {
      angle: 0.35,
      lineWidth: 0.1,
      radiusScale: 1,
      limitMax: false,
      limitMin: false,
      colorStart: color,
      colorStop: color,
      strokeColor: '#FFF',
      highDpiSupport: true,
    };
    var target = document.getElementById(element_id);
    var gauge = new Donut(target).setOptions(opts);
    gauge.maxValue = 100;
    gauge.setMinValue(0);
    gauge.animationSpeed = 32;
    gauge.set(number);
};