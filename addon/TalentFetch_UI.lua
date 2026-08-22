local TF = TalentFetch

local UI = CreateFrame("Frame", "TalentFetchFrame", UIParent, "BackdropTemplate")
TF.UI = UI

UI:SetSize(430, 430)
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
content:SetSize(380, 1)
scroll:SetScrollChild(content)
UI.content = content

local rows = {}

local function GetRow(index)
    local row = rows[index]
    if row then return row end

    row = CreateFrame("Frame", nil, content)
    row:SetSize(375, 68)

    row.name = row:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
    row.name:SetPoint("TOPLEFT", 8, -7)

    row.meta = row:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
    row.meta:SetPoint("TOPLEFT", row.name, "BOTTOMLEFT", 0, -5)

    row.import = CreateFrame("Button", nil, row, "UIPanelButtonTemplate")
    row.import:SetSize(72, 24)
    row.import:SetPoint("TOPRIGHT", -5, -8)
    row.import:SetText("Import")

    rows[index] = row
    return row
end

function UI:Refresh()
    local builds, spec = TF:GetBuildsForCurrentSpec()
    subtitle:SetText(spec and (spec.specName .. "  •  Wowhead") or "Unable to determine specialization")

    for _, row in ipairs(rows) do row:Hide() end

    local y = 0
    for index, build in ipairs(builds) do
        local row = GetRow(index)
        row:SetPoint("TOPLEFT", 0, -y)
        row.name:SetText(build.name or "Unnamed build")

        local updated = build.updatedAt and date("%Y-%m-%d %H:%M", build.updatedAt) or "unknown"
        row.meta:SetText((build.heroSpec or "") .. "  •  " .. (build.content or "") .. "  •  Updated " .. updated)
        row.import:SetScript("OnClick", function() TF.Import:OpenBuild(build) end)
        row:Show()
        y = y + 72
    end

    content:SetHeight(math.max(1, y))
end

UI:SetScript("OnShow", function(self) self:Refresh() end)
