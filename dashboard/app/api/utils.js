import * as d3 from "d3";
import {
  class2color,
  moistureFilterDict,
  temperatureFilterDict,
  trialDurationDict,
} from "@/lib/constants";
import { loadData } from "./constants";

const calculateQuartiles = (data, key) => {
  const sorted = data.map((d) => parseFloat(d[key])).sort((a, b) => a - b);
  const max = d3.max(sorted);
  const min = d3.min(sorted);
  const q1 = d3.quantile(sorted, 0.25);
  const q3 = d3.quantile(sorted, 0.75);
  const upperfence = Math.min(q3 + 1.5 * (q3 - q1), max);
  const lowerfence = Math.max(q1 - 1.5 * (q3 - q1), min);
  const outliers = sorted.filter((v) => v > upperfence || v < lowerfence);
  return {
    lowerfence,
    q1,
    median: Math.round(d3.quantile(sorted, 0.5) * 1000) / 1000,
    mean: Math.round(d3.mean(sorted) * 1000) / 1000,
    q3,
    upperfence,
    max,
    min,
    outliers,
    color: class2color[data[0]["Material Class I"]],
  };
};

const getFilteredTrialIDs = (data, column, low, high, inclusive) => {
  return data
    .filter((trial) => {
      const value = parseFloat(trial[column]);
      if (inclusive === "inclusive_min_exclusive_max") {
        return value >= low && value < high;
      }
      if (inclusive) {
        return value >= low && value <= high;
      }
      return value > low && value < high;
    })
    .map((trial) => trial["Trial ID"]);
};

const filterTrialIDsByConditions = (
  column,
  filters,
  operatingConditions,
  filterDict,
) => {
  const trialIDs = new Set();
  filters.forEach((filter) => {
    if (filters.length === Object.keys(filterDict).length) {
      operatingConditions.forEach((condition) =>
        trialIDs.add(condition["Trial ID"]),
      );
      return Array.from(trialIDs);
    } else {
      const [low, high, inclusive] = filterDict[filter];
      const filteredTrialIDs = getFilteredTrialIDs(
        operatingConditions,
        column,
        low,
        high,
        inclusive,
      );
      filteredTrialIDs.forEach((id) => trialIDs.add(id));
    }
  });
  return trialIDs;
};

const filterData = (data, column, conditions) => {
  if (conditions.some((condition) => condition.includes("All"))) {
    return data;
  }
  return data.filter((row) =>
    conditions.some((condition) => row[column] === condition),
  );
};

const getIntersectingTrialIDs = (...sets) => {
  if (sets.length === 0 || sets.some((set) => set.size === 0)) {
    return new Set();
  }
  const [firstSet, ...restSets] = sets;
  const intersection = [...firstSet].filter((item) =>
    restSets.every((set) => set.has(item)),
  );
  return new Set(intersection);
};

const toOrderMap = (arr) => new Map(arr.map((v, i) => [v, i]));

const materialClassIOrderMap = toOrderMap([
  "Fiber",
  "Compostable Polymer",
  "Mixed Materials",
  "Positive Control",
]);

const materialClassIIOrderMap = toOrderMap([
  "Lined Fiber",
  "Unlined Fiber",
  "Rigid Compostable Polymer (< 0.75mm)",
  "Rigid Compostable Polymer (> 0.75mm)",
  "Compostable Polymer Film/Bag",
  "Positive Control - Food Scraps",
  "Positive Control - Fiber",
  "Positive Control - Film",
]);

const materialClassIIIOrderMap = toOrderMap([
  "PLA-lined Paper",
  "PLA-lined Bagasse",
  "PLA-lined Mixed Fiber",
  "PLA-lined Bamboo Paper",
  "Agave",
  "Paper",
  "Bagasse",
  "Mixed Fiber",
  "PLA",
  "CPLA",
  "PBAT",
  "PHA",
  "Mixed Compostable Polymer",
  "PBAT & Other Materials",
  "Cellulose",
  "Positive Control - Food Scraps",
  "Positive Control - Unlined Paper",
  "Kraft Paper",
  "Positive Control - Cellulose Film",
]);

const ordinalOrders = {
  "Material Class II": materialClassIIOrderMap,
  "Material Class III": materialClassIIIOrderMap,
};

const ordinalSort = (orderMap, a, b) => {
  const aIdx = orderMap.get(a);
  const bIdx = orderMap.get(b);
  if (aIdx !== undefined && bIdx !== undefined) return aIdx - bIdx;
  if (aIdx !== undefined) return -1;
  if (bIdx !== undefined) return 1;
  return a.localeCompare(b, undefined, { numeric: true, sensitivity: "base" });
};

export const prepareData = async (searchParams, useTestData = false) => {
  // Display params
  const aggCol = searchParams.get("aggcol") || "Material Class I";
  const displayCol = searchParams.get("displaycol") || "% Residuals (Mass)";
  const uncapResults = searchParams.get("uncapresults") === "true" || false;
  const displayResiduals = searchParams.get("displayresiduals") === "true";
  // Trial and item filters
  const testMethod = searchParams.get("testmethod") || "Mesh Bag";
  const timepoint = searchParams.get("timepoint") || "Final";
  const technologies = searchParams.get("technologies")
    ? searchParams.get("technologies").split(",")
    : [];
  const materials = searchParams.get("materials")
    ? searchParams.get("materials").split(",")
    : [];
  const specificMaterials = searchParams.get("specificMaterials")
    ? searchParams.get("specificMaterials").split(",")
    : [];
  const formats = searchParams.get("formats")
    ? searchParams.get("formats").split(",")
    : [];
  const brands = searchParams.get("brands")
    ? searchParams.get("brands").split(",")
    : [];
  // Operating conditions filters
  const temperatureFilter = searchParams.get("temperature")
    ? searchParams.get("temperature").split(",")
    : [];
  const moistureFilter = searchParams.get("moisture")
    ? searchParams.get("moisture").split(",")
    : [];
  const trialDurations = searchParams.get("trialdurations")
    ? searchParams.get("trialdurations").split(",")
    : [];

  const noFiltersSelected = [
    technologies,
    materials,
    specificMaterials,
    brands,
    formats,
    temperatureFilter,
    moistureFilter,
    trialDurations,
  ].some((f) => f.length === 0);

  if (noFiltersSelected) {
    return {
      message:
        "”None” is selected for at least one filtering criteria. Please ensure you have at least one option selected for each filter.",
    };
  }

  let { trialData, operatingConditions } = await loadData(useTestData);
  var filteredData = [...trialData];

  // Filter out rows where displayCol is empty or null
  filteredData = filteredData.filter(
    (d) => d[displayCol] !== "" && d[displayCol] !== null,
  );

  // filter data based on selected filters
  filteredData = filterData(filteredData, "Test Method", [testMethod]);
  // TODO: Enable final and midpoint timepoint filters
  // filteredData = filterData(filteredData, "Timepoint", [timepoint]);
  filteredData = filterData(filteredData, "Technology", technologies);
  // Return empty object to preserve privacy if not enough trials (Except for Bulk Dose)
  const technologyTrialIDs = new Set(filteredData.map((d) => d["Trial ID"]));
  const trialThreshold = testMethod === "Bulk Dose" ? 1 : 3;
  if (technologyTrialIDs.size < trialThreshold && testMethod !== "Bulk Dose") {
    return {
      message:
        "There are not enough trials for the selected technology. Please select more options.",
    };
  }

  filteredData = filterData(filteredData, "Material Class II", materials);
  filteredData = filterData(
    filteredData,
    "Material Class III",
    specificMaterials,
  );
  filteredData = filterData(filteredData, "Item Format", formats);
  filteredData = filterData(filteredData, "Item Brand", brands);

  if (!uncapResults) {
    filteredData = filteredData.map((d) => {
      if (d[displayCol] > 1) {
        d[displayCol] = 1;
      }
      return d;
    });
  }

  if (!displayResiduals) {
    filteredData = filteredData.map((d) => {
      d[displayCol] = 1 - d[displayCol];
      if (d[displayCol] < 0) {
        d[displayCol] = 0;
      }
      return d;
    });
  }

  // TODO: How do we want to handle communicating that not all trials have operating conditions?
  const moistureTrialIDs = filterTrialIDsByConditions(
    "Average % Moisture (In Field)",
    moistureFilter,
    operatingConditions,
    moistureFilterDict,
  );

  const temperatureTrialIDs = filterTrialIDsByConditions(
    "Average Temperature (F)",
    temperatureFilter,
    operatingConditions,
    temperatureFilterDict,
  );
  const trialDurationTrialIDs = filterTrialIDsByConditions(
    "Trial Duration",
    trialDurations,
    operatingConditions,
    trialDurationDict,
  );

  const combinedTrialIDs = getIntersectingTrialIDs(
    moistureTrialIDs,
    temperatureTrialIDs,
    trialDurationTrialIDs,
  );

  if (combinedTrialIDs.size === 0) {
    filteredData = [];
  } else {
    filteredData = filteredData.filter((d) =>
      combinedTrialIDs.has(d["Trial ID"]),
    );
  }

  // Not enough data - return empty object
  const dataThreshold = 1;
  if (filteredData.length < dataThreshold) {
    return {
      message:
        "There is not enough data for the selected options. Please select more options.",
    };
  }

  const uniqueTrialIDs = new Set(filteredData.map((d) => d["Trial ID"]));
  const numTrials = uniqueTrialIDs.size;

  const grouped = d3.groups(filteredData, (d) => d[aggCol]);

  const sortedGrouped = grouped.map(([key, values]) => {
    // TODO: Verify that this is always the same
    const classIName = values[0]["Material Class I"];
    const quartiles = calculateQuartiles(values, displayCol);

    return {
      aggCol: key,
      count: values.length,
      "Material Class I": classIName,
      ...quartiles,
    };
  });

  sortedGrouped.sort((a, b) => {
    const colorOrder = ordinalSort(
      materialClassIOrderMap,
      a["Material Class I"],
      b["Material Class I"],
    );
    if (colorOrder !== 0) return colorOrder;
    return a.aggCol.localeCompare(b.aggCol, undefined, {
      numeric: true,
      sensitivity: "base",
    });
  });

  // console.log("sortedGrouped", sortedGrouped);

  return {
    data: sortedGrouped,
    numTrials: numTrials,
  };
};

export const getUniqueValues = async (columns, useTestData = false) => {
  let { trialData: data } = await loadData(useTestData);
  const uniqueValues = {};
  columns.forEach((column) => {
    const values = [...new Set(data.map((item) => item[column]))];
    const orderMap = ordinalOrders[column];
    if (orderMap) {
      values.sort((a, b) => ordinalSort(orderMap, a, b));
    } else {
      values.sort((a, b) => {
        const aStartsWithPos = a.startsWith("Pos");
        const bStartsWithPos = b.startsWith("Pos");
        if (aStartsWithPos && !bStartsWithPos) return 1;
        if (bStartsWithPos && !aStartsWithPos) return -1;
        return a.localeCompare(b, undefined, {
          numeric: true,
          sensitivity: "base",
        });
      });
    }
    uniqueValues[column] = values;
  });
  return uniqueValues;
};
