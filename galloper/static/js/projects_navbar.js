(function () {
    let projectsDropdown = document.getElementById("projects-dropdown");
    let projectsDropdownItems = document.getElementById("projects-dropdown-items");
    let selectedProjectTitle = document.getElementById("selected-project");
    let selectedProjectId = document.getElementById("selected-project-id");

    let navSASTReport = document.getElementById("nav-sast-report");
    let navDASTReport = document.getElementById("nav-dast-report");
    let navSASTThreshold = document.getElementById("nav-sast-threshold");
    let navDASTThreshold = document.getElementById("nav-dast-threshold");
    let navUIReport = document.getElementById("nav-ui-report");
    let navUIThreshold = document.getElementById("nav-ui-threshold");

    function processNavbarItems(dastEnabled, sastEnabled, performanceEnabled) {
        if (dastEnabled === true && sastEnabled === true) {
            navSASTReport.style.display = "block";
            navDASTReport.style.display = "block";
            navSASTThreshold.style.display = "block";
            navDASTThreshold.style.display = "block";
        } else {
            navSASTReport.style.display = "none";
            navDASTReport.style.display = "none";
            navSASTThreshold.style.display = "none";
            navDASTThreshold.style.display = "none";
        }
        navUIReport.style.display = performanceEnabled ? "block" : "none";
        navUIThreshold.style.display = performanceEnabled ? "block" : "none";
    }

    function fillSelectedProject(projectData) {
        if (projectData instanceof Object) {
            selectedProjectId.textContent = projectData.id;
            selectedProjectTitle.textContent = projectData.name;
        }
        sessionStorage.setItem("proj_dast_enabled", projectData.dast_enabled);
        sessionStorage.setItem("proj_sast_enabled", projectData.sast_enabled);
        sessionStorage.setItem("proj_performance_enabled", projectData.performance_enabled);
        processNavbarItems(projectData.dast_enabled, projectData.sast_enabled, projectData.performance_enabled);
    }

    function initProjectDropdown(projectData) {
        if (projectData === undefined) {
            let request = new XMLHttpRequest();
            request.open("GET", "/api/v1/project-session", false);  // `false` makes the request synchronous
            request.send();
            if (request.status === 200) {
                projectData = JSON.parse(request.responseText);
            }
            if (request.status === 404) {
                fillDropdown();
            }
        }
        fillSelectedProject(projectData);
    }

    function setUserSession() {
        try {
            let req = new XMLHttpRequest();
            req.open("GET", `/forward-auth/me`, false);
            req.send();
            if (req.status === 200) {
                let request = new XMLHttpRequest();
                request.open("POST", `/api/v1/project-session`, false);  // `false` makes the request synchronous
                request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
                request.send(req.responseText);
                if (request.status === 200) {
                    return false;
                }
            }
            return false;
        } catch (err) {
            console.log("Request Error :-S", err);
        }
    }


    function selectSessionProject(projectData) {
        try {
            let req = new XMLHttpRequest();
            req.open("GET", `/forward-auth/me`, false);
            req.send();
            if (req.status === 200) {
                let request = new XMLHttpRequest();
                request.open("POST", `/api/v1/project-session/${projectData.id}`, false);  // `false` makes the request synchronous
                request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
                request.send(req.responseText);
                if (request.status === 200) {
                    projectData = JSON.parse(request.responseText);
                    initProjectDropdown(projectData);
                    window.location.reload();
                    return false;
                }
            }
            return false;
        } catch (err) {
            console.log("Request Error :-S", err);
        }
    }

    function fillDropdown() {
        while (projectsDropdownItems.firstChild) {
            projectsDropdownItems.removeChild(projectsDropdownItems.firstChild);
        }
        try {
            let request = new XMLHttpRequest();
            request.open("GET", `/api/v1/project`, false);  // `false` makes the request synchronous
            request.send();
            if (request.status === 200) {
                let projectsData = JSON.parse(request.responseText);
                for (let projectData of projectsData) {
                    let aElement = document.createElement("a");
                    aElement.setAttribute("class", "dropdown-item");
                    let spanElement = document.createElement("span");
                    let projectNameText = document.createTextNode(projectData.name);
                    spanElement.appendChild(projectNameText);
                    aElement.appendChild(spanElement);
                    aElement.addEventListener(
                        "click",
                        () => selectSessionProject(projectData), false
                    );
                    projectsDropdownItems.appendChild(aElement);
                }
            }
        } catch (err) {
            console.log("Request Error :-S", err);
        }
    }

    initProjectDropdown();
    setUserSession();
    projectsDropdown.addEventListener("click", fillDropdown, false);

    window.getSelectedProjectId = function () {
        return selectedProjectId.textContent
    };
    window.selectSessionProject = selectSessionProject;
})();
