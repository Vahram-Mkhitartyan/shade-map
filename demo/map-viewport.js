/* Keep the entire visible map inside the loaded geographic rectangle. */
"use strict";
function constrainView(view, bounds, aspectRatio) {
  const [west, south, east, north] = bounds;
  const areaWidth = east - west,
    areaHeight = north - south;
  const maximumWidth = Math.min(areaWidth, areaHeight * aspectRatio);
  const width = Math.min(
    maximumWidth,
    Math.max(Math.min(200, maximumWidth), view[2]),
  );
  const height = width / aspectRatio;
  const centerX = view[0] + view[2] / 2;
  const centerY = view[1] + view[3] / 2;
  return [
    Math.max(west, Math.min(east - width, centerX - width / 2)),
    Math.max(-north, Math.min(-south - height, centerY - height / 2)),
    width,
    height,
  ];
}
if (typeof module !== "undefined") module.exports = { constrainView };
