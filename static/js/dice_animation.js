
import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.module.js";

const el = (id) => document.getElementById(id);

const canvas = el("dice_canvas");
const stage = el("dice_stage");
const status = el("dice_status");
const form = el("dice_form");
const button = el("roll_button");

const typeSelect = el("dice_type");
const countInput = el("number");
const modifierInput = el("modifier");
const modeSelect = el("roll_type");

const resultPanel = el("dice_results");

const validTypes = new Set([
    "d4", "d6", "d8", "d10", "d12", "d20", "d100"
]);


// THREE.JS SCENE


const scene = new THREE.Scene();

const camera = new THREE.PerspectiveCamera(
    40, 1, 0.1, 100
);

const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: true
});

renderer.setPixelRatio(
    Math.min(window.devicePixelRatio || 1, 2)
);

renderer.outputColorSpace = THREE.SRGBColorSpace;

// LIGHTING


scene.add(
    new THREE.HemisphereLight(
        0xf6eaff,
        0x302044,
        2.4
    )
);

const keyLight = new THREE.DirectionalLight(
    0xffffff, 3
);

keyLight.position.set(4, 7, 5);
scene.add(keyLight);

const fillLight = new THREE.PointLight(
    0xa36cff, 24
);

fillLight.position.set(-4, 2, 3);
scene.add(fillLight);


// DICE STATE


const diceRoot = new THREE.Group();
scene.add(diceRoot);

const clock = new THREE.Clock();

let dice = [];
let rolling = false;
let busy = false;
let rollStartedAt = 0;
let resultReceived = null;
let rollFinished = false;

const ROLL_MS = 1800;

// D10 GEOMETRY


function d10Geometry() {

    const vertices = [
        new THREE.Vector3(0, 1.55, 0),
        new THREE.Vector3(0, -1.55, 0)
    ];

    for (let i = 0; i < 10; i++) {

        const angle = i * Math.PI / 5;

        vertices.push(
            new THREE.Vector3(
                Math.cos(angle),
                i % 2 === 0 ? 0.32 : -0.32,
                Math.sin(angle)
            )
        );
    }

    const faces = [];

    function tri(a, b, c) {

        for (const j of [a, b, c]) {
            faces.push(...vertices[j].toArray());
        }
    }

    for (let i = 0; i < 10; i++) {

        const a = i + 2;
        const b = ((i + 1) % 10) + 2;
        const c = ((i + 2) % 10) + 2;

        if (i % 2 === 0) {
            tri(0, a, b);
            tri(1, b, c);
        } else {
            tri(1, a, b);
            tri(0, b, c);
        }
    }

    const geometry = new THREE.BufferGeometry();

    geometry.setAttribute(
        "position",
        new THREE.Float32BufferAttribute(faces, 3)
    );

    geometry.computeVertexNormals();

    return geometry;
}

// CREATE DIE MESH


function dieMesh(type) {

    const geometry = ({
        d4: () => new THREE.TetrahedronGeometry(1.15),
        d6: () => new THREE.BoxGeometry(1.65, 1.65, 1.65),
        d8: () => new THREE.OctahedronGeometry(1.18),
        d10: () => d10Geometry(),
        d12: () => new THREE.DodecahedronGeometry(1.18),
        d20: () => new THREE.IcosahedronGeometry(1.2)
    })[type]();

    const mesh = new THREE.Mesh(
        geometry,
        new THREE.MeshStandardMaterial({
            color: 0x8050b5,
            metalness: 0.25,
            roughness: 0.3,
            flatShading: true,
            side: THREE.DoubleSide
        })
    );

    const edges = new THREE.LineSegments(
        new THREE.EdgesGeometry(geometry),
        new THREE.LineBasicMaterial({
            color: 0xf3d8ff
        })
    );

    mesh.add(edges);

    return mesh;
}


// REMOVE OLD DICE


function destroyDice() {

    while (diceRoot.children.length) {

        const node = diceRoot.children[0];

        diceRoot.remove(node);

        node.traverse((part) => {

            if (part.geometry) {
                part.geometry.dispose();
            }

            if (part.material) {

                const materials = Array.isArray(part.material)
                    ? part.material
                    : [part.material];

                materials.forEach((material) => {
                    material.dispose();
                });
            }
        });
    }

    dice = [];
}


// BUILD SELECTED DICE


function rebuildDice() {

    if (rolling || busy) {
        return;
    }

    const type = typeSelect.value;

    if (!validTypes.has(type)) {
        return;
    }

    if (type !== "d20") {
        modeSelect.value = "normal";
    }

    destroyDice();

    const count = Math.min(
        12,
        Math.max(
            1,
            Number.parseInt(countInput.value, 10) || 1
        )
    );

    const columns = Math.ceil(Math.sqrt(count));
    const rows = Math.ceil(count / columns);

    const spacing = type === "d100" ? 2.9 : 2.25;

    for (let i = 0; i < count; i++) {

        const group = new THREE.Group();

        if (type === "d100") {

            const tens = dieMesh("d10");
            const ones = dieMesh("d10");

            tens.position.x = -0.67;
            ones.position.x = 0.67;

            tens.scale.setScalar(0.64);
            ones.scale.setScalar(0.64);

            group.add(tens, ones);

        } else {

            group.add(dieMesh(type));
        }

        group.position.x =
            ((i % columns) - (columns - 1) / 2) * spacing;

        group.position.z =
            (Math.floor(i / columns) - (rows - 1) / 2) * spacing;

        group.rotation.set(0.22, 0.38, 0.12);

        group.userData.homeX = group.position.x;
        group.userData.homeZ = group.position.z;

        diceRoot.add(group);
        dice.push(group);
    }

    camera.position.set(
        0,
        3.2 + rows * 0.65,
        6.5 + columns * 2.5
    );

    camera.lookAt(0, 0, 0);

    status.textContent =
        `${type.toUpperCase()} ready to roll`;
}


// RESIZE CANVAS


function resize() {

    const width = stage.clientWidth;
    const height = stage.clientHeight;

    if (!width || !height) {
        return;
    }

    renderer.setSize(width, height, false);

    camera.aspect = width / height;
    camera.updateProjectionMatrix();
}


// DISPLAY FLASK RESULT


function showResult(result) {

    el("result_dice").textContent = result.dice_type;

    el("result_rolls").textContent =
        JSON.stringify(result.rolls);

    el("result_modifier").textContent =
        result.modifier;

    el("result_total").textContent =
        result.total;

    resultPanel.hidden = false;

    status.textContent =
        `${result.dice_type} roll complete`;

    busy = false;
    button.disabled = false;
}


// ANIMATION LOOP


function tick() {

    requestAnimationFrame(tick);

    const delta = Math.min(clock.getDelta(), 0.05);

    if (rolling) {

        const t = Math.min(
            1,
            (performance.now() - rollStartedAt) / ROLL_MS
        );

        const intensity = (1 - t) ** 1.25;

        dice.forEach((group, i) => {

            group.rotation.x +=
                delta * 13 * intensity *
                (i % 2 ? -1 : 1);

            group.rotation.y +=
                delta * 17 * intensity;

            group.rotation.z +=
                delta * 9 * intensity;

            group.position.y =
                Math.abs(Math.sin(t * Math.PI * 7)) *
                intensity;

            group.position.x =
                group.userData.homeX +
                Math.sin(t * 17 + i) *
                0.18 * intensity;

            group.position.z =
                group.userData.homeZ +
                Math.cos(t * 15 + i) *
                0.18 * intensity;

            if (typeSelect.value === "d100") {

                group.children.forEach((child, index) => {

                    child.rotation.y +=
                        delta *
                        (index ? -11 : 11) *
                        intensity;

                    child.rotation.x +=
                        delta * 8 * intensity;
                });
            }
        });

        if (t >= 1) {

            rolling = false;
            rollFinished = true;

            dice.forEach((group) => {

                group.position.set(
                    group.userData.homeX,
                    0,
                    group.userData.homeZ
                );
            });

            status.textContent = "Waiting for result...";

            if (resultReceived) {
                showResult(resultReceived);
            }
        }

    } else {

        dice.forEach((group) => {
            group.rotation.y += delta * 0.12;
        });
    }

    renderer.render(scene, camera);
}


// ROLL DICE WITHOUT RELOADING PAGE


async function roll() {

    if (busy || rolling) {
        return;
    }

    if (!form.reportValidity()) {
        return;
    }

    const type = typeSelect.value;
    const count = Number(countInput.value);
    const mode = modeSelect.value;

    if (
        !validTypes.has(type) ||
        !Number.isInteger(count) ||
        count < 1 ||
        count > 100
    ) {
        status.textContent =
            "Choose a valid die and count (1-100).";
        return;
    }

    if (
        mode !== "normal" &&
        (type !== "d20" || count !== 1)
    ) {
        status.textContent =
            "Advantage/disadvantage requires one D20.";
        return;
    }

    // Collect form data BEFORE disabling controls.
    const data = new FormData(form);

    data.set("dice_type", type);
    data.set("number", String(count));
    data.set("modifier", modifierInput.value);
    data.set("roll_type", mode);

    // Rebuild the currently selected die.
    rebuildDice();

    busy = true;
    rolling = true;
    rollFinished = false;
    resultReceived = null;

    rollStartedAt = performance.now();

    resultPanel.hidden = true;
    button.disabled = true;

    status.textContent =
        `Rolling ${type.toUpperCase()}...`;

    try {

        const response = await fetch(form.action, {
            method: "POST",
            body: data,
            headers: {
                "Accept": "application/json"
            }
        });

        if (!response.ok) {

            throw new Error(
                `Flask returned HTTP ${response.status}`
            );
        }

        const result = await response.json();

        if (
            !result ||
            result.dice_type !== type.toUpperCase() ||
            !Array.isArray(result.rolls)
        ) {
            throw new Error(
                "Unexpected JSON response from Flask"
            );
        }

        resultReceived = result;

        if (rollFinished) {
            showResult(result);
        }

    } catch (error) {

        console.error("Dice request failed:", error);

        rolling = false;
        busy = false;

        button.disabled = false;

        status.textContent =
            `Roll failed: ${error.message}`;
    }
}


// EVENT LISTENERS


button.addEventListener("click", roll);

form.addEventListener("submit", (event) => {
    event.preventDefault();
    roll();
});

typeSelect.addEventListener("change", rebuildDice);

countInput.addEventListener("input", rebuildDice);

window.addEventListener("resize", resize);

// INITIALIZE


resize();
rebuildDice();
tick();

console.log("NEW dice_animation.js loaded");
