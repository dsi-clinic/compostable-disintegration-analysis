import path from "path";
import { fetchCloudData, fetchLocalData } from "@/lib/serverUtils";

export const dataSource = process.env.DATA_SOURCE || "local";
export const bucketName = "cftp_data";

export const getFileNames = (useTestData = false) => {
  return {
    trialsFilename: `disintegration_data_all${process.env.DATA_VERSION_ID || ""}${
      useTestData ? "_test" : ""
    }.csv`,
    operatingConditionsFilename: `operating_conditions_avg${
      process.env.DATA_VERSION_ID || ""
    }${useTestData ? "_test" : ""}.csv`,
    operatingConditionsFullFilename: `operating_conditions_full${
      process.env.DATA_VERSION_ID || ""
    }${useTestData ? "_test" : ""}.csv`,
  };
};

export const getLocalPaths = (useTestData = false) => {
  const {
    trialsFilename,
    operatingConditionsFilename,
    operatingConditionsFullFilename,
  } = getFileNames(useTestData);
  return {
    trialDataPath: path.join(process.cwd(), "data", trialsFilename),
    operatingConditionsPath: path.join(
      process.cwd(),
      "data",
      operatingConditionsFilename,
    ),
    operatingConditionsFullPath: path.join(
      process.cwd(),
      "data",
      operatingConditionsFullFilename,
    ),
  };
};

export const loadData = async (useTestData = false) => {
  let trialData;
  let operatingConditions;
  let operatingConditionsFull;

  if (dataSource === "local") {
    const { trialDataPath, operatingConditionsPath } =
      getLocalPaths(useTestData);
    trialData = await fetchLocalData(trialDataPath);
    operatingConditions = await fetchLocalData(operatingConditionsPath);
    operatingConditionsFull = await fetchLocalData(
      getLocalPaths(useTestData).operatingConditionsFullPath,
    );
  } else if (dataSource === "google") {
    const { trialsFilename, operatingConditionsFilename } =
      getFileNames(useTestData);
    trialData = await fetchCloudData(trialsFilename, bucketName);
    operatingConditions = await fetchCloudData(
      operatingConditionsFilename,
      bucketName,
    );
    operatingConditionsFull = await fetchCloudData(
      getFileNames(useTestData).operatingConditionsFullFilename,
      bucketName,
    );
  } else {
    throw new Error("Invalid data source specified");
  }
  return { trialData, operatingConditions, operatingConditionsFull };
};
