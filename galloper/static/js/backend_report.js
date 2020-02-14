var page_params = new URLSearchParams(window.location.search);
var presetsContext=document.getElementById("chart-requests").getContext("2d");
var analyticsContext=document.getElementById("chart-analytics").getContext("2d");
var samplerType;
var build_id;
var test_name;
var lg_type;
var lineChartData;
var analyticsData;
var analyticsLine;
var aggregator="auto";

function setParams(){
    build_id = page_params.get("build_id");
    test_name = page_params.get("test_name");
    lg_type = page_params.get("lg_type");
    samplerType = $("#sampler").val().toUpperCase();
    if (build_id == null) {
        build_id = document.querySelector("[property~=build_id][content]").content;
        lg_type = document.querySelector("[property~=lg_type][content]").content;
        test_name = document.querySelector("[property~=test_name][content]").content;
    }
}

function displayAnalytics() {
    if ( ! $("#analytics").is(":visible") ) {
        $("#preset").hide();
        analyticsCanvas();
        $("#analytics").show();
        if(window.presetLine!=null){
            window.presetLine.destroy();
        }
    }
}

function loadRequestData(url, y_label) {
    if ( ! $("#preset").is(":visible") ) {
        $("#preset").show();
        $("#analytics").hide();
        if(analyticsLine!=null){
            analyticsLine.destroy();
        }
    }
    $.get(
      url,
      {
        build_id: build_id,
        test_name: test_name,
        lg_type: lg_type,
        sampler: samplerType,
        aggregator: aggregator,
        start_time: $("#start_time").html(),
        end_time: $("#end_time").html(),
        low_value: $("#input-slider-range-value-low").html(),
        high_value: $("#input-slider-range-value-high").html()
      }, function( data ) {
        lineChartData = $.parseJSON(data);
        if(window.presetLine!=null){
            window.presetLine.destroy();
        }
        drawCanvas(y_label);
      }
     );
}

function fillTable(){
    $.get(
    '/report/request/table',
    {
        build_id: build_id,
        test_name: test_name,
        lg_type: lg_type,
        sampler: samplerType,
        start_time: $("#start_time").html(),
        end_time: $("#end_time").html(),
        low_value: $("#input-slider-range-value-low").html(),
        high_value: $("#input-slider-range-value-high").html()
    },
    function( data ) {
        var tbody = $("#summary_table > tbody")
        tbody.empty();
        $.parseJSON(data).forEach( item => {
            tbody.append(`<tr><td>${item["request_name"]}</td><td>${item["total"]}</td><td>${item["throughput"]}</td><td>${item["ko"]}</td><td>${item["min"]}</td><td>${item["pct50"]}</td><td>${item["pct95"]}</td><td>${item["max"]}</td></tr>`)
        });
    });
}

function findAndRemoveDataSet(dataset_name){
    for (var i=0; i<analyticsLine.data.datasets.length; i++) {
        if (analyticsLine.data.datasets[i].label === dataset_name) {
            analyticsLine.data.datasets.splice(i, 1);
            analyticsLine.update();
            break;
        }
    }
}

function getDataForAnalysis(metric, request_name) {
$.get(
  '/report/request/data',
  {
    scope: request_name,
    metric: metric,
    build_id: build_id,
    test_name: test_name,
    lg_type: lg_type,
    sampler: samplerType,
    aggregator: aggregator,
    start_time: $("#start_time").html(),
    end_time: $("#end_time").html(),
    low_value: $("#input-slider-range-value-low").html(),
    high_value: $("#input-slider-range-value-high").html()
  },
  function( data ) {
    data = $.parseJSON(data);
    if (analyticsLine.data.labels.length == 0 || analyticsLine.data.labels.length != data.labels.length)
    {
        analyticsData = data;
        analyticsCanvas();
    } else {
        analyticsLine.data.datasets.push(data.datasets[0]);
        analyticsLine.update();
    }
  }
 );
}

function getData(scope, request_name) {
    if (! $(`#${request_name}_${scope}`).is(":checked")) {
        findAndRemoveDataSet(`${request_name}_${scope}`);
    } else {
        getDataForAnalysis(scope, request_name)
    }
}


$(document).ready(function() {
    setParams();
    loadRequestData('/report/requests/summary', "Response time, ms");
    analyticsCanvas();
    fillTable();
    fillErrorTable();
    $('#RT').trigger( "click" )
    $("#analytics").hide();
});

function analyticsCanvas() {
    analyticsLine = Chart.Line(analyticsContext, {
        data: analyticsData,
        options: {
            responsive: true,
            hoverMode: 'index',
            stacked: false,
            legend: {
                display: true,
                position: 'bottom',
                labels: {
                    fontSize: 10,
                    usePointStyle: false
                }
            },
            title:{
                display: false,
            },
            scales: {
                yAxes: [{
                    type: "linear", // only linear but allow scale type registration. This allows extensions to exist solely for log scale for instance
                    display: true,
                    position: "left",
                    scaleLabel: {
                        display: true,
                        labelString: "Response Time, ms"
                    },
                    id: "time",
                }, {
                    type: "linear", // only linear but allow scale type registration. This allows extensions to exist solely for log scale for instance
                    display: true,
                    position: "right",
                    scaleLabel: {
                        display: true,
                        labelString: "Count"
                    },
                    id: "count",
                    gridLines: {
                        drawOnChartArea: false, // only want the grid lines for one axis to show up
                    },
                }],
            }
        }
    });
}

function drawCanvas(y_label) {
    window.presetLine = Chart.Line(presetsContext, {
        data: lineChartData,
        options: {
            responsive: true,
            hoverMode: 'index',
            stacked: false,
            legend: {
                display: true,
                position: 'right',
                labels: {
                    fontSize: 10,
                    usePointStyle: false,
                    filter: function(legendItem, data) {
                        return legendItem.text != "Active Users";
                    }
                }
            },
            title:{
                display: false,
            },
            scales: {
                yAxes: [{
                    type: "linear", // only linear but allow scale type registration. This allows extensions to exist solely for log scale for instance
                    display: true,
                    position: "left",
                    scaleLabel: {
                        display: true,
                        labelString: y_label
                    },
                    id: "response_time",
                }, {
                    type: "linear", // only linear but allow scale type registration. This allows extensions to exist solely for log scale for instance
                    display: true,
                    position: "right",
                    scaleLabel: {
                        display: true,
                        labelString: "Active users"
                    },
                    id: "active_users",
                    gridLines: {
                        drawOnChartArea: false, // only want the grid lines for one axis to show up
                    },
                }],
            }
        }
    });
}

document.getElementById('input-slider-range').noUiSlider.on('set', function() { resizeChart(); });

function recalculateAnalytics() {
    var iterator = document.evaluate("//div[@id='analytics']//input[@type='checkbox']", document, null, XPathResult.UNORDERED_NODE_ITERATOR_TYPE, null );
    var el = iterator.iterateNext();
    var arr = []
    while (el) {
        if (el.checked) {
            arr.push(el)
        }
        el = iterator.iterateNext();
    }
    arr.forEach(el => el.onchange());
}

function resizeChart() {
    if ( $("#analytics").is(":visible") ){
        analyticsData = null;
        analyticsLine.destroy();
        analyticsCanvas();
        recalculateAnalytics();
    }
    ["RT", "AR", "HT", "AN"].forEach( item => {
        if ($(`#${item}`).hasClass( "active" )) {
            $(`#${item}`).trigger( "click" );
        }
    });
    fillTable();
    fillErrorTable();
}

function downloadPic() {
    var canvas;
    var name;
    if ( $("#analytics").is(":visible") ){
         canvas = document.getElementById("chart-analytics")
         name = "analytics.png"
    } else {
        canvas = document.getElementById("chart-requests")
        name = "requests.png"
    }
    var link = document.createElement('a');
    link.download = name;
    link.href = canvas.toDataURL('image/png');
    link.click();
    link.remove();
}

function switchSampler() {
    samplerType = $("#sampler").val().toUpperCase();
    resizeChart();
}

function switchAggregator() {
    aggregator = $("#aggregator").val();
    console.log(aggregator)
    resizeChart();
}


function fillErrorTable() {
    var start_time = $("#start_time").html()
    var end_time = $("#end_time").html()
    var low_value = $("#input-slider-range-value-low").html()
    var high_value = $("#input-slider-range-value-high").html()
    $("#errors").bootstrapTable('refreshOptions', {url: `/report/request/issues?test_name=${test_name}&start_time=${start_time}&end_time=${end_time}&low_value=${low_value}&high_value=${high_value}`})
}
