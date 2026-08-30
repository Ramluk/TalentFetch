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
        local importString = build.importString or ""
        local usableImport = #importString >= 20
            and #importString <= 140
            and not string.find(importString, "/", 1, true)
            and not string.find(importString, " ", 1, true)
        local buildSpecID = build.specID or build.specId
        local sameSpec = buildSpecID and tonumber(buildSpecID) == tonumber(spec.specID)
        local sameRegisteredSpec = build.class == spec.classSlug and build.spec == spec.specSlug
        if usableImport and (sameSpec or sameRegisteredSpec) then
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
    if event == "ADDON_LOADED" and ... == ADDON_NAME then
        TF:Print("loaded. Type |cffFFFFFF/tf|r to open builds.")
    elseif event == "PLAYER_LOGIN" then
        if C_AddOns and C_AddOns.LoadAddOn then
            C_AddOns.LoadAddOn("Blizzard_PlayerSpells")
        end
        TF:InstallTalentTabButton()
        if not TF.TalentTabButton then
            TF:Print("Talents button unavailable. Type |cffFFFFFF/tf|r to open builds.")
        end
    elseif event == "ADDON_LOADED" then
        local addonName = ...
        if addonName == "Blizzard_PlayerSpells" then
            TF:InstallTalentTabButton()
        end
    elseif event == "PLAYER_SPECIALIZATION_CHANGED" then
        if TF.UI and TF.UI:IsShown() then TF.UI:Refresh() end
    end
end

function TF:InstallTalentTabButton()
    if self.TalentTabButton or not PlayerSpellsFrame then return end

    local button = CreateFrame("Button", nil, PlayerSpellsFrame, "UIPanelButtonTemplate")
    button:SetSize(110, 24)
    button:SetPoint("TOPRIGHT", PlayerSpellsFrame, "TOPRIGHT", -48, -38)
    button:SetText("TalentFetch")
    button:SetScript("OnClick", function()
        self.UI:SetShown(not self.UI:IsShown())
    end)
    self.TalentTabButton = button
end

local frame = CreateFrame("Frame")
frame:RegisterEvent("PLAYER_LOGIN")
frame:RegisterEvent("PLAYER_SPECIALIZATION_CHANGED")
frame:RegisterEvent("ADDON_LOADED")
frame:SetScript("OnEvent", OnEvent)

SLASH_TALENTFETCH1 = "/tf"
SlashCmdList.TALENTFETCH = function()
    if TF.UI then
        TF.UI:SetShown(not TF.UI:IsShown())
    else
        TF:Print("UI failed to load. Enable TalentFetch in the AddOns menu and reload.")
    end
end

SLASH_TALENTFETCHDEBUG1 = "/tfdebug"
SlashCmdList.TALENTFETCHDEBUG = function()
    local spec = TF:GetPlayerSpec()
    local builds = TF:GetBuildsForCurrentSpec()
    local total = TalentFetchBuildData and #(TalentFetchBuildData.builds or {}) or 0
    TF:Print(string.format(
        "spec=%s (%s), matching builds=%d, packaged builds=%d, data=%s",
        spec and spec.specName or "unknown",
        spec and spec.classSlug or "unknown",
        #builds,
        total,
        TalentFetchBuildData and TalentFetchBuildData.generatedAt or "missing"
    ))
end
