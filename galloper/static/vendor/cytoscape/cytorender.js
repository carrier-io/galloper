var page_params = new URLSearchParams(window.location.search);
Promise.all([
  fetch('/static/vendor/cytoscape/cytostyle.json').then(function(res) { return res.json() }),
  fetch(`/api/v1/visual/${getSelectedProjectId()}/${page_params.get("report_id")}/chart`).then(function(res) { return res.json() })
]).then(function(dataArray) {
    var cy = window.cy = cytoscape({
        container: document.getElementById('cy'),
        layout: {name: 'avsdf', nodeSeparation: 300 },
        ready: function(){ console.log("done") },
        style: dataArray[0],
        elements: dataArray[1]
    });
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
             a= document.createElement('a');
             a.target= '_blank';
             a.href= `/api/v1/artifacts/${getSelectedProjectId()}/${elem.data('bucket')}/${elem.data('file')}`;
             a.click();
             a.remove();
            }
        }
    ]});
//    cy.cxtmenu({
//        selector: 'core',
//        commands: [
//        {
//            content: 'bg1',
//            select: function(){
//                console.log( 'bg1' );
//            }
//        },
//        {
//            content: 'bg2',
//            select: function(){
//                console.log( 'bg2' );
//            }
//        }
//    ]});
});
