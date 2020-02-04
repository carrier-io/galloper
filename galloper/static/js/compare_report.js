var page_params = new URLSearchParams(window.location.search);
var chartUsers=document.getElementById("chart-users").getContext("2d");
var chartResponse=document.getElementById("chart-response").getContext("2d");
var chartErrors=document.getElementById("chart-errors").getContext("2d");
var chartHits=document.getElementById("chart-hits").getContext("2d");
var usersLine;
var responsesLine;
var errorsLine;
var hitsLine;
var usersData;
var responsesData;
var errorsData;
var hitsData;

function setParams(){
    build_ids = page_params.getAll("id");
}

function loadUsersData() {

    url = "/report/compare/users?"
    low_value = $("#input-slider-range-value-low").html()
    high_value=$("#input-slider-range-value-high").html()
    build_ids.forEach(item => {
        url += `id=${item}&`
    })
    url += `low_value=${low_value}&high_value=${high_value}`,
    $.get(
      url,
      function( data ) {
        console.log(data);
        usersData = $.parseJSON(data);
        if(usersLine!=null){
            usersLine.destroy();
        }
        usersCanvas();
      }
     );
}

function loadResponsesData() {

    url = "/report/compare/response?"
    low_value = $("#input-slider-range-value-low").html()
    high_value=$("#input-slider-range-value-high").html()
    build_ids.forEach(item => {
        url += `id=${item}&`
    })
    url += `low_value=${low_value}&high_value=${high_value}`,
    $.get(
      url,
      function( data ) {
        console.log(data);
        responsesData = $.parseJSON(data);
        if(responsesLine!=null){
            responsesLine.destroy();
        }
        responsesCanvas();
      }
     );
}

$(document).ready(function() {
    resizeChart();
});

function usersCanvas() {
    usersLine = Chart.Line(chartUsers, {
        data: usersData,
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
                        labelString: "Users"
                    },
                    id: "users",
                }],
            }
        }
    });
}

function responsesCanvas() {
    responsesLine = Chart.Line(chartResponse, {
        data: responsesData,
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
                    id: "responses",
                }],
            }
        }
    });
}

function errorsCanvas() {
    errorsLine = Chart.Line(chartErrors, {
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
                    id: "errors",
                }],
            }
        }
    });
}

function hitsCanvas() {
    hitsLine = Chart.Line(chartHits, {
        data: hitsData,
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
                        labelString: "Hits"
                    },
                    id: "hits",
                }],
            }
        }
    });
}

document.getElementById('input-slider-range').noUiSlider.on('set', function() { resizeChart(); });

function resizeChart() {
    setParams();
    loadUsersData();
    loadResponsesData();
    errorsCanvas();
    hitsCanvas();
}
