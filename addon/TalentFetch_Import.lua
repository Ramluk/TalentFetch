local TF = TalentFetch

local Import = {}
TF.Import = Import

local function LoadBlizzardTalentUI()
    if C_AddOns and C_AddOns.LoadAddOn then
        C_AddOns.LoadAddOn("Blizzard_PlayerSpells")
        C_AddOns.LoadAddOn("Blizzard_ClassTalentUI")
    end
end

function Import:ImportString(importString, loadoutName)
    if type(importString) ~= "string" or importString == "" then
        return false, "Missing talent import string."
    end

    LoadBlizzardTalentUI()

    if ClassTalentImportExportMixin and ClassTalentImportExportMixin.ImportLoadout then
        local ok, result = ClassTalentImportExportMixin:ImportLoadout(importString, loadoutName)
        if ok then
            if ClassTalentLoadoutImportDialog then
                ClassTalentLoadoutImportDialog:Show()
            end
            return true, result
        end
        return false, result
    end

    return false, "Blizzard talent import API is unavailable."
end

function Import:OpenBuild(build)
    if not build or not build.importString then
        TF:Print("Build has no import string.")
        return
    end

    local ok, result = self:ImportString(build.importString, build.name)
    if not ok then
        TF:Print("Import failed: " .. tostring(result))
        return
    end

    TF:Print("Prepared |cffFFFFFF" .. tostring(build.name) .. "|r. Review it in Blizzard's import dialog and apply it there.")
end
