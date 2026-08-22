local ADDON_NAME = ...

TalentFetchDB = TalentFetchDB or {}
TalentFetchDB.selected = TalentFetchDB.selected or {}

local TF = {}
_G.TalentFetch = TF

function TF:GetPlayerSpec()
    local specIndex = GetSpecialization()
    if not specIndex then return nil end

    local specID, specName, _, specIcon, role, classFile = GetSpecializationInfo(specIndex)
    local _, playerClassFile = UnitClassBase("player")

    return {
        specID = specID,
        specName = specName,
        specIcon = specIcon,
        role = role,
        classFile = classFile or playerClassFile,
    }
end

function TF:GetBuildsForCurrentSpec()
    local spec = self:GetPlayerSpec()
    if not spec or not TalentFetchBuildData then return {}, spec end

    local result = {}
    for _, build in ipairs(TalentFetchBuildData.builds or {}) do
        if tonumber(build.specID) == tonumber(spec.specID) then
            result[#result + 1] = build
        end
    end

    table.sort(result, function(a, b)
        return (a.priority or 999) < (b.priority or 999)
    end)

    return result, spec
end

function TF:Print(msg)
    DEFAULT_CHAT_FRAME:AddMessage("|cff9b59ffTalentFetch|r " .. tostring(msg))
end

local function OnEvent(self, event, ...)
    if event == "PLAYER_LOGIN" then
        TF:Print("loaded. Type |cffFFFFFF/tf|r to open builds.")
    elseif event == "PLAYER_SPECIALIZATION_CHANGED" then
        if TF.UI and TF.UI:IsShown() then TF.UI:Refresh() end
    end
end

local frame = CreateFrame("Frame")
frame:RegisterEvent("PLAYER_LOGIN")
frame:RegisterEvent("PLAYER_SPECIALIZATION_CHANGED")
frame:SetScript("OnEvent", OnEvent)

SLASH_TALENTFETCH1 = "/tf"
SlashCmdList.TALENTFETCH = function()
    if TF.UI then
        TF.UI:SetShown(not TF.UI:IsShown())
    end
end
