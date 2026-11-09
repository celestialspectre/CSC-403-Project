
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

let raceBonuses = [];
let classSkills = [];

const abilities = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"];

const standardArray = [15, 14, 13, 12, 10, 8];

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

function displayRaceInfo() {
    const raceInfo = document.getElementById("raceInfo");

    const race = races.find(r => r.id === Number(raceSelect.value));

    if (!race) {
        raceInfo.replaceChildren();
        return;
    }

    const bonuses = raceBonuses.filter(bonus =>
        bonus.subrace_id === null || bonus.subrace_id === Number(subraceSelect.value)
    );

    const lines = [
        // `${race.description}`  this is where a description would go
        `Speed: ${race.speed} feet`,
        ...bonuses.map(bonus => `${bonus.ability} +${bonus.bonus}`)
    ];

    raceInfo.replaceChildren();

    for (const line of lines) {
        const paragraph = document.createElement("p");
        paragraph.textContent = line;
        raceInfo.appendChild(paragraph);
    }

    updateAbilityScores();

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

classSelect.addEventListener("change", async () => {
    const classInfo = document.getElementById("classInfo");

    const selectedClass = classes.find(
        c => c.id === Number(classSelect.value)
    );

    classInfo.replaceChildren();
    classSkills = [];

    if (!selectedClass) return;

    const classID = classSelect.value;

    try {
        // get class skills
        const response = await fetch(`/api/classes/${classID}/skills`);

        if (!response.ok) {
            throw new Error("Could not load class skills.");
        }

        const skills = await response.json();

        if (classSelect.value !== classID) {
            return;
        }

        classSkills = skills;

        // display info
        const details = document.createElement("p");
        details.textContent =
            `Hit Die: d${selectedClass.hit_dice} | ` +
            `Choose ${selectedClass.starting_skills} skills`;

        classInfo.appendChild(details);

        // make checkbox for each skill
        for (const skill of classSkills) {
            const label = document.createElement("label");
            const checkbox = document.createElement("input");

            checkbox.type = "checkbox";
            checkbox.value = skill.id;
            checkbox.name = "class-skill";

            label.appendChild(checkbox);
            label.append(
                ` ${skill.name} (${skill.ability})`
            );

            classInfo.appendChild(label);
        }

    } catch (error) {
        document.getElementById("form-error").textContent = error.message;
    }
});

raceSelect.addEventListener("change", async () => {
    subraceSelect.replaceChildren();

    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "Select a subrace"
    subraceSelect.appendChild(placeholder);
    subraceSelect.disabled = true;

    const raceID = raceSelect.value;

    raceBonuses = [];
    displayRaceInfo();

    if (!raceID) {
        return;
    }

    try {
        // get subraces for this race
        const subRaceResponse = await fetch(`/api/races/${raceID}/subraces`);
        const bonusResponse = await fetch(`/api/races/${raceID}/bonuses`);

        if (!subRaceResponse.ok) {
            throw new Error("Could not load subraces.");
        }

        if (!bonusResponse.ok) { 
            throw new Error("Could not load racial bonuses.");
        }

        const subraces = await subRaceResponse.json();
        const bonuses = await bonusResponse.json();
        
        // if player changes their race
        if (raceSelect.value !== raceID) {
            return;
        }

        raceBonuses = bonuses;
        displayRaceInfo();

        // if there are subraces
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

subraceSelect.addEventListener("change", () => {
    displayRaceInfo();
    updateAbilityScores();
});

function calculateAbilityMod(score) {
    return Math.floor((score - 10) / 2);
}

function getRaceBonus(ability) {
    return raceBonuses.filter(bonus =>
        bonus.ability === ability && (
            bonus.subrace_id === null || bonus.subrace_id === Number(subraceSelect.value)
        )
    ).reduce((total, bonus) => total + bonus.bonus, 0);
}

function createAbilityScores() {
    const container = document.getElementById("abilityScores");

    container.replaceChildren();

    for (const ability of abilities) {
        const row = document.createElement("div");
        row.className = "ability-row";

        const label = document.createElement("label");
        label.className = "ability-name";
        label.textContent = ability.substring(0,3).toUpperCase() + "\t";

        const select = document.createElement("select");
        select.id = `ability-${ability}`;
        label.htmlFor = select.id;

        const placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.textContent = "--";
        select.appendChild(placeholder);

        for (const score of standardArray) {
            const option = document.createElement("option");
            option.value = score;
            option.textContent = score;
            select.appendChild(option);
        }

        const plus = document.createElement("span");
        plus.className = "ability-symbol";
        plus.textContent = " + ";

        const bonus = document.createElement("span");
        bonus.className = "ability-bonus";
        bonus.id = `bonus-${ability}`;

        const equals = document.createElement("span");
        equals.className = "ability-symbol";
        equals.textContent = " = ";

        const finalScore = document.createElement("span");
        finalScore.className = "ability-final";
        finalScore.id = `result-${ability}`;

        const modifier = document.createElement("span");
        modifier.className = "ability-modifier";
        modifier.id = `modifier-${ability}`;

        select.addEventListener("change", updateAbilityScores);

        row.append(label, select, plus, bonus, equals, finalScore, modifier);

        container.appendChild(row);
    }

    updateAbilityScores();
}

function updateAbilityScores() {
    const selects = abilities.map(ability => document.getElementById(`ability-${ability}`));

    const usedScores = selects.map(select => select.value).filter(value => value !== "");

    for (const ability of abilities) {
        const select = document.getElementById(`ability-${ability}`);
        const bonus = document.getElementById(`bonus-${ability}`);
        const result = document.getElementById(`result-${ability}`);
        const modifier = document.getElementById(`modifier-${ability}`);

        const racialBonus = getRaceBonus(ability);
        bonus.textContent = racialBonus;

        for (const option of select.options) {
            if (option.value === "") continue;

            option.disabled = usedScores.includes(option.value) && option.value !== select.value;
        }

        if (select.value === "") {
            result.textContent = "--";
            modifier.textContent = ""
            continue;
        }

        const baseScore = Number(select.value);
        const finalScore = baseScore + racialBonus;

        const abilityMod = calculateAbilityMod(finalScore);


        result.textContent = finalScore;

        modifier.textContent = `(${abilityMod >= 0 ? "+" : ""}${abilityMod})`;
    }
}


function displayReview() {
    const review = document.getElementById("characterReview");

    review.replaceChildren();

    const characterName = document.getElementById("character-name").value.trim();

    const selectedRace = races.find(r => r.id === Number(raceSelect.value));

    const selectedSubrace = subraceSelect.value ? subraceSelect.options[subraceSelect.selectedIndex].textContent : "None";

    const selectedClass = classes.find(c => c.id === Number(classSelect.value));

    const checkedSkills = document.querySelectorAll('input[name="class-skill"]:checked');

    const selectedSkills = Array.from(checkedSkills).map(checkbox => {
        const skill = classSkills.find(s => s.id === Number(checkbox.value));
        return skill ? skill.name : "Unknown Skill";
    });

    // helper function to add an element
    function addDetail(label, value) {
        const paragraph = document.createElement("p");

        const boldLabel = document.createElement("strong");
        boldLabel.textContent = `${label}: `;

        paragraph.append(boldLabel, value);
        review.appendChild(paragraph);
    }

    // display overall details
    addDetail("Character Name", characterName);
    addDetail("Race", selectedRace ? selectedRace.name : "Unknown");
    addDetail("Subrace", selectedSubrace);
    addDetail("Class", selectedClass ? selectedClass.name : "Unknown");

    // display hit dice
    if (selectedClass) {
        addDetail("Hit Die", `d${selectedClass.hit_dice}`);
    }

    // heading
    const abilityHeading = document.createElement("h3");
    abilityHeading.textContent = "Ability Scores";
    review.appendChild(abilityHeading);

    // for each ability score
    for (const ability of abilities) {

        // Get the base score from the dropdown.
        const baseScore = Number(document.getElementById(`ability-${ability}`).value);
        const racialBonus = getRaceBonus(ability);
        const finalScore = baseScore + racialBonus;

        const modifier = calculateAbilityMod(finalScore);
        const modifierText = modifier >= 0 ? `+${modifier}` : `${modifier}`;

        addDetail(ability, `${finalScore} (${modifierText})`);
    }

    // skills
    const skillsHeading = document.createElement("h3");
    skillsHeading.textContent = "Proficiencies";
    review.appendChild(skillsHeading);

    addDetail("Skills", selectedSkills.length > 0 ? selectedSkills.join(", ") : "None");
}

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

    if (index === steps.length - 1) {
        displayReview();
    }
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

            if (!subraceSelect.disabled && subraceSelect.value === "") {
                errorMessage.textContent = "Please select a subrace.";
                return false;
            }
            break;
        case 2:
            if (classSelect.value === "") {
                errorMessage.textContent = "Please select a class.";
                return false
            }

            const selectedClass = classes.find(c => c.id === Number(classSelect.value));

            const checkedSkills = document.querySelectorAll('input[name="class-skill"]:checked');

            if (checkedSkills.length !== selectedClass.starting_skills) {
                errorMessage.textContent = `Please select exactly ${selectedClass.starting_skills} skill(s).`;
                return false;
            }
            break;
        case 3:
            const selectedScores = abilities.map(ability => document.getElementById(`ability-${ability}`).value);

            if (selectedScores.some(score => score === "")) {
                errorMessage.textContent = "Please assign all six ability scores.";
                return false;
            }

            if (new Set(selectedScores).size !== 6) {
                errorMessage.textContent = "You may only use each score once.";
                return false;
            }
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
createAbilityScores();

initialiseCharacterCreator()