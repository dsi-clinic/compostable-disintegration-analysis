"use client";
import { useEffect, useState, useMemo } from "react";
import Plot from "react-plotly.js";

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
  const plotData = useMemo(() => {
    return _plotData.filter((d) => selectedTrials?.length ? selectedTrials.includes(d.name) : true);
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
          (d) => d["Operating Condition"] === selectedColumn
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
              row[col] !== ""
          );
        });

        let timeSteps = filteredData.map((d) => d["Time Step"]);
        if (selectedMetric !== "Temperature") {
          timeSteps = timeSteps.map((d) => d * 7); // Convert weeks to days
        }

        const maxDaysFromData = Math.max(...timeSteps);
        const calculatedEffectiveMaxDays = capAt90Days
          ? Math.min(90, maxDaysFromData)
          : ignoreMaxDays
          ? maxDaysFromData + 5
          : Math.min(maxDays, maxDaysFromData);

        setEffectiveMaxDays(calculatedEffectiveMaxDays); // Update state

        const trialColumns = Object.keys(data[0]).filter(
          (column) => !nonTrialColumns.includes(column)
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
                value === null
                  ? null
                  : Math.round(value * 100 * 100) / 100
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
                  : "Day %{x}<br>%{y:.2f}%<extra>%{fullData.name}</extra>",
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

  const yMax = selectedMetric === "Temperature" ? 200 : 100;

  const xTickAngle = plotData.length > 6 ? 90 : 0;

  return (
    <>
      {errorMessage ? (
        <div className="flex items-center justify-center h-full mx-[200px]">
          <p>{errorMessage}</p>
        </div>
      ) : (
        <>
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
                range: [0, yMax],
                tickformat: selectedMetric === "Temperature" ? undefined : ".2f",
                ticksuffix: selectedMetric === "Temperature" ? "" : "%",
                showline: true,
              },
              xaxis: {
                title: {
                  text: "<b>Days</b>",
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
          <div className="flex flex-wrap justify-center my-4 gap-4">
            <div className="w-1/3 flex justify-center">
              <select
                className="select select-bordered"
                value={selectedMetric}
                onChange={(e) => setSelectedMetric(e.target.value)}
              >
                {metrics.map((metric) => (
                  <option key={metric} value={metric}>
                    {metric}
                  </option>
                ))}
              </select>
            </div>
            <div className="w-1/3 flex justify-center">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={!ignoreMaxDays}
                  onChange={(e) => setIgnoreMaxDays(!e.target.checked)}
                />
                <span className="ml-2">Cap at 45 Days</span>
              </label>
            </div>
            <div className="w-1/3 flex justify-center">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={!applyMovingAverage}
                  onChange={(e) => setApplyMovingAverage(!e.target.checked)}
                />
                <span className="ml-2">
                  Display Raw Data (No Moving Average)
                </span>
              </label>
            </div>
            <div className="w-1/3 flex justify-center">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={capAt90Days}
                  onChange={(e) => setCapAt90Days(e.target.checked)}
                />
                <span className="ml-2">Cap at 90 Days</span>
              </label>
            </div>
          </div>
          {availableTrials.length > 0 && (
            <div className="flex flex-col items-center my-2">
              <span className="mb-1 text-sm font-semibold">
                Show Trials
              </span>
              <div className="flex flex-wrap justify-center gap-2 max-h-32 overflow-y-auto px-2">
                {availableTrials.map((trial) => (
                  <label
                    key={trial}
                    className="flex items-center text-xs border rounded px-2 py-1"
                  >
                    <input
                      type="checkbox"
                      className="mr-1"
                      checked={
                        selectedTrials.length === 0 ||
                        selectedTrials.includes(trial)
                      }
                      onChange={(e) => {
                        setSelectedTrials((prev) => {
                          if (!prev.length) {
                            return availableTrials.filter((t) => t !== trial);
                          } else {
                            return availableTrials.filter((t) => {
                              if (prev.includes(t) && t !== trial) {
                                return true;
                              } else if (!prev.includes(t) && t === trial) {
                                return true;
                              } else {
                                return false;
                              }
                            })
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
        </>
      )}
    </>
  );
}
