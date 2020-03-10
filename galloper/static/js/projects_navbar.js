(function () {
    let projectsDropdown = document.getElementById("projects-dropdown");
    let projectsDropdownItems = document.getElementById("projects-dropdown-items");

    async function selectProject(projectId) {
        try {
            let response = await fetch(
                `/api/v1/project/${projectId}`,
                {
                    method: "POST",
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({action: "select"})
                }
            );
            let responseJson = await response.json();
            console.error(responseJson);
        } catch (err) {
            console.error(err);
            // Handle errors here
        }
    }


    async function fillDropdown() {

        while (projectsDropdownItems.firstChild) {
            projectsDropdownItems.removeChild(projectsDropdownItems.firstChild);
        }

        let response = await fetch("/api/v1/project", {method: "GET"});
        let projectsData = await response.json();
        for (let projectData of projectsData) {
            let aElement = document.createElement("a");
            aElement.setAttribute("class", "dropdown-item");
            let spanElement = document.createElement("span");
            let projectNameText = document.createTextNode(projectData.name);
            spanElement.appendChild(projectNameText);
            aElement.appendChild(spanElement);
            aElement.addEventListener("click", () => selectProject(projectData.id), false);
            projectsDropdownItems.appendChild(aElement);
        }
    }

    projectsDropdown.addEventListener("click", fillDropdown, false);

})();
