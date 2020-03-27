var page_params = new URLSearchParams(window.location.search);
var analyticsContext=document.getElementById("chart-analytics").getContext("2d");
var analyticsData;
var analyticsLine;

var responseContext=document.getElementById("chart-response").getContext("2d");
var responseData;
var responseLine;

var errorsContext=document.getElementById("chart-errors").getContext("2d");
var errorsData;
var errorsLine;

var rpsContext=document.getElementById("chart-rps").getContext("2d");
var rpsData;
var rpsLine;

var benchmarkContext=document.getElementById("chart-benchmark").getContext("2d");
var benchmarkLine;
var benchmarkData;
var aggregator="auto";
var request="";
var calculation="";



function setParams(){
    build_ids = page_params.getAll("id[]");
}



function getPerTestData() {
    $.get(
  '/api/v1/compare/tests',
    {
    id: build_ids,
    },
      function( data ) {
        responseData = data['response'];
        errorsData = data['errors'];
        rpsData = data['rps'];
        responsesCanvas();
        errorsCanvas();
        rpsCanvas();
      }
 );
}


function getDataForAnalysis(metric, request_name) {
$.get(
  '/api/v1/compare/data',
  {
    scope: request_name,
    metric: metric,
    id: build_ids,
    low_value: $("#input-slider-range-value-low").html(),
    high_value: $("#input-slider-range-value-high").html()
  },
  function( data ) {
    if (analyticsLine.data.labels.length == 0 || analyticsLine.data.labels.length != data.labels.length)
    {
        analyticsData = data;
        analyticsCanvas();
    } else {
        data.datasets.forEach (dataset => {
            analyticsLine.data.datasets.push(dataset);
        })
        analyticsLine.update();
    }
  }
 );
}

function resizeChart() {
    setParams();
    analyticsCanvas();
    getPerTestData();
    switchAggregator();
}

function findAndRemoveDataSet(dataset_name){
    index_to_remove = []
    for (var i=0; i<analyticsLine.data.datasets.length; i++) {
        if (analyticsLine.data.datasets[i].label.includes(dataset_name.split("_")[1])) {
            index_to_remove.push(i)
        }
    }
    index_to_remove.reverse().forEach(index => {
    analyticsLine.data.datasets.splice(index, 1);
    })
    analyticsLine.update();
}

function getData(scope, request_name) {
    if (! $(`#${request_name}_${scope}`).is(":checked")) {
        findAndRemoveDataSet(`${request_name}_${scope}`);
    } else {
        getDataForAnalysis(scope, request_name)
    }
}


function responsesCanvas() {
    responseLine = Chart.Line(responseContext, {
        data: responseData,
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
                },
                {
                    type: "linear", // only linear but allow scale type registration. This allows extensions to exist solely for log scale for instance
                    display: true,
                    position: "right",
                    scaleLabel: {
                        display: true,
                        labelString: "Users"
                    },
                    id: "active_users",
                }],
            }
        }
    });
}

function errorsCanvas() {
    errorsLine = Chart.Line(errorsContext, {
        data: errorsData,
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
                        labelString: "Errors"
                    },
                    id: "count",
                    gridLines: {
                        drawOnChartArea: false, // only want the grid lines for one axis to show up
                    },
                },
                {
                    type: "linear", // only linear but allow scale type registration. This allows extensions to exist solely for log scale for instance
                    display: true,
                    position: "right",
                    scaleLabel: {
                        display: true,
                        labelString: "Users"
                    },
                    id: "active_users",
                }],
            }
        }
    });
}

function rpsCanvas() {
    rpsLine = Chart.Line(rpsContext, {
        data: rpsData,
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
                        labelString: "RPS, count"
                    },
                    id: "count",
                    gridLines: {
                        drawOnChartArea: false, // only want the grid lines for one axis to show up
                    },
                },
                {
                    type: "linear", // only linear but allow scale type registration. This allows extensions to exist solely for log scale for instance
                    display: true,
                    position: "right",
                    scaleLabel: {
                        display: true,
                        labelString: "Users"
                    },
                    id: "active_users",
                }],
            }
        }
    });
}


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

function downloadPic(chart_id) {
    var link = document.createElement('a');
    link.download = chart_id+".png"
    link.href = document.getElementById(chart_id).toDataURL('image/png');
    link.click();
    link.remove();
}


function switchSampler() {
    samplerType = $("#sampler").val().toUpperCase();
    resizeChart();
}

function loadBenchmarkData(aggregator, request, calculation) {
    $.get(
      "/api/v1/compare/benchmark",
      {
        id: page_params.getAll("id[]"),
        aggregator: aggregator,
        request: request,
        status: status,
        calculation: calculation
      }, function( data ) {
        benchmarkData = data["data"]
        if(benchmarkLine!=null){
            benchmarkLine.destroy();
        }
        drawCanvas(data["label"]);
      }
     );
}

function drawCanvas(y_label) {
    benchmarkLine = Chart.Line(benchmarkContext, {
        data: benchmarkData,
        options: {
            responsive: true,
            hoverMode: 'index',
            stacked: false,
            legend: {
                display: true,
                position: 'bottom',
                labels: {
                    fontSize: 10,
                    usePointStyle: false,
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
                    id: "data",
                }],
            }
        }
    });
}

function switchAggregator() {
    aggregator = $("#timeaggr").val();
    request = $("#requestsaggr").val();
    calculation = $("#calculationaggr").val();
    status = $("#status").val();
    loadBenchmarkData(aggregator, request, calculation, status);
}

$(document).ready(function() {
    resizeChart();
});
