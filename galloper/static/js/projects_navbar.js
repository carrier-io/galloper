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
            if (response.status === 200) {
                projectData = await response.json();
            }
        }
        if (projectData instanceof Object) {
            selectedProjectId.textContent = projectData.id;
            selectedProjectTitle.textContent = projectData.name
        }

    }

    async function selectSessionProject(projectData) {
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
            if (response.status === 200) {
                let responseJson = await response.json();
                console.log(responseJson);
                await initProjectDropdown(projectData);
                window.location.reload();
                return false
            }
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
        if (response.status === 200) {
            let projectsData = await response.json();
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

    await initProjectDropdown();

    projectsDropdown.addEventListener("click", fillDropdown, false);

    window.getSelectedProjectId = function () {
        return selectedProjectId.textContent
    };
    window.selectSessionProject = selectSessionProject;
})();
