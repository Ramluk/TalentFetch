local ADDON_NAME = ...

TalentFetchDB = TalentFetchDB or {}
TalentFetchDB.selected = TalentFetchDB.selected or {}

local TF = {}
_G.TalentFetch = TF

local CLASS_SLUGS = {
    DEATHKNIGHT = "death-knight",
    DEMONHUNTER = "demon-hunter",
}

local function Slugify(text)
    text = tostring(text or ""):lower()
    text = text:gsub("[^%w]+", "-")
    text = text:gsub("^-+", ""):gsub("-+$", "")
    return text
end

function TF:GetPlayerSpec()
    local specIndex = GetSpecialization()
    if not specIndex then return nil end

    local specID, specName, _, specIcon, role, classFile = GetSpecializationInfo(specIndex)
    local _, playerClassFile = UnitClassBase("player")

    return {
        specID = specID,
        specName = specName,
        specSlug = Slugify(specName),
        specIcon = specIcon,
        role = role,
        classFile = classFile or playerClassFile,
        classSlug = CLASS_SLUGS[classFile or playerClassFile] or Slugify(classFile or playerClassFile),
    }
end

function TF:GetBuildsForCurrentSpec()
    local spec = self:GetPlayerSpec()
    if not spec or not TalentFetchBuildData then return {}, spec end

    local result = {}
    for _, build in ipairs(TalentFetchBuildData.builds or {}) do
        local sameSpec = build.specID and tonumber(build.specID) == tonumber(spec.specID)
        local sameRegisteredSpec = build.class == spec.classSlug and build.spec == spec.specSlug
        if sameSpec or sameRegisteredSpec then
            result[#result + 1] = build
        end
    end

    table.sort(result, function(a, b)
        local aPriority = a.priority or (a.recommended and 10 or 100)
        local bPriority = b.priority or (b.recommended and 10 or 100)
        if aPriority ~= bPriority then
            return aPriority < bPriority
        end
        return tostring(a.name or "") < tostring(b.name or "")
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
