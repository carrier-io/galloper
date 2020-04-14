document.addEventListener("DOMContentLoaded", function(){

    function createInner(value, icon, text, description) {
        return `<div class="blockelem create-flowy noselect">
        <input type="hidden" name="blockelemtype" class="blockelemtype" value="${value}">
        <div class="grabme"><i class="fas fa-ellipsis-v"></i><i class="fas fa-ellipsis-v"></i></div>
        <div class="blockin">
            <div class="blockico"><span></span><i class="fas fa-${icon}"></i></div>
            <div class="blocktext">
                <p class="blocktitle">${text}</p>
                <p class="blockdesc">${description}</p>
            </div>
        </div>
    </div>`
    }

    function createTileInner(icon, text, explanation) {
        return `
        <div class='blockyleft'>
            <i class="fas fa-${icon}"></i>
            <p class='blockyname'>${text}</p>
        </div>
        <div class='blockyright'><i class="fas fa-ellipsis-h"></i></div>
        <div class='blockydiv'></div>
        <div class='blockyinfo'>${explanation}</div>
        `
    }

    var rightcard = false;
    var tempblock;
    var tempblock2;

    var triggersInner = `
    ${createInner("1", "globe-europe", "Open", "Navigates to a page")}
    ${createInner("2", "mouse", "Click", "Clicks on element")}
    ${createInner("3", "keyboard", "Type", "Types text to an element")}
    ${createInner("4", "i-cursor", "Send Keys", "Send a key or sequence to an element")}
    ${createInner("5", "clock", "Wait", "Wait for element to became visible")}
    `

    var actionsInner = `
    ${createInner("6", "arrow-circle-down", "GET", "HTTP method to retrieve data")}
    ${createInner("7", "arrow-circle-up", "POST", "HTTP method to send data")}
    ${createInner("8", "arrow-alt-circle-up", "PUT", "HTTP method to update data")}
    ${createInner("9", "times-circle", "DELETE", "HTTP method to delete data")}
    `

    document.getElementById("blocklist").innerHTML = triggersInner;

    flowy(document.getElementById("canvas"), drag, release, snapping);
    function addEventListenerMulti(type, listener, capture, selector) {
        var nodes = document.querySelectorAll(selector);
        for (var i = 0; i < nodes.length; i++) {
            nodes[i].addEventListener(type, listener, capture);
        }
    }
    function snapping(drag, first) {
        var grab = drag.querySelector(".grabme");
        grab.parentNode.removeChild(grab);
        var blockin = drag.querySelector(".blockin");
        blockin.parentNode.removeChild(blockin);
        // UI objects
        if (drag.querySelector(".blockelemtype").value == "1") {
            drag.innerHTML += createTileInner("globe-europe", "Open", "When a <span>new visitor</span> goes to <span>Site 1</span>")
        } else if (drag.querySelector(".blockelemtype").value == "2") {
            drag.innerHTML += createTileInner("mouse", "Click", "When <span>Action 1</span> is performed");
        } else if (drag.querySelector(".blockelemtype").value == "3") {
            drag.innerHTML += createTileInner("keyboard", "Type", "When <span>10 seconds</span> have passed");
        } else if (drag.querySelector(".blockelemtype").value == "4") {
            drag.innerHTML += createTileInner("i-cursor", "Send Keys", "When <span>Error 1</span> is triggered");
        } else if (drag.querySelector(".blockelemtype").value == "5") {
            drag.innerHTML += createTileInner("clock", "Wait", "Add <span>Data object</span> to <span>Database 1</span>");
        // API objects
        } else if (drag.querySelector(".blockelemtype").value == "6") {
            drag.innerHTML += createTileInner("arrow-circle-down", "GET", "Update <span>Database 1</span>");
        } else if (drag.querySelector(".blockelemtype").value == "7") {
            drag.innerHTML += createTileInner("arrow-circle-up", "POST", "Perform <span>Action 1</span");
        } else if (drag.querySelector(".blockelemtype").value == "8") {
            drag.innerHTML += createTileInner("arrow-alt-circle-up", "PUT", "Tweet <span>Query 1</span> with the account <span>@alyssaxuu</span>");
        } else if (drag.querySelector(".blockelemtype").value == "9") {
            drag.innerHTML += createTileInner("times-circle", "DELETE", "Tweet <span>Query 1</span> with the account <span>@alyssaxuu</span>");
        }
        return true;
    }
    function drag(block) {
        block.classList.add("blockdisabled");
        tempblock2 = block;
    }
    function release() {
        if (tempblock2) {
            tempblock2.classList.remove("blockdisabled");
        }
    }

    var disabledClick = function(){
        document.querySelector(".navactive").classList.add("navdisabled");
        document.querySelector(".navactive").classList.remove("navactive");
        this.classList.add("navactive");
        this.classList.remove("navdisabled");
        if (this.getAttribute("id") == "triggers") {
            document.getElementById("blocklist").innerHTML = triggersInner;
        } else if (this.getAttribute("id") == "actions") {
            document.getElementById("blocklist").innerHTML = actionsInner;
        }
    }
    addEventListenerMulti("click", disabledClick, false, ".side");
    document.getElementById("close").addEventListener("click", function(){
       if (rightcard) {
           rightcard = false;
           document.getElementById("properties").classList.remove("expanded");
           setTimeout(function(){
                document.getElementById("propwrap").classList.remove("itson");
           }, 300);
            tempblock.classList.remove("selectedblock");
       }
    });

document.getElementById("removeblock").addEventListener("click", function(){
 flowy.deleteBlocks();
});

var aclick = false;
var noinfo = false;
var beginTouch = function (event) {
    aclick = true;
    noinfo = false;
    if (event.target.closest(".create-flowy")) {
        noinfo = true;
    }
}
var checkTouch = function (event) {
    aclick = false;
}
var doneTouch = function (event) {
    if (event.type === "mouseup" && aclick && !noinfo) {
      if (!rightcard && event.target.closest(".block") && !event.target.closest(".block").classList.contains("dragging")) {
            tempblock = event.target.closest(".block");
            rightcard = true;
            document.getElementById("properties").classList.add("expanded");
            document.getElementById("propwrap").classList.add("itson");
            tempblock.classList.add("selectedblock");
       }
    }
}
addEventListener("mousedown", beginTouch, false);
addEventListener("mousemove", checkTouch, false);
addEventListener("mouseup", doneTouch, false);
addEventListenerMulti("touchstart", beginTouch, false, ".block");
});
