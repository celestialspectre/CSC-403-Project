
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <title>D&D Character Hub - Dice Roller</title>

    <link rel="stylesheet"
          href="{{ url_for('static', filename='styles/skeleton.css') }}">

    <style>
        .dice-layout {
            width: 90%;
            max-width: 900px;
            margin: 25px auto;
            box-sizing: border-box;
        }

        .dice-layout h2 {
            color: #30251e;
            text-align: center;
            margin: 20px 0;
        }

        .dice-stage {
            position: relative;
            width: 100%;
            height: 330px;
            margin: 25px auto;
            background: radial-gradient(
                ellipse at center,
                #493160 0%,
                #21172e 65%,
                #100d17 100%
            );
            border: 3px solid #9274b4;
            border-radius: 15px;
            overflow: hidden;
            box-sizing: border-box;
        }

        #dice-canvas {
            display: block;
            width: 100%;
            height: 100%;
        }

        .dice-stage-label {
            position: absolute;
            bottom: 12px;
            left: 0;
            width: 100%;
            color: #f2e5ff;
            text-align: center;
            font-family: "Young Serif", serif;
            font-size: 14px;
            pointer-events: none;
        }

        .dice-form {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 18px;
            max-width: 650px;
            margin: 20px auto;
        }

        .dice-field {
            display: flex;
            flex-direction: column;
            gap: 8px;
            text-align: left;
        }

        .dice-layout .dice-field label {
            color: #30251e;
            text-align: left;
            font-size: 16px;
        }

        .dice-field input,
        .dice-field select {
            width: 100%;
            min-height: 42px;
            padding: 10px;
            border: 1px solid #777;
            border-radius: 6px;
            background: white;
            color: #222;
            box-sizing: border-box;
        }

        .dice-form-footer {
            grid-column: 1 / -1;
            text-align: center;
        }

        .dice-form-footer button {
            padding: 12px 30px;
            font-size: 18px;
            cursor: pointer;
        }

        .dice-form-footer p {
            color: #333;
            font-size: 13px;
        }

        .dice-results {
            max-width: 650px;
            margin: 25px auto;
            padding: 20px;
            background: rgba(255, 250, 240, 0.9);
            border: 2px solid #9274b4;
            border-radius: 10px;
            text-align: center;
            box-sizing: border-box;
        }

        .dice-results h2,
        .dice-results p {
            color: #30251e;
            text-align: center;
            margin: 12px 0;
        }

        .dice-results .total {
            font-size: 28px;
            font-weight: bold;
            color: #543376;
        }

        .dice-navigation {
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 15px;
            margin: 25px 0;
        }

        .dice-navigation form {
            margin: 0;
        }

        .dice-navigation button {
            padding: 10px 20px;
            cursor: pointer;
        }

        @media (max-width: 600px) {
            .dice-layout {
                width: 95%;
                padding: 15px;
            }

            .dice-form {
                grid-template-columns: 1fr;
            }

            .dice-stage {
                height: 260px;
            }
        }
    </style>
</head>

<body>
<center>

    <div id="triangle-down" class="border-decor"></div>

    <div class="login_border dice-layout">

        <h1>Welcome to the D&D Character Hub!</h1>
        <h2>3D Dice Roller</h2>

        <!-- 3D DICE DISPLAY -->

        <div class="dice-stage">
            <canvas id="dice-canvas"></canvas>

            <div class="dice-stage-label" id="dice-status">
                Choose your dice and roll!
            </div>
        </div>

        <!-- DICE ROLLER FORM -->

        <form action="{{ url_for('dice_roller') }}"
              method="POST"
              class="dice-form"
              id="dice-form">

            <div class="dice-field">
                <label for="dice_type">Select Dice Type</label>

                <select id="dice_type" name="dice_type" required>
                    <option value="d4">D4</option>
                    <option value="d6">D6</option>
                    <option value="d8">D8</option>
                    <option value="d10">D10</option>
                    <option value="d12">D12</option>
                    <option value="d20" selected>D20</option>
                    <option value="d100">D100</option>
                </select>
            </div>

            <div class="dice-field">
                <label for="number">Number of Dice</label>

                <input type="number"
                       id="number"
                       name="number"
                       min="1"
                       max="100"
                       value="1"
                       required>
            </div>

            <div class="dice-field">
                <label for="modifier">Modifier</label>

                <input type="number"
                       id="modifier"
                       name="modifier"
                       value="0"
                       required>
            </div>

            <div class="dice-field">
                <label for="roll_type">Roll Type</label>

                <select id="roll_type" name="roll_type" required>
                    <option value="normal">Normal Roll</option>
                    <option value="advantage">Advantage (D20)</option>
                    <option value="disadvantage">Disadvantage (D20)</option>
                </select>
            </div>

            <div class="dice-form-footer">
                <button type="submit" id="roll-button">
                    Roll Dice
                </button>

                <p>
                    Note: Advantage and Disadvantage
                    require exactly one D20.
                </p>
            </div>

        </form>

        <!-- FLASK ROLL RESULTS -->

        {% if result %}

        <div class="dice-results" id="roll-results">
            <h2>Roll Results</h2>

            <p>
                <strong>Dice:</strong>
                {{ result["dice_type"] }}
            </p>

            <p>
                <strong>Individual Rolls:</strong>
                {{ result["rolls"] }}
            </p>

            <p>
                <strong>Modifier:</strong>
                {{ result["modifier"] }}
            </p>

            <h2 class="total">
                Total: {{ result["total"] }}
            </h2>
        </div>

        {% endif %}

        <!-- NAVIGATION -->

        <div class="dice-navigation">

            <form action="{{ url_for('character_creator') }}"
                  method="GET">
                <button type="submit">
                    Character Creator
                </button>
            </form>

            <form action="{{ url_for('main_menu') }}"
                  method="GET">
                <button type="submit">
                    Return to Main Menu
                </button>
            </form>

        </div>

    </div>

    <marquee>
        <img src="{{ url_for('static', filename='img/dnd.png') }}"
             style="width: 10%; height: auto;"
             alt="D&D decoration">
    </marquee>

    <div id="triangle-up" class="border-decor"></div>

</center>

<!-- THREE.JS -->

<script type="module">

import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.module.js";

const canvas = document.getElementById("dice-canvas");
const stage = document.querySelector(".dice-stage");
const status = document.getElementById("dice-status");

const diceType = document.getElementById("dice_type");
const diceForm = document.getElementById("dice-form");
const rollType = document.getElementById("roll_type");
const numberInput = document.getElementById("number");

const scene = new THREE.Scene();

const camera = new THREE.PerspectiveCamera(
    45, 1, 0.1, 100
);

camera.position.set(0, 2.5, 7);
camera.lookAt(0, 0, 0);

const renderer = new THREE.WebGLRenderer({
    canvas: canvas,
    antialias: true,
    alpha: true
});

renderer.setPixelRatio(
    Math.min(window.devicePixelRatio, 2)
);

scene.add(new THREE.AmbientLight(0xffffff, 1.4));

const directionalLight = new THREE.DirectionalLight(
    0xd5b3ff, 3
);
directionalLight.position.set(4, 6, 5);
scene.add(directionalLight);

const purpleLight = new THREE.PointLight(
    0x9b59ff, 30
);
purpleLight.position.set(-3, 2, 3);
scene.add(purpleLight);

let diceGroup = new THREE.Group();
scene.add(diceGroup);

let rolling = false;
let rollStart = 0;

const clock = new THREE.Clock();


// CREATE A TEN-SIDED TRAPEZOHEDRON

function createD10Geometry() {
    const sides = 10;
    const half = sides / 2;
    const vertices = [];

    // Top and bottom poles
    vertices.push(0, 1.3, 0);
    vertices.push(0, -1.3, 0);

    // Alternating upper/lower ring vertices
    for (let i = 0; i < sides; i++) {
        const angle = i * Math.PI * 2 / sides;
        const y = i % 2 === 0 ? 0.3 : -0.3;

        vertices.push(
            Math.cos(angle),
            y,
            Math.sin(angle)
        );
    }

    const positions = [];

    function addTriangle(a, b, c) {
        const indices = [a, b, c];

        for (const index of indices) {
            const offset = index * 3;
            positions.push(
                vertices[offset],
                vertices[offset + 1],
                vertices[offset + 2]
            );
        }
    }

    // Ten kite-shaped faces, triangulated
    for (let i = 0; i < sides; i++) {
        const next = (i + 1) % sides;
        const currentIndex = i + 2;
        const nextIndex = next + 2;

        if (i % 2 === 0) {
            addTriangle(0, currentIndex, nextIndex);
        } else {
            addTriangle(1, nextIndex, currentIndex);
        }
    }

    const geometry = new THREE.BufferGeometry();

    geometry.setAttribute(
        "position",
        new THREE.Float32BufferAttribute(positions, 3)
    );

    geometry.computeVertexNormals();

    return geometry;
}


// CREATE ONE DIE

function createDie(type) {
    let geometry;

    switch (type) {
        case "d4":
            geometry = new THREE.TetrahedronGeometry(1.2);
            break;

        case "d6":
            geometry = new THREE.BoxGeometry(1.6, 1.6, 1.6);
            break;

        case "d8":
            geometry = new THREE.OctahedronGeometry(1.25);
            break;

        case "d10":
        case "d100":
            geometry = createD10Geometry();
            break;

        case "d12":
            geometry = new THREE.DodecahedronGeometry(1.2);
            break;

        case "d20":
        default:
            geometry = new THREE.IcosahedronGeometry(1.25);
            break;
    }

    const material = new THREE.MeshStandardMaterial({
        color: 0x6934a3,
        metalness: 0.45,
        roughness: 0.3,
        flatShading: true,
        side: THREE.DoubleSide
    });

    const mesh = new THREE.Mesh(geometry, material);

    const edges = new THREE.EdgesGeometry(geometry);

    const outline = new THREE.LineSegments(
        edges,
        new THREE.LineBasicMaterial({
            color: 0xe2c7ff
        })
    );

    mesh.add(outline);

    return mesh;
}


// UPDATE DISPLAYED DICE

function createDice(type) {
    while (diceGroup.children.length > 0) {
        const child = diceGroup.children[0];
        diceGroup.remove(child);

        child.traverse(function(object) {
            if (object.geometry) {
                object.geometry.dispose();
            }

            if (object.material) {
                object.material.dispose();
            }
        });
    }

    if (type === "d100") {
        // Percentile rolls use two D10 models.
        const tensDie = createDie("d10");
        const onesDie = createDie("d10");

        tensDie.position.x = -1.2;
        onesDie.position.x = 1.2;

        tensDie.scale.setScalar(0.85);
        onesDie.scale.setScalar(0.85);

        diceGroup.add(tensDie);
        diceGroup.add(onesDie);
    } else {
        diceGroup.add(createDie(type));
    }

    diceGroup.rotation.set(0, 0, 0);
    diceGroup.position.y = 0;
}


// RESIZE CANVAS

function resizeCanvas() {
    const width = stage.clientWidth;
    const height = stage.clientHeight;

    if (!width || !height) {
        return;
    }

    renderer.setSize(width, height, false);

    camera.aspect = width / height;
    camera.updateProjectionMatrix();
}

window.addEventListener("resize", resizeCanvas);
resizeCanvas();


// START ROLL ANIMATION

function startRoll() {
    rolling = true;
    rollStart = performance.now();

    diceGroup.rotation.set(
        Math.random() * Math.PI,
        Math.random() * Math.PI,
        Math.random() * Math.PI
    );

    status.textContent = "Rolling...";
}


// ANIMATION LOOP

function animate() {
    requestAnimationFrame(animate);

    const delta = clock.getDelta();

    if (rolling) {
        const elapsed = (
            performance.now() - rollStart
        ) / 1000;

        const speed = Math.max(
            0,
            1 - elapsed / 2.2
        );

        diceGroup.rotation.x += delta * 13 * speed;
        diceGroup.rotation.y += delta * 16 * speed;
        diceGroup.rotation.z += delta * 8 * speed;

        diceGroup.position.y =
            Math.abs(Math.sin(elapsed * 10)) *
            0.65 * speed;

        if (elapsed >= 2.2) {
            rolling = false;
            diceGroup.position.y = 0;
            status.textContent = "Roll complete!";
        }
    } else {
        diceGroup.rotation.y += delta * 0.2;
    }

    renderer.render(scene, camera);
}


// CHANGE DICE TYPE

diceType.addEventListener("change", function() {
    rolling = false;
    createDice(this.value);
    status.textContent = "Ready to roll!";
});


// VALIDATE ADVANTAGE / DISADVANTAGE

diceForm.addEventListener("submit", function(event) {
    if (
        rollType.value !== "normal" &&
        (
            diceType.value !== "d20" ||
            Number(numberInput.value) !== 1
        )
    ) {
        event.preventDefault();

        alert(
            "Advantage and Disadvantage require exactly one D20."
        );
    }
});


// INITIALIZE

createDice(diceType.value);
animate();

const hasResult =
    document.getElementById("roll-results") !== null;

if (hasResult) {
    startRoll();
}

</script>

</body>
</html>
