local TF = TalentFetch

local Import = {}
TF.Import = Import

local function LoadBlizzardTalentUI()
    if C_AddOns and C_AddOns.LoadAddOn then
        pcall(C_AddOns.LoadAddOn, "Blizzard_PlayerSpells")
    elseif UIParentLoadAddOn then
        pcall(UIParentLoadAddOn, "Blizzard_PlayerSpells")
    end
end

local function GetImportDialog()
    LoadBlizzardTalentUI()

    if not ClassTalentLoadoutImportDialog and UIParentLoadAddOn then
        pcall(UIParentLoadAddOn, "Blizzard_PlayerSpells")
    end

    return ClassTalentLoadoutImportDialog
end

function Import:OpenImportDialog(importString, loadoutName)
    if type(importString) ~= "string" or importString == "" then
        return false, "This build does not have a Blizzard import string yet."
    end

    if InCombatLockdown() then
        return false, "Talent builds cannot be imported while in combat."
    end

    local dialog = GetImportDialog()
    if not dialog or not dialog.ShowDialog then
        return false, "Blizzard's talent import dialog is unavailable. Open the Talents window first."
    end

    dialog:ShowDialog()

    local importBox = dialog.ImportControl
        and dialog.ImportControl.InputContainer
        and dialog.ImportControl.InputContainer.EditBox
    local nameBox = dialog.NameControl and dialog.NameControl.EditBox

    if not importBox then
        return false, "Could not find Blizzard's talent import field."
    end

    importBox:SetText(importString)
    if nameBox and loadoutName then
        nameBox:SetText(loadoutName)
    end

    return true
end

function Import:OpenBuild(build)
    if not build then
        TF:Print("No build selected.")
        return
    end

    local ok, err = self:OpenImportDialog(build.importString, build.name)
    if not ok then
        TF:Print("|cffff5555Import unavailable:|r " .. tostring(err))
        return
    end

    TF:Print("Loaded |cffFFFFFF" .. tostring(build.name) .. "|r into Blizzard's import dialog. Review and apply it there.")
end
