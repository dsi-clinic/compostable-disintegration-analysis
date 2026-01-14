"use client";
import { display2col, material2col, residuals2col } from "@/lib/constants";
import state from "@/lib/state";
import { InformationCircleIcon } from "@heroicons/react/24/solid";
import { useSnapshot } from "valtio";
import RadioSingleSelect from "./RadioSingleSelect";

export default function DashboardDisplayControls() {
  const snap = useSnapshot(state);

  return (
    <div className="flex flex-col">
      <div className="flex justify-center mb-4">
        <h2>Display Options</h2>
      </div>
      <RadioSingleSelect
        options={{ "Mesh Bag": "Mesh Bag", "Bulk Dose": "Bulk Dose" }}
        title="Select Test Method"
        filterKey="testMethod"
        infoText="Choose to see results from either of the two methods for field testing: the mesh bag method, where items are contained in a bag, or bulk dose, where items are loosely loaded into a pile. Results from these two methods are shown separately."
      />
      <RadioSingleSelect
        options={display2col}
        title="Show Results by Mass or by Surface Area"
        filterKey="displayCol"
        infoText="Field testing results can be based on the change in weight of a product, or the surface area before and after testing. The results by mass provided here are a combination of wet and dry weights. Future versions of the dashboard will further divide these data sets."
      />
      <RadioSingleSelect
        options={{ Final: "Final", Midpoint: "Midpoint" }}
        title="Select Point of Analysis"
        filterKey="timepoint"
        infoText="Some trials analyzed residuals at a midpoint, around 45 days, before the full composting cycle is complete. Select ‘midpoint’ to view this subset of the data."
      />
      <RadioSingleSelect
        options={material2col}
        title="Select X-Axis Display"
        filterKey="aggCol"
        infoText="Change the categories the data is grouped by on the X-axis."
      />
      <RadioSingleSelect
        options={residuals2col}
        title="Show by % Residuals Remaining or % Disintegrated"
        filterKey="displayResiduals"
        infoText="Disintegration data can be shown either of these two ways. % Residuals remaining is the inverse of % disintegrated."
      />
      <div>
        <input
          type="checkbox"
          id="capResults"
          className="mr-2"
          checked={snap.filters.uncapResults}
          onChange={() =>
            state.setFilterValue("uncapResults", !snap.filters.uncapResults)
          }
        />
        <label htmlFor="capResults" className="text-sm">
          Show results with over 100% residuals remaining
        </label>
        <div
          className="tooltip tooltip-primary tooltip-bottom ml-2 inline-flex"
          data-tip="The dashboard automatically caps results at 100% residuals. Click
            this checkbox to see uncapped data."
        >
          <span className="cursor-pointer text-primary">
            <InformationCircleIcon className="h-5 w-5 text-primary" />
          </span>
        </div>
      </div>
    </div>
  );
}
