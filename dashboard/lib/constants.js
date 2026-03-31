export function invertDictionary(dict) {
  return Object.fromEntries(
    Object.entries(dict).map(([key, value]) => [value, key]),
  );
}

export const moistureFilterDict = {
  "<40%": [-Infinity, 0.4, false],
  "≥40 - <45%": [0.4, 0.45, "inclusive_min_exclusive_max"],
  "≥45 - <50%": [0.45, 0.5, "inclusive_min_exclusive_max"],
  "≥50 - <55%": [0.5, 0.55, "inclusive_min_exclusive_max"],
  "≥55 - <60%": [0.55, 0.6, "inclusive_min_exclusive_max"],
  "≥60%": [0.6, Infinity, "inclusive_min_exclusive_max"],
};

export const temperatureFilterDict = {
  "<130F": [-Infinity, 130, false],
  "≥130 - <135F": [130, 135, "inclusive_min_exclusive_max"],
  "≥135 - <140F": [135, 140, "inclusive_min_exclusive_max"],
  "≥140 - <145F": [140, 145, "inclusive_min_exclusive_max"],
  "≥145 - <150F": [145, 150, "inclusive_min_exclusive_max"],
  "≥150 - <155F": [150, 155, "inclusive_min_exclusive_max"],
  "≥155 - <160F": [155, 160, "inclusive_min_exclusive_max"],
  "≥160 - <165F": [160, 165, "inclusive_min_exclusive_max"],
  "≥165F": [165, Infinity, "inclusive_min_exclusive_max"],
};

export const trialDurationDict = {
  "40-59 Days": [40, 60, "inclusive_min_exclusive_max"],
  "60-89 Days": [60, 90, "inclusive_min_exclusive_max"],
  "90-119 Days": [90, 120, "inclusive_min_exclusive_max"],
  "120+ Days": [120, Infinity, "inclusive_min_exclusive_max"],
};

export const material2col = {
  "High-Level Material Categories": "Material Class I",
  "Generic Material Categories": "Material Class II",
  "Specific Material Categories": "Material Class III",
  "Item Types": "Item Format",
};

export const col2material = invertDictionary(material2col);

export const residuals2col = {
  "Residuals Remaining": "Residuals",
  "Percent Disintegrated": "Disintegrated",
};

export const display2col = {
  "Results by Mass": "% Residuals (Mass)",
  "Results by Surface Area": "% Residuals (Area)",
};

export const class2color = {
  "Positive Control": "#70AD47",
  "Mixed Materials": "#48646A",
  Fiber: "#298FC2",
  "Compostable Polymer": "#FFB600",
};
