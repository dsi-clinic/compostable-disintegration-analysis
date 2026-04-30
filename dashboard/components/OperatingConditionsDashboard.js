"use client";
import { useEffect, useState, useMemo } from "react";
import Plot from "react-plotly.js";

const DEFAULT_RANGES = {
  Temperature: { min: 100, max: 215 },
  "% Moisture in Field": { min: 25, max: 75 },
  "% Oxygen, in Field": { min: 0, max: 25 },
};

export default function OperatingConditionsDashboard({
  maxDays = 45,
  windowSize = 10,
}) {
  // Add windowSize as a prop
  const [dataLoaded, setDataLoaded] = useState(false);
  const [_plotData, setPlotData] = useState([]);
  const [errorMessage, setErrorMessage] = useState("");
  const [selectedMetric, setSelectedMetric] = useState("Temperature");
  const [ignoreMaxDays, setIgnoreMaxDays] = useState(false);
  const [applyMovingAverage, setApplyMovingAverage] = useState(true);
  const [capAt90Days, setCapAt90Days] = useState(false);
  const [availableTrials, setAvailableTrials] = useState([]);
  const [selectedTrials, setSelectedTrials] = useState([]);
  const [yAxisRanges, setYAxisRanges] = useState(DEFAULT_RANGES);
  const plotData = useMemo(() => {
    return _plotData.filter((d) =>
      selectedTrials?.length
        ? selectedTrials.includes(d.name) || d.name === "PFRP"
        : true,
    );
  }, [_plotData, selectedTrials]);

  const metrics = ["Temperature", "% Moisture in Field", "% Oxygen, in Field"];

  const [effectiveMaxDays, setEffectiveMaxDays] = useState(maxDays);

  useEffect(() => {
    fetch("/api/operating-conditions", {
      headers: {
        "use-test-data": window.location.pathname.includes("test"),
      },
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to fetch operating conditions from API");
        }
        return response.json();
      })
      .then((data) => {
        const formattedData = [];
        const selectedColumn =
          selectedMetric === "Temperature"
            ? "Temperature"
            : selectedMetric === "% Moisture in Field"
              ? "Moisture"
              : selectedMetric === "% Oxygen, in Field"
                ? "Oxygen"
                : null;

        let filteredData = data.filter(
          (d) => d["Operating Condition"] === selectedColumn,
        );

        const nonTrialColumns = [
          "Time Step",
          "Operating Condition",
          "Time Unit",
        ];

        filteredData = filteredData.filter((row) => {
          // Check if all trial columns are empty (null, undefined, or empty string)
          return Object.keys(row).some(
            (col) =>
              !nonTrialColumns.includes(col) &&
              row[col] !== null &&
              row[col] !== undefined &&
              row[col] !== "",
          );
        });

        const isTemperature = selectedMetric === "Temperature";
        const timeSteps = filteredData.map((d) => d["Time Step"]);

        // Day-based caps need to be expressed in the chart's native unit
        // (days for Temperature, weeks otherwise) so gridlines align with data.
        const unitsPerDay = isTemperature ? 1 : 1 / 7;
        const maxFromData = Math.max(...timeSteps);
        const calculatedEffectiveMax = capAt90Days
          ? Math.min(90 * unitsPerDay, maxFromData)
          : ignoreMaxDays
            ? maxFromData + (isTemperature ? 5 : 1)
            : Math.min(maxDays * unitsPerDay, maxFromData);

        setEffectiveMaxDays(calculatedEffectiveMax);

        const trialColumns = Object.keys(data[0]).filter(
          (column) => !nonTrialColumns.includes(column),
        );

        if (availableTrials.length === 0) {
          setAvailableTrials(trialColumns);
        }
        const activeTrials =
          selectedTrials.length > 0 ? selectedTrials : trialColumns;

        trialColumns.forEach((column) => {
          if (!activeTrials.includes(column)) {
            return;
          }
          if (!nonTrialColumns.includes(column)) {
            let yData = filteredData.map((d) => parseFloat(d[column]) || null);
            yData = interpolateData(yData);
            if (selectedMetric !== "Temperature") {
              windowSize = 3; // Reduce window size for non-temperature metrics
            }
            if (applyMovingAverage) {
              yData = movingAverage(yData, windowSize);
            }

            if (selectedMetric !== "Temperature") {
              yData = yData.map((value) =>
                value === null ? null : Math.round(value * 100 * 100) / 100,
              );
            }

            formattedData.push({
              x: timeSteps,
              y: yData,
              mode: "lines+markers",
              name: column,
              hovertemplate:
                selectedMetric === "Temperature"
                  ? "Day %{x}<br>%{y:.2f}<extra>%{fullData.name}</extra>"
                  : "Week %{x}<br>%{y:.2f}%<extra>%{fullData.name}</extra>",
            });
          }
        });

        if (selectedMetric === "Temperature") {
          formattedData.push({
            x: [0, 45],
            y: [131, 131],
            mode: "lines",
            name: "PFRP",
            line: {
              dash: "dot",
              color: "red",
              width: 2,
            },
          });
        }

        formattedData.sort((a, b) => a.name.localeCompare(b.name));
        setPlotData(formattedData);
        setDataLoaded(true);
      })
      .catch((error) => {
        console.error("Error loading CSV data:", error);
        setErrorMessage("Failed to load data.");
      });
  }, [
    windowSize,
    selectedMetric,
    ignoreMaxDays,
    applyMovingAverage,
    capAt90Days,
    selectedTrials,
  ]);

  function interpolateData(yData) {
    let lastValidIndex = null;

    for (let i = 0; i < yData.length; i++) {
      if (yData[i] === null) {
        // Find the next valid index
        const nextValidIndex = yData.slice(i).findIndex((v) => v !== null) + i;

        if (lastValidIndex !== null && nextValidIndex < yData.length) {
          // Interpolate between the last valid and next valid index
          const slope =
            (yData[nextValidIndex] - yData[lastValidIndex]) /
            (nextValidIndex - lastValidIndex);
          yData[i] = yData[lastValidIndex] + slope * (i - lastValidIndex);
        }
      } else {
        lastValidIndex = i;
      }
    }

    return yData;
  }

  function movingAverage(data, windowSize) {
    return data.map((value, idx, arr) => {
      // Ignore null values
      if (value === null) return null;

      const start = Math.max(0, idx - Math.floor(windowSize / 2));
      const end = Math.min(arr.length, idx + Math.ceil(windowSize / 2));
      const window = arr.slice(start, end);
      const validNumbers = window.filter((n) => n !== null);

      if (validNumbers.length === 0) return null;

      const sum = validNumbers.reduce((acc, num) => acc + num, 0);
      return sum / validNumbers.length;
    });
  }

  const yAxisTitle = `${selectedMetric}`;

  const title = `${selectedMetric} Over Time`;

  const currentRange = yAxisRanges[selectedMetric];

  const xTickAngle = plotData.length > 6 ? 90 : 0;

  return (
    <>
      {errorMessage ? (
        <div className="flex items-center justify-center h-full mx-[200px]">
          <p>{errorMessage}</p>
        </div>
      ) : (
        <div className="flex flex-col items-center">
          <div className="relative">
            <Plot
              data={plotData}
              layout={{
                width: 1280,
                height: 600,
                title: {
                  text: `<b>${title}</b>`,
                  x: 0.5,
                  xanchor: "center",
                  yanchor: "top",
                },
                showlegend: true,
                yaxis: {
                  title: {
                    text: `<b>${yAxisTitle}</b>`,
                  },
                  range: [currentRange.min, currentRange.max],
                  tickformat:
                    selectedMetric === "Temperature" ? undefined : ".2f",
                  ticksuffix: selectedMetric === "Temperature" ? "" : "%",
                  showline: true,
                },
                xaxis: {
                  title: {
                    text: `<b>${selectedMetric === "Temperature" ? "Days" : "Weeks"}</b>`,
                  },
                  tickangle: xTickAngle,
                  ticklen: 10,
                  automargin: true,
                  range: [0, effectiveMaxDays],
                  showline: true,
                },
                hovermode: "x",
              }}
              config={{
                displayModeBar: false,
              }}
            />
          </div>
          <div className="my-4 flex w-full justify-center">
            <div className="flex w-full max-w-5xl items-start justify-evenly gap-6 px-4">
              {availableTrials.length > 0 && (
                <div className="flex flex-col">
                  <span className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Show Trials
                  </span>
                  <div className="flex max-h-56 flex-col gap-1 overflow-y-auto pr-2">
                    {availableTrials.map((trial) => (
                      <label
                        key={trial}
                        className="flex items-center rounded px-1 py-0.5 text-xs"
                      >
                        <input
                          type="checkbox"
                          className="checkbox checkbox-primary checkbox-xs mr-1"
                          checked={
                            selectedTrials.length === 0 ||
                            selectedTrials.includes(trial)
                          }
                          onChange={(e) => {
                            setSelectedTrials((prev) => {
                              if (!prev.length) {
                                return availableTrials.filter(
                                  (t) => t !== trial,
                                );
                              } else {
                                return availableTrials.filter((t) => {
                                  if (prev.includes(t) && t !== trial) {
                                    return true;
                                  } else if (!prev.includes(t) && t === trial) {
                                    return true;
                                  } else {
                                    return false;
                                  }
                                });
                              }
                            });
                          }}
                        />
                        <span>{trial}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}
              <div className="flex flex-col">
                <span className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Metric
                </span>
                <select
                  className="select select-bordered w-full max-w-xs"
                  value={selectedMetric}
                  onChange={(e) => setSelectedMetric(e.target.value)}
                >
                  {metrics.map((metric) => (
                    <option key={metric} value={metric}>
                      {metric}
                    </option>
                  ))}
                </select>
                <span className="mb-1 mt-3 text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Y-Axis Range ({selectedMetric === "Temperature" ? "°F" : "%"})
                </span>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    className="input input-bordered input-sm w-20"
                    value={currentRange.min}
                    onChange={(e) => {
                      const val = parseFloat(e.target.value);
                      if (!isNaN(val)) {
                        setYAxisRanges((prev) => ({
                          ...prev,
                          [selectedMetric]: {
                            ...prev[selectedMetric],
                            min: val,
                          },
                        }));
                      }
                    }}
                  />
                  <span className="text-gray-400">—</span>
                  <input
                    type="number"
                    className="input input-bordered input-sm w-20"
                    value={currentRange.max}
                    onChange={(e) => {
                      const val = parseFloat(e.target.value);
                      if (!isNaN(val)) {
                        setYAxisRanges((prev) => ({
                          ...prev,
                          [selectedMetric]: {
                            ...prev[selectedMetric],
                            max: val,
                          },
                        }));
                      }
                    }}
                  />
                  <button
                    className="btn btn-ghost btn-xs"
                    title="Reset to default"
                    onClick={() =>
                      setYAxisRanges((prev) => ({
                        ...prev,
                        [selectedMetric]: DEFAULT_RANGES[selectedMetric],
                      }))
                    }
                  >
                    Reset
                  </button>
                </div>
                <label className="mt-3 flex cursor-pointer items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    className="toggle toggle-primary toggle-sm"
                    checked={!applyMovingAverage}
                    onChange={(e) => setApplyMovingAverage(!e.target.checked)}
                  />
                  <span>
                    Display Raw Data (No Moving Average)
                  </span>
                </label>
              </div>
              <div className="flex flex-col">
                <div className="flex flex-col gap-y-2">
                  <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                    Plot Duration
                  </h3>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      className="radio radio-primary"
                      name="durationRange"
                      checked={!ignoreMaxDays && !capAt90Days}
                      onChange={() => {
                        setIgnoreMaxDays(false);
                        setCapAt90Days(false);
                      }}
                    />
                    <span className="ml-2 text-sm">Cap at 45 Days</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      className="radio radio-primary"
                      name="durationRange"
                      checked={capAt90Days}
                      onChange={() => {
                        setCapAt90Days(true);
                        setIgnoreMaxDays(false);
                      }}
                    />
                    <span className="ml-2 text-sm">Cap at 90 Days</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      className="radio radio-primary"
                      name="durationRange"
                      checked={ignoreMaxDays}
                      onChange={() => {
                        setIgnoreMaxDays(true);
                        setCapAt90Days(false);
                      }}
                    />
                    <span className="ml-2 text-sm">Full Duration</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
