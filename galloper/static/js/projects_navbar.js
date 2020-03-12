(async function () {
    let projectsDropdown = document.getElementById("projects-dropdown");
    let projectsDropdownItems = document.getElementById("projects-dropdown-items");
    let selectedProjectTitle = document.getElementById("selected-project");
    let selectedProjectId = document.getElementById("selected-project-id");

    async function initProjectDropdown(projectData) {
        if (projectData === undefined) {
            let response = await fetch(
                "/api/v1/project/?" + new URLSearchParams({"get_selected": true}),
                {method: "GET"}
            );
            projectData = await response.json();
        }

        selectedProjectId.textContent = projectData.id;
        selectedProjectTitle.textContent = projectData.name
    }

    async function selectProject(projectData) {
        try {
            let response = await fetch(
                `/api/v1/project/${projectData.id}`,
                {
                    method: "POST",
                    headers: {
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({action: "select"})
                }
            );
            let responseJson = await response.json();
            console.log(responseJson);
            await initProjectDropdown(projectData);
        } catch (err) {
            console.error(err);
            // Handle errors here
        }
    }

    async function fillDropdown() {

        while (projectsDropdownItems.firstChild) {
            projectsDropdownItems.removeChild(projectsDropdownItems.firstChild);
        }

        let response = await fetch(
            "/api/v1/project/", {method: "GET"}
        );
        let projectsData = await response.json();
        for (let projectData of projectsData) {
            let aElement = document.createElement("a");
            aElement.setAttribute("class", "dropdown-item");
            // TODO Pass Project is used in session flag to dropdown
            // let usedInSession = projectData.used_in_session;
            let spanElement = document.createElement("span");
            let projectNameText = document.createTextNode(projectData.name);
            spanElement.appendChild(projectNameText);
            aElement.appendChild(spanElement);
            aElement.addEventListener(
                "click",
                () => selectProject(projectData), false
            );
            projectsDropdownItems.appendChild(aElement);
        }
    }

    await initProjectDropdown();

    projectsDropdown.addEventListener("click", fillDropdown, false);

    window.getSelectedProjectId = function () {
        return selectedProjectId.textContent
    };
})();
