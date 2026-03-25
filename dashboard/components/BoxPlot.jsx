"use client";
import React, { useMemo } from "react";
import { scaleBand, scaleLinear } from "@visx/scale";
import { Group } from "@visx/group";
import { Line, Bar } from "@visx/shape";
import { Text } from "@visx/text";
import { useTooltip } from "@visx/tooltip";
import { localPoint } from "@visx/event";
import { useParentSize } from "@visx/responsive";
import { AxisBottom, AxisLeft } from "@visx/axis";
import { format } from "d3-format";
import { Grid } from "@visx/grid";

const pctFormat = format(".0%");
export const BoxPlot = ({
  xAxisTitle,
  yAxisTitle,
  data,
  minWidth,
  minHeight,
}) => {
  const { parentRef, width, height } = useParentSize({ debounceTime: 150 });
  const margin = { top: 40, right: 20, bottom: 140, left: 80 };
  const xMax = width - margin.left - margin.right;
  const yMax = height - margin.top - margin.bottom;
  const xScale = scaleBand({
    domain: data.map((_, i) => i.toString()),
    range: [0, xMax],
    padding: 0.4,
  });

  const yScale = scaleLinear({
    domain: [0, Math.max(Math.max(...data.map((d) => d.max)), 1)],
    range: [yMax, 0],
  });

  const { tooltipData, tooltipLeft, tooltipTop, showTooltip, hideTooltip } =
    useTooltip();

  const handleMouseOver = (event, datum) => {
    const coords = localPoint(event.target.ownerSVGElement, event);
    const barWidth = xScale.bandwidth();
    showTooltip({
      tooltipData: datum,
      tooltipLeft:
        xScale(data.findIndex((d) => d === datum).toString()) +
        margin.left +
        barWidth / 2,
      tooltipTop: coords?.y,
    });
  };
  return (
    <div
      ref={parentRef}
      className="flex-grow"
      style={{ minHeight, minWidth, width: "100%", height: "100%" }}
    >
      <svg width={width} height={height}>
        <Group left={margin.left} top={margin.top}>
          <AxisBottom
            scale={xScale}
            top={yMax}
            tickFormat={(v) => `${data[v].aggCol} (${data[v].count})`}
            tickComponent={CustomTickLabel}
            tickLabelProps={() => ({
              fontSize: 12,
              textAnchor: data.length > 5 ? "end" : "middle",
              dy: data.length > 5 ? "-0.25em" : "0.75em",
              angle: data.length > 5 ? -90 : 0,
            })}
            numTicks={data.length}
            label={xAxisTitle}
          />
          <AxisLeft
            scale={yScale}
            tickFormat={pctFormat}
            numTicks={5}
            hideAxisLine
            hideTicks
            left={10}
            tickLabelProps={() => ({
              fontSize: 12,
              textAnchor: "end",
              dx: "-0.25em",
              dy: "0.25em",
            })}
            label={yAxisTitle}
            labelProps={{
              fontSize: 20,
              fontWeight: "bold",
              textAnchor: "middle",
              angle: -90,
              dx: "-1em",
            }}
          />
          <Grid
            yScale={yScale}
            numTicksRows={5}
            xScale={xScale}
            numTicksColumns={0}
            width={xMax}
            height={yMax}
            strokeWidth={1}
          />
          {data.map((d, i) => {
            const x = xScale(i.toString());
            const boxWidth = xScale.bandwidth();
            const medianY = yScale(d.median);
            const q1Y = yScale(d.q1);
            const q3Y = yScale(d.q3);
            const lowerFenceY = yScale(d.lowerfence);
            const upperFenceY = yScale(d.upperfence);
            const meanY = yScale(d.mean);

            return (
              <Group key={`boxplot-${i}`}>
                {/* Vertical whiskers */}
                <Line
                  from={{ x: x + boxWidth / 2, y: yScale(d.q1) }}
                  to={{ x: x + boxWidth / 2, y: lowerFenceY }}
                  stroke={d.color}
                  strokeWidth={3}
                />
                <Line
                  from={{ x: x + boxWidth / 2, y: Math.min(upperFenceY, yMax) }}
                  to={{ x: x + boxWidth / 2, y: yScale(d.q3) }}
                  stroke={d.color}
                  strokeWidth={3}
                />
                {/* T-lines */}
                <Line
                  from={{ x: x + boxWidth / 4, y: lowerFenceY }}
                  to={{ x: x + (boxWidth * 3) / 4, y: lowerFenceY }}
                  stroke={d.color}
                  strokeWidth={3}
                />
                <Line
                  id="upperfence-h"
                  from={{ x: x + boxWidth / 4, y: upperFenceY }}
                  to={{ x: x + (boxWidth * 3) / 4, y: upperFenceY }}
                  stroke={d.color}
                  strokeWidth={3}
                />
                <Bar
                  x={x}
                  y={q3Y}
                  width={boxWidth}
                  height={q1Y - q3Y}
                  fill={d.color}
                  fillOpacity={0.5}
                  stroke={d.color}
                  strokeWidth={4}
                />
                <Line
                  from={{ x, y: medianY }}
                  to={{ x: x + boxWidth, y: medianY }}
                  stroke={d.color}
                  strokeWidth={4}
                />
                {/* Mean dashed line */}
                <Line
                  from={{ x, y: meanY }}
                  to={{ x: x + boxWidth, y: meanY }}
                  stroke={d.color}
                  strokeDasharray="8,4"
                  strokeWidth={4}
                />
                <Bar
                  x={x}
                  y={0}
                  width={boxWidth}
                  height={yMax}
                  opacity={0}
                  onMouseOver={(e) => handleMouseOver(e, d)}
                  onMouseOut={hideTooltip}
                />
                {/* Outliers */}
                {d.outliers.map((outlier, j) => {
                  return (
                    <circle
                      key={`outlier-${i}-${j}`}
                      cx={x + boxWidth / 2}
                      cy={yScale(outlier)}
                      r={2}
                      opacity={0.5}
                      fill={d.color}
                    />
                  );
                })}
              </Group>
            );
          })}
        </Group>
        {tooltipData && (
          <CustomTooltip
            tooltipLeft={tooltipLeft}
            tooltipData={tooltipData}
            top={margin.top}
            yScale={yScale}
            height={height}
            width={width}
          />
        )}
      </svg>
    </div>
  );
};

const tooltipKeys = [
  "max",
  "upperfence",
  "q3",
  "mean",
  "median",
  "q1",
  "lowerfence",
  "min",
];
const CustomTickLabel = ({
  x,
  y,
  formattedValue,
  lineLength = 16,
  ...props
}) => {
  if (formattedValue.length > lineLength) {
    const words = formattedValue.split(" ");
    let lines = [""];
    let currentLine = 0;

    words.forEach((word) => {
      if ((lines[currentLine] + word).length > lineLength) {
        currentLine++;
        lines[currentLine] = "";
      }
      lines[currentLine] += (lines[currentLine] ? " " : "") + word;
    });
    const offset = -12 * ((lines.length - 1) / 2);

    return (
      <>
        {lines.map((line, i) => (
          <Text
            x={x + (props.angle === -90 ? offset + i * 12 : 0)}
            y={y + (props.angle !== -90 ? offset + i * 15 : 0)}
            {...props}
            key={i}
          >
            {line}
          </Text>
        ))}
      </>
    );
  } else {
    return (
      <Text x={x} y={y} {...props}>
        {formattedValue}
      </Text>
    );
  }
};

const CustomTooltip = ({
  tooltipLeft,
  tooltipData,
  top,
  height,
  width,
  yScale,
}) => {
  const mappedLabels = useMemo(() => {
    let countByValue = {};
    tooltipKeys.forEach((key) => {
      countByValue[tooltipData[key]] =
        (countByValue[tooltipData[key]] || 0) + 1;
    });
    let keyRanges = {};
    const sortedValues = Object.keys(countByValue).sort((a, b) => +b - +a);

    sortedValues.forEach((key, i) => {
      let y = yScale(key) - 10;
      // shift up and down 20 for each count
      let minY = y - (countByValue[key] / 2) * 20;
      let maxY = y + (countByValue[key] / 2) * 20;

      keyRanges[key] = {
        minY,
        y,
        maxY,
      };
    });
    let areColided = true;
    let index = 0;
    let runs = 0;
    while (areColided && runs < 100) {
      areColided = false;
      for (let i = 0; i < sortedValues.length; i++) {
        let key = sortedValues[i];
        let range = keyRanges[key];
        for (let j = i + 1; j < sortedValues.length; j++) {
          let key2 = sortedValues[j];
          let range2 = keyRanges[key2];
          if (range.minY < range2.maxY && range.maxY > range2.minY) {
            areColided = true;
            let shift = 10;
            keyRanges[key].minY -= shift;
            keyRanges[key].y -= shift;
            keyRanges[key].maxY -= shift;

            keyRanges[key2].minY += shift;
            keyRanges[key2].y += shift;
            keyRanges[key2].maxY += shift;
          }
        }
      }
      runs++;
    }

    return tooltipKeys.map((key) => {
      const value = tooltipData[key];
      countByValue[value] = countByValue[value] - 1;
      const yValue = yScale(value);
      const offset = countByValue[value] * 20;
      const displayValue = keyRanges[value].maxY - offset;
      return {
        yValue,
        value,
        displayValue,
        key,
      };
    });
  }, [tooltipData, yScale]);
  const orientation = tooltipLeft > width - 120 ? "left" : "right";
  const direction = orientation === "left" ? -1 : 1;
  return (
    <Group
      left={tooltipLeft}
      top={top}
      height={height}
      style={{ pointerEvents: "none" }}
    >
      {mappedLabels.map((entry) => (
        <React.Fragment key={entry.key}>
          <line
            x1={5 * direction}
            y1={entry.yValue}
            x2={20 * direction}
            y2={entry.displayValue}
            stroke={tooltipData.color}
            strokeDasharray="4,2"
          />
          <rect
            x={20 * direction + (direction === -1 ? -100 : 0)}
            y={entry.displayValue - 9}
            width={100}
            height={22}
            fill={"white"}
            stroke={tooltipData.color}
            strokeWidth={1}
          />
          {/* <text x={35} y={mappedYValues[key] + 5} fontSize={10} stroke="white" strokeWidth={2}>
            {`${key.charAt(0).toUpperCase() + key.slice(1)}: ${pctFormat(tooltipData[key])}`}
          </text> */}
          <text
            x={25 * direction + (direction === -1 ? -90 : 0)}
            y={entry.displayValue + 5}
            fontSize={10}
            fill="black"
            fontWeight={"bold"}
          >
            {`${
              entry.key.charAt(0).toUpperCase() + entry.key.slice(1)
            }: ${pctFormat(entry.value)}`}
          </text>
        </React.Fragment>
      ))}
    </Group>
  );
};

export default BoxPlot;
