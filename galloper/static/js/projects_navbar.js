(function () {
    let projectsDropdown = document.getElementById("projects-dropdown");
    let projectsDropdownItems = document.getElementById("projects-dropdown-items");
    let selectedProjectTitle = document.getElementById("selected-project");
    let selectedProjectId = document.getElementById("selected-project-id");

    function initProjectDropdown(projectData) {
        if (projectData === undefined) {
            var request = new XMLHttpRequest();
            request.open('GET', "/api/v1/project/?" + new URLSearchParams({"get_selected": true}), false);
            request.send(null);
            if (request.status === 200) {
                projectData = JSON.parse(request.responseText);
            }
        }
        if (projectData instanceof Object) {
            selectedProjectId.textContent = projectData.id;
            selectedProjectTitle.textContent = projectData.name
        }

    }

    function selectSessionProject(projectData) {
        try {
            var request = new XMLHttpRequest();
            request.open('GET', `/api/v1/project/${projectData.id}`, false);
            request.setRequestHeader("Accept", "application/json")
            request.setRequestHeader("Content-Type", "application/json")
            request.send(JSON.stringify({action: "select"}))
            if (request.status === 200) {
                let responseJson = JSON.parse(request.responseText);
                console.log(responseJson);
                initProjectDropdown(projectData);
                window.location.reload();
                return false
            }
        } catch (err) {
            console.error(err);
        }
    }

    function fillDropdown() {
        while (projectsDropdownItems.firstChild) {
            projectsDropdownItems.removeChild(projectsDropdownItems.firstChild);
        }
        var request = new XMLHttpRequest();
        request.open('GET',  "/api/v1/project/", false);
        request.send(null);
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
    }

    initProjectDropdown();

    projectsDropdown.addEventListener("click", fillDropdown, false);

    window.getSelectedProjectId = function () {
        return selectedProjectId.textContent
    };
    window.selectSessionProject = selectSessionProject;
})();
