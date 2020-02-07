var page_params = new URLSearchParams(window.location.search);
var analyticsContext=document.getElementById("chart-analytics").getContext("2d");
var analyticsData;
var analyticsLine;

function setParams(){
    build_ids = page_params.getAll("id[]");
}

function getDataForAnalysis(metric, request_name) {
$.get(
  '/report/compare/data',
  {
    scope: request_name,
    metric: metric,
    id: build_ids,
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
        data.datasets.forEach (dataset => {
            analyticsLine.data.datasets.push(dataset);
        })
        analyticsLine.update();
    }
  }
 );
}

$(document).ready(function() {
    resizeChart();
});

function resizeChart() {
    setParams();
    analyticsCanvas();
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

function downloadPic() {
    var link = document.createElement('a');
    link.download = "comparison.png"
    link.href = document.getElementById("chart-analytics").toDataURL('image/png');
    link.click();
    link.remove();
}


function switchSampler() {
    samplerType = $("#sampler").val().toUpperCase();
    resizeChart();
}
