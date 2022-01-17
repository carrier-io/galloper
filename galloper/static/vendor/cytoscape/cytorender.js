var page_params = new URLSearchParams(window.location.search);

function renderCy() {
    var metric = $("#metric").val();
    var cy = window.cy = cytoscape({
        container: document.getElementById('cy'),
        layout: {
            name: 'euler',
            springLength: edge => 30,
            springCoeff: edge => 0.0008,
            gravity: -12.5,
            randomize: true,
            fit: true,
            animate: true
        },
        ready: function(){ console.log("done") },
        style: fetch('/static/vendor/cytoscape/cytostyle.json').then(function(res) { return res.json() }),
        elements: fetch(`/api/v1/visual/${getSelectedProjectId()}/${page_params.get("report_id")}/chart?metric=${metric}`).then(function(res) { return res.json() }),
        userPanningEnabled: false,
        userZoomingEnabled: false,
        maxZoom: 2.5,
    });

    var maxZoom = cy.maxZoom();

    cy.fit();

    if( cy.zoom() > maxZoom ){
      cy.zoom( maxZoom );
      cy.center();
    }

    cy.cxtmenu({
        selector: 'node', // we can add ctx for edge and for everything else, which is cool
        commands: [
        {
            content: '<span><i class="fas fa-camera"></i> Steps</span',
            select: function(ele){
            },
            enabled: false
        },
        {
            content: '<span><i class="fas fa-tachometer-alt"></i> Perf</span',
            select: function(elem){
             let a= document.createElement('a');
             a.target= '_blank';
             a.href= `${elem.data('file')}`;
             a.click();
             a.remove();
            }
        },
        {
            content: '<span><i class="fas fa-tachometer-alt"></i>Rename</span>',
            select: function(elem){
                $('#exampleModal').on('show.bs.modal', function (event) {
                  var modal = $(this)
                  modal.find('.modal-title').html(`Rename page: <br><br> ${elem.data('name')}`)
                  $("#resultId").val(elem.data('result_id'))
                  $("#resultIdentifier").val(elem.data('identifier'))
                })

                $('#exampleModal').modal('show')
            }
        }
    ]});

}
