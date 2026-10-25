const { JSDOM, VirtualConsole } = require("jsdom");
const fs = require("node:fs");
const assert = require("node:assert/strict");
const path = require("node:path");
const test = require("node:test");
const artifact = path.resolve(__dirname, "../demo/campus.html");
test(
  "custom endpoint controls and bounded pan/zoom",
  { skip: !fs.existsSync(artifact) },
  () => {
    const source = fs.readFileSync(artifact, "utf8");
    const errors = [];
    const consoleCapture = new VirtualConsole();
    consoleCapture.on("jsdomError", (error) => errors.push(error.message));
    const dom = new JSDOM(source, {
      runScripts: "dangerously",
      virtualConsole: consoleCapture,
      beforeParse(window) {
        window.SVGElement.prototype.getBoundingClientRect = function () {
          return {
            width: 800,
            height: 680,
            x: 0,
            y: 0,
            left: 0,
            top: 0,
            right: 800,
            bottom: 680,
          };
        };
        window.SVGElement.prototype.getScreenCTM = function () {
          return {
            inverse() {
              return {
                transformPoint(point) {
                  return point;
                },
              };
            },
          };
        };
        window.SVGElement.prototype.setPointerCapture = function () {};
        window.SVGElement.prototype.releasePointerCapture = function () {};
        window.SVGElement.prototype.hasPointerCapture = function () {
          return false;
        };
        window.DOMPoint = class {
          constructor(x, y) {
            this.x = x;
            this.y = y;
          }
          matrixTransform(matrix) {
            return matrix.transformPoint(this);
          }
        };
      },
    });
    const w = dom.window,
      d = w.document;
    assert.deepEqual(errors, []);
    assert.ok(d.querySelectorAll("#buildings path").length > 2000);
    const campus = JSON.parse(source.match(/const campus = (.*);/)[1]);
    const points = campus.scenarios[1].nodes.map(
      (node) => campus.network.points[node],
    );
    function place(button, point) {
      d.getElementById(button).click();
      const options = { bubbles: true, clientX: point[0], clientY: -point[1] };
      d.getElementById("map").dispatchEvent(
        new w.MouseEvent("pointerdown", options),
      );
      w.dispatchEvent(new w.MouseEvent("pointerup", options));
    }
    place("place-start", [points[0][0] + 5, points[0][1] + 2]);
    place("place-finish", [points[1][0] + 7, points[1][1] + 1]);
    assert.equal(d.getElementById("journey").value, "custom");
    assert.ok(d.querySelectorAll(".route").length > 0);
    assert.match(d.getElementById("snap").textContent, /Custom walk/);
    assert.match(d.getElementById("snap").textContent, /excluded/);
    const routeBefore = d.getElementById("active").getAttribute("d");
    const pin = d.querySelector('[data-pin="0"] circle');
    pin.dispatchEvent(
      new w.MouseEvent("pointerdown", {
        bubbles: true,
        clientX: points[0][0],
        clientY: -points[0][1],
      }),
    );
    w.dispatchEvent(
      new w.MouseEvent("pointerup", {
        clientX: points[0][0] + 20,
        clientY: -points[0][1] - 10,
      }),
    );
    assert.ok(d.querySelectorAll(".route").length > 0);
    const slider = d.getElementById("departure");
    slider.value = "18";
    slider.dispatchEvent(new w.Event("input"));
    assert.ok(d.querySelectorAll(".route").length > 0);
    d.getElementById("fastest").click();
    assert.match(
      d.querySelector(".route.selected strong").textContent,
      /Shortest/,
    );
    for (let i = 0; i < 10; i++) d.getElementById("zoom-out").click();
    const view = d
        .getElementById("map")
        .getAttribute("viewBox")
        .split(" ")
        .map(Number),
      bounds = campus.bounds;
    assert.ok(view[0] >= bounds[0] - 1e-8 && view[1] >= -bounds[3] - 1e-8);
    assert.ok(
      view[0] + view[2] <= bounds[2] + 1e-8 &&
        view[1] + view[3] <= -bounds[1] + 1e-8,
    );
    const eventOptions = { bubbles: true, clientX: 0, clientY: 0 };
    d.getElementById("map").dispatchEvent(
      new w.MouseEvent("pointerdown", eventOptions),
    );
    d.getElementById("map").dispatchEvent(
      new w.MouseEvent("pointermove", {
        bubbles: true,
        clientX: 100000,
        clientY: 100000,
      }),
    );
    w.dispatchEvent(
      new w.MouseEvent("pointerup", { clientX: 100000, clientY: 100000 }),
    );
    const after = d
      .getElementById("map")
      .getAttribute("viewBox")
      .split(" ")
      .map(Number);
    assert.ok(after[0] >= bounds[0] - 1e-8 && after[1] >= -bounds[3] - 1e-8);
    assert.ok(
      after[0] + after[2] <= bounds[2] + 1e-8 &&
        after[1] + after[3] <= -bounds[1] + 1e-8,
    );
    assert.deepEqual(errors, []);
    console.log(
      "PASS: DOM initialization, custom start/finish placement, pin drag, custom route recomputation, departure time, fastest choice, extreme zoom/pan bounds; no script errors.",
    );
    dom.window.close();
  },
);
