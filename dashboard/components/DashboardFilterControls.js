"use client";
import CheckboxMenu from "@/components/CheckboxMenu";
import { useSnapshot } from "valtio";
import state from "@/lib/state";
import {
  moistureFilterDict,
  temperatureFilterDict,
  trialDurationDict,
} from "@/lib/constants";
export default function DashboardFilterControls() {
  const snap = useSnapshot(state);

  return (
    <div className="flex flex-col">
      <div className="flex-1 mx-2 w-full min-h-[300px]">
        <h2 className="text-center"> Item Filters</h2>
        <div className="flex flex-col items-center lg:grid lg:grid-cols-4 gap-2">
          <CheckboxMenu
            options={snap.options["Material Class II"]}
            selectedOptions={snap.filters.selectedMaterialTypes}
            filterKey="selectedMaterialTypes"
            title="Generic Material"
            infoText="Select one or more options to filter the data by the generic type of material tested, e.g. compostable polymer or fiber."
          />
          <CheckboxMenu
            options={snap.options["Material Class III"]}
            selectedOptions={snap.filters.selectedSpecificMaterialTypes}
            filterKey="selectedSpecificMaterialTypes"
            title="Specific Material"
            infoText="Select one or more options to filter the data by the specific type of material tested, e.g. PLA or PHA, tree fiber or sugarcane fiber (bagasse)."
          />
          <CheckboxMenu
            options={snap.options["Item Format"]}
            selectedOptions={snap.filters.selectedFormats}
            filterKey="selectedFormats"
            title="Item Type"
            infoText="Select one or more options to filter the data by the type of item tested."
          />
          <CheckboxMenu
            options={snap.options["Item Brand"]}
            selectedOptions={snap.filters.selectedBrands}
            filterKey="selectedBrands"
            title="Item Brand"
            infoText="Select one or more options to filter the data by the brands whose items were tested."
          />
        </div>
        <h2 className="text-center"> Operations Filters</h2>
        <div className="flex flex-col lg:grid lg:grid-cols-4 gap-2">
          <CheckboxMenu
            options={snap.options["Technology"]}
            selectedOptions={snap.filters.selectedTechnologies}
            filterKey="selectedTechnologies"
            title="Composting Method"
            infoText="Select one or more options to filter the data by the primary composting method used by the facility conducting the field test. Note that 'Aerated Static Pile' includes versions that are covered or extended."
            showInfoIcon={false}
          />
          <CheckboxMenu
            options={Object.keys(temperatureFilterDict)}
            selectedOptions={snap.filters.selectedTemperatureLevels}
            filterKey="selectedTemperatureLevels"
            title="Mean Temperature"
            infoText="Select one or more options to filter the data by the average Temperature from the first 45 days of the trial. Note that most temperature measurements are taken in the area surrounding the items being tested."
          />
          <CheckboxMenu
            options={Object.keys(moistureFilterDict)}
            selectedOptions={snap.filters.selectedMoistureLevels}
            filterKey="selectedMoistureLevels"
            title="Mean % Moisture"
            infoText="Select one or more options to filter the data by the average % moisture. Note that moisture measurements are taken from material in the area surrounding the items being tested."
          />
          <CheckboxMenu
            options={Object.keys(trialDurationDict)}
            selectedOptions={snap.filters.selectedTrialDurations}
            filterKey="selectedTrialDurations"
            title="Trial Duration"
            infoText="Select one or more options to filter the data by the duration of the field test."
            disabled={snap.filters.timepoint !== 'Final'}
          />
        </div>
      </div>
    </div>
  );
}
