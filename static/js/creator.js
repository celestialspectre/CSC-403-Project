
// current step in character creation
let currentStep = 0;

// get all elements with .form-step (so the 5 steps of the creator)
const steps = document.querySelectorAll(".form-step");

// get all elements with .step-label (so the 5 labels)
const stepLabels = document.querySelectorAll(".step-label");

// get the back and next buttons
const backButton = document.getElementById("back");
const nextButton = document.getElementById("next");

const raceSelect = document.getElementById("race");
const subraceSelect = document.getElementById("subrace");
const classSelect = document.getElementById("class");

let races = [];
let classes = [];

async function loadRaces() {
    // get api data for races
    const response = await fetch("/api/races");

    if (!response.ok) {
        throw new Error("Could not load races.");
    }

    // convert to JS array
    races = await response.json()

    // create option for each race
    for (const race of races) {
        const option = document.createElement("option");

        option.value = race.id;
        option.textContent = race.name;
        raceSelect.appendChild(option);
    }
}

async function loadClasses() {
    // get api data for classes
    const response = await fetch("/api/classes");

    if (!response.ok) {
        throw new Error("Could not load classes.");
    }

    // convert to JS array
    classes = await response.json()

    //create option for each class
    for (const cclass of classes) {
        const option = document.createElement("option");

        option.value = cclass.id;
        option.textContent = cclass.name;
        classSelect.appendChild(option);
    }
}

raceSelect.addEventListener("change", async () => {
    subraceSelect.replaceChildren();

    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "Select a subrace"
    subraceSelect.appendChild(placeholder);
    subraceSelect.disabled = true;

    const raceID = raceSelect.value;

    if (!raceID) {
        return;
    }

    try {
        const response = await fetch(`/api/races/${raceID}/subraces`)

        if (!response.ok) {
            throw new Error("Could not load subraces.")
        }

        const subraces = await response.json();

        if (raceSelect.value !== raceID) {
            return;
        }

        if (subraces.length > 0) {
            subraceSelect.disabled = false;

            for (const subrace of subraces) {
                const option = document.createElement("option");

                option.value = subrace.id;
                option.textContent = subrace.name;

                subraceSelect.appendChild(option);
            }
        }
    } catch (error) {
        document.getElementById("form-error").textContent = error.message;
    }
});

// displays whatever the current step is
function showStep(index) {
    steps.forEach((step, i) => {
        // if i = index, then toggle active, otherwise disactivate
        step.classList.toggle("active", i === index)
    });

    stepLabels.forEach((label, i) => {
        label.classList.toggle("active", i === index)
    });

    // disable back button on first step
    backButton.disabled = index === 0;
    // change next button to "finish" when on last step
    nextButton.textContent = index === steps.length - 1 ? "Finish" : "Next";
}

function checkIfComplete() {
    const errorMessage = document.getElementById("form-error");
    errorMessage.textContent = "";

    switch (currentStep) {
        case 0:
            if (document.getElementById("character-name").value.trim() === "") {
                errorMessage.textContent = "Please enter your character's name.";
                return false
            }
            break;
        case 1:
            if (raceSelect.value === "") {
                errorMessage.textContent = "Please select a race.";
                return false
            }
            break;
        case 2:
            if (classSelect.value === "") {
                errorMessage.textContent = "Please select a class.";
                return false
            }
            break;
        case 3:
            break;
        case 4:
            break;
    }
    return true;
}

// when next button is clicked
nextButton.addEventListener("click", () => {
    if (!checkIfComplete()) {
        return;
    }

    // advance to next step
    if (currentStep < steps.length-1) {
        currentStep++;
        showStep(currentStep);
    } else {
        alert("ihcehi")
    }
});

// when back button is clicked
backButton.addEventListener("click", () => {
    // go back to previous step
    if (currentStep > 0) {
        currentStep--;
        showStep(currentStep);
    }
});

async function initialiseCharacterCreator() {
    try {
        await Promise.all([loadRaces(), loadClasses()]);
    } catch (error) {
        document.getElementById("form-error").textContent = error.message;
    }
}

// initialise first step
showStep(currentStep);

initialiseCharacterCreator()