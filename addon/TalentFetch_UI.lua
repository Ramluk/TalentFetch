local TF = TalentFetch

local UI = CreateFrame("Frame", "TalentFetchFrame", UIParent, "BackdropTemplate")
TF.UI = UI

UI:SetSize(500, 520)
UI:SetPoint("CENTER")
UI:SetMovable(true)
UI:EnableMouse(true)
UI:RegisterForDrag("LeftButton")
UI:SetScript("OnDragStart", UI.StartMoving)
UI:SetScript("OnDragStop", UI.StopMovingOrSizing)
UI:SetBackdrop({
    bgFile = "Interface/Tooltips/UI-Tooltip-Background",
    edgeFile = "Interface/Tooltips/UI-Tooltip-Border",
    tile = true,
    tileSize = 16,
    edgeSize = 12,
    insets = { left = 3, right = 3, top = 3, bottom = 3 },
})
UI:Hide()

local title = UI:CreateFontString(nil, "OVERLAY", "GameFontHighlightLarge")
title:SetPoint("TOPLEFT", 18, -16)
title:SetText("TalentFetch")

local subtitle = UI:CreateFontString(nil, "OVERLAY", "GameFontNormal")
subtitle:SetPoint("TOPLEFT", title, "BOTTOMLEFT", 0, -8)

local close = CreateFrame("Button", nil, UI, "UIPanelCloseButton")
close:SetPoint("TOPRIGHT", -4, -4)

local refresh = CreateFrame("Button", nil, UI, "UIPanelButtonTemplate")
refresh:SetSize(90, 24)
refresh:SetPoint("BOTTOMRIGHT", -14, 12)
refresh:SetText("Refresh")
refresh:SetScript("OnClick", function() UI:Refresh() end)

local scroll = CreateFrame("ScrollFrame", nil, UI, "UIPanelScrollFrameTemplate")
scroll:SetPoint("TOPLEFT", 14, -72)
scroll:SetPoint("BOTTOMRIGHT", -30, 46)

local content = CreateFrame("Frame", nil, scroll)
content:SetSize(440, 1)
scroll:SetScrollChild(content)
UI.content = content

local rows = {}
local headers = {}

local CONTENT_ORDER = {
    { key = "mythic+", label = "Mythic+" },
    { key = "raid", label = "Raid" },
    { key = "delves", label = "Delves" },
    { key = "pvp", label = "PvP" },
    { key = "leveling", label = "Leveling" },
    { key = "unknown", label = "Other" },
}

local function GetRow(index)
    local row = rows[index]
    if row then return row end

    row = CreateFrame("Frame", nil, content)
    row:SetSize(435, 72)

    row.name = row:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
    row.name:SetPoint("TOPLEFT", 8, -7)
    row.name:SetWidth(300)
    row.name:SetJustifyH("LEFT")

    row.meta = row:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
    row.meta:SetPoint("TOPLEFT", row.name, "BOTTOMLEFT", 0, -5)
    row.meta:SetWidth(330)
    row.meta:SetJustifyH("LEFT")

    row.import = CreateFrame("Button", nil, row, "UIPanelButtonTemplate")
    row.import:SetSize(78, 24)
    row.import:SetPoint("TOPRIGHT", -5, -8)
    row.import:SetText("Import")

    rows[index] = row
    return row
end

local function GetHeader(index)
    local header = headers[index]
    if header then return header end

    header = content:CreateFontString(nil, "OVERLAY", "GameFontNormalLarge")
    header:SetSize(435, 26)
    headers[index] = header
    return header
end

local function FormatUpdated(build)
    if not build.updatedAt then
        return "Update time unavailable"
    end
    return "Updated " .. date("%Y-%m-%d %H:%M", build.updatedAt)
end

local function BuildGroups(builds)
    local groups = {}
    for _, entry in ipairs(CONTENT_ORDER) do
        groups[entry.key] = { label = entry.label, builds = {} }
    end

    for _, build in ipairs(builds) do
        local key = build.content or "unknown"
        local group = groups[key] or groups.unknown
        group.builds[#group.builds + 1] = build
    end

    return groups
end

function UI:Refresh()
    local builds, spec = TF:GetBuildsForCurrentSpec()
    subtitle:SetText(spec and (spec.specName .. "  •  Wowhead") or "Unable to determine specialization")

    for _, row in ipairs(rows) do row:Hide() end
    for _, header in ipairs(headers) do header:Hide() end

    local groups = BuildGroups(builds)
    local rowIndex, headerIndex = 0, 0
    local y = 0

    for _, entry in ipairs(CONTENT_ORDER) do
        local group = groups[entry.key]
        if group and #group.builds > 0 then
            headerIndex = headerIndex + 1
            local header = GetHeader(headerIndex)
            header:SetPoint("TOPLEFT", 8, -y)
            header:SetText(group.label)
            header:Show()
            y = y + 28

            for _, build in ipairs(group.builds) do
                rowIndex = rowIndex + 1
                local row = GetRow(rowIndex)
                row:SetPoint("TOPLEFT", 0, -y)
                row.name:SetText(build.name or "Unnamed build")

                local hero = build.heroSpec or "Hero spec unavailable"
                local status = build.importString and "Ready to import" or "Import data pending"
                row.meta:SetText(hero .. "  •  " .. FormatUpdated(build) .. "  •  " .. status)

                row.import:SetEnabled(type(build.importString) == "string" and build.importString ~= "")
                row.import:SetScript("OnClick", function() TF.Import:OpenBuild(build) end)
                row:Show()
                y = y + 76
            end
        end
    end

    if rowIndex == 0 then
        rowIndex = 1
        local row = GetRow(rowIndex)
        row:SetPoint("TOPLEFT", 0, -y)
        row.name:SetText("No Wowhead builds are available yet.")
        row.meta:SetText("Refresh data from the TalentFetch build service.")
        row.import:Hide()
        row:Show()
        y = y + 72
    else
        for i = 1, rowIndex do
            rows[i].import:Show()
        end
    end

    content:SetHeight(math.max(1, y))
end

UI:SetScript("OnShow", function(self) self:Refresh() end)
