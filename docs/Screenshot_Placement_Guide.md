# Screenshot Placement Guide for User Guide

This document provides exact instructions for where to place screenshots in the User Guide Word document and what to highlight in each screenshot.

---

## Screenshot 1: Home Page
**Location**: After "Accessing the Application" section, before "Understanding the System"

**What to capture**:
- Full browser window showing the home page
- URL bar showing `http://localhost:8000`

**What to highlight/annotate**:
1. **Red circle/arrow** pointing to: OffSight™ logo in top-left corner
2. **Red box** around: Navigation menu (Home, Changes, Sources, Run Pipeline)
3. **Yellow highlight** on: "What this system does" explanation box
4. **Green highlight** on: "End-to-end workflow" section with the 4 numbered steps

**Annotation text to add**:
- "Logo" near the logo
- "Navigation Menu" near the menu
- "System Overview" near the explanation box
- "Workflow Steps" near the numbered list

---

## Screenshot 2: Sources Page - Add Form
**Location**: In "Adding a New Source" section, after step 2

**What to capture**:
- The "Manage Sources" page
- The "Add New Source" form at the top (fully visible)

**What to highlight/annotate**:
1. **Red box** around: "Add New Source" heading
2. **Yellow highlight** on: Name input field
3. **Yellow highlight** on: URL input field
4. **Yellow highlight** on: Description textarea
5. **Green highlight** on: "Enabled" checkbox
6. **Blue highlight** on: Help text below checkbox ("✓ Checked: The scraper will monitor...")
7. **Red circle** around: "Add Source" button

**Annotation text to add**:
- "Required field" next to Name
- "Required field" next to URL
- "Optional" next to Description
- "Enable monitoring" next to checkbox

---

## Screenshot 3: Sources Page - Success Message
**Location**: In "Adding a New Source" section, after step 5

**What to capture**:
- The page after successfully adding a source
- Success message banner visible
- The new source in the table

**What to highlight/annotate**:
1. **Green box** around: Success message banner (e.g., "Source 'HSE Offshore Safety Regulations' created successfully")
2. **Red box** around: The new source row in the table
3. **Yellow highlight** on: Source ID column
4. **Yellow highlight** on: Source name
5. **Yellow highlight** on: URL (as clickable link)
6. **Green highlight** on: Status badge showing "Enabled"
7. **Blue highlight** on: Created date
8. **Red circle** around: Enable/Disable button

**Annotation text to add**:
- "Success!" near the banner
- "New source" pointing to the table row

---

## Screenshot 4: Enable/Disable Button
**Location**: In "Enabling or Disabling a Source" section, after step 2

**What to capture**:
- Close-up of the Actions column in the sources table
- One source row with the Enable/Disable button visible

**What to highlight/annotate**:
1. **Red circle** around: The "Enable" or "Disable" button
2. **Green box** around: The status badge ("Enabled" or "Disabled")
3. **Arrow** pointing from button to status badge

**Annotation text to add**:
- "Click to toggle" near the button
- "Current status" near the badge

---

## Screenshot 5: Run Pipeline Page - Form
**Location**: In "Running the Pipeline" section, after step 2

**What to capture**:
- The "Run Monitoring Pipeline" page
- All checkboxes and options visible

**What to highlight/annotate**:
1. **Green checkmarks** (✓) next to all checked checkboxes:
   - Seed demo sources
   - Scrape enabled sources
   - Detect changes
   - Run AI analysis
   - Test Ollama connectivity
2. **Yellow highlight** on: "AI limit" input field showing "5"
3. **Red circle** around: "Run Monitoring Pipeline" button
4. **Blue box** around: "Advanced Options" section (if visible, show it collapsed)

**Annotation text to add**:
- "Default settings" near the checkboxes
- "Number of changes to analyze" near AI limit field
- "Click to start" near the button

---

## Screenshot 6: Pipeline Results Page
**Location**: In "Running the Pipeline" section, after step 4

**What to capture**:
- The results page after pipeline execution
- Success banner (if changes detected)
- Summary section
- Step-by-step execution section

**What to highlight/annotate**:
1. **Green box** around: Success banner (if present) showing:
   - Number of new changes
   - Number of AI processed changes
   - "View Changes →" button
2. **Yellow highlight** on: "New Changes" value in Summary section
3. **Yellow highlight** on: "AI Processed" value in Summary section
4. **Green checkmarks** (✅) next to successful steps
5. **Red box** around: One step item showing status icon, name, and message

**Annotation text to add**:
- "Pipeline completed!" near success banner
- "Key metrics" near Summary section
- "Step results" near execution log

---

## Screenshot 7: Advanced Options
**Location**: In "Advanced Options" subsection

**What to capture**:
- The expanded "Advanced Options" section
- All advanced checkboxes and warning text

**What to highlight/annotate**:
1. **Red box** around: "Advanced Options" heading
2. **Yellow highlight** on: "Init DB (create tables)" checkbox (unchecked)
3. **Red highlight** on: "Reset demo DB (DANGEROUS)" checkbox (unchecked)
4. **Orange box** around: Warning text about dangerous operations
5. **Red circle** around: Confirmation text field (if reset is checked)

**Annotation text to add**:
- "⚠️ Use with caution" near the section
- "DANGEROUS" near reset checkbox

---

## Screenshot 8: Changes List Page
**Location**: In "The Changes List Page" section, after step 2

**What to capture**:
- Full "Detected Regulatory Changes" page
- Filters section
- Changes table with multiple rows

**What to highlight/annotate**:
1. **Blue box** around: Explanation box at top
2. **Yellow highlight** on: Status dropdown (showing "All Statuses")
3. **Yellow highlight** on: Source ID input field
4. **Red circle** around: "Apply Filters" button
5. **Green box** around: One complete change row showing all columns:
   - ID
   - Detected At
   - Source (bold)
   - Status badge
   - Requirement class
   - Summary (truncated)
   - View button

**Annotation text to add**:
- "Filter options" near filters
- "Change record" pointing to one row

---

## Screenshot 9: Filtered Changes
**Location**: In "Filtering Changes" section, after step 3

**What to capture**:
- Changes list with a filter applied
- Status dropdown showing a selected status (e.g., "AI Suggested")
- Filtered table results

**What to highlight/annotate**:
1. **Yellow highlight** on: Status dropdown showing selected status
2. **Green boxes** around: All status badges in the table matching the filter
3. **Red arrow** pointing from dropdown to matching badges

**Annotation text to add**:
- "Filter active" near dropdown
- "Matching results" near table

---

## Screenshot 10: Change Row Detail
**Location**: In "Understanding the Changes Table" section

**What to capture**:
- Close-up of one change row
- All columns clearly visible

**What to highlight/annotate**:
1. **Red circle** around: Change ID (e.g., "#1")
2. **Yellow highlight** on: Status badge (colored: blue for AI Suggested, green for Validated)
3. **Blue highlight** on: Summary text (showing truncation with "..." if long)
4. **Green circle** around: "View" button

**Annotation text to add**:
- "Unique ID" near ID
- "Current status" near badge
- "Click to view details" near View button

---

## Screenshot 11: Change Detail Page
**Location**: In "Viewing Change Details" section, after step 2

**What to capture**:
- Full change detail page
- All sections visible (may need to scroll, capture main sections)

**What to highlight/annotate**:
1. **Blue box** around: Explanation banner at top
2. **Yellow highlight** on: Metadata section showing:
   - Source (as clickable link)
   - Detected At
   - Status badge
   - Previous/New version numbers
3. **Green box** around: AI-Generated Suggestion section (if present):
   - Requirement class badge
   - Summary text
4. **Red box** around: Change Diff section:
   - Diff content box
   - Lines with `-` (removed, should appear red)
   - Lines with `+` (added, should appear green)

**Annotation text to add**:
- "Change information" near metadata
- "AI analysis" near suggestion section
- "Text differences" near diff section

---

## Screenshot 12: Validation Form
**Location**: In "How to Validate a Change" section, after step 2

**What to capture**:
- The "Human Validation (Required)" section
- The validation form with all options visible

**What to highlight/annotate**:
1. **Red box** around: "Human Validation (Required)" heading
2. **Yellow highlight** on: "Approved" radio button
3. **Yellow highlight** on: "Corrected" radio button
4. **Yellow highlight** on: "Rejected" radio button
5. **Blue highlight** on: "Final Summary" textarea (when visible)
6. **Blue highlight** on: "Final Requirement class" dropdown (when visible)
7. **Green highlight** on: "Notes" textarea
8. **Red circle** around: "Submit Validation" button

**Annotation text to add**:
- "Choose one" near radio buttons
- "Required for corrections" near Final Summary
- "Click to submit" near button

---

## Screenshot 13: Validation Form - Corrected Selected
**Location**: In "How to Validate a Change" section, Option B

**What to capture**:
- Validation form with "Corrected" radio button selected
- All correction fields visible and filled in

**What to highlight/annotate**:
1. **Green circle** around: "Corrected" radio button (selected)
2. **Yellow highlight** on: "Final Summary" textarea with text entered
3. **Yellow highlight** on: "Final Requirement class" dropdown with selection
4. **Blue highlight** on: "Notes" field (if filled)
5. **Red circle** around: "Submit Validation" button

**Annotation text to add**:
- "Selected option" near radio button
- "Your corrections" near textarea
- "Your category" near dropdown

---

## Screenshot 14: Validation Success
**Location**: In "How to Validate a Change" section, after step 4

**What to capture**:
- Page after successful validation
- Success message visible
- Updated status badge

**What to highlight/annotate**:
1. **Green box** around: Success message banner
2. **Yellow highlight** on: Updated status badge (showing "Validated", "Corrected", or "Rejected")
3. **Blue box** around: Validation record information (if displayed)

**Annotation text to add**:
- "Validation saved!" near success message
- "New status" near badge

---

## General Screenshot Guidelines

### Image Quality
- Use **PNG format** for screenshots (better quality than JPG)
- **Resolution**: At least 1920x1080 or higher
- **File size**: Keep under 2MB per image for Word document

### Highlighting Tools
- Use **red circles/arrows** for clickable elements (buttons, links)
- Use **yellow highlights** for important fields or data
- Use **green boxes** for success messages or positive indicators
- Use **blue boxes** for informational sections
- Use **red boxes** for warnings or important sections

### Annotation Text
- Use **Arial or Calibri font**, size 10-12pt
- Place annotations **outside** the highlighted area
- Use **arrows** to connect annotations to elements
- Keep text **concise** (1-3 words per annotation)

### Screenshot Composition
- **Capture full sections** when possible (don't crop important UI elements)
- **Include context** (show surrounding elements, not just the target)
- **Avoid personal information** (blur any names, emails, or sensitive data)
- **Consistent browser** (use same browser for all screenshots)
- **Clean state** (close unnecessary tabs, use default zoom level)

---

## Word Document Formatting Tips

1. **Insert screenshots**:
   - Go to Insert → Pictures → This Device
   - Select the screenshot file
   - Right-click image → Wrap Text → "In Line with Text" or "Square"

2. **Add annotations**:
   - Use Insert → Shapes for circles, arrows, boxes
   - Use Insert → Text Box for annotation text
   - Group shapes and text together (select all → Right-click → Group)

3. **Caption screenshots**:
   - Right-click image → Insert Caption
   - Use format: "Figure X: [Description]"
   - Example: "Figure 1: OffSight Home Page"

4. **Consistent sizing**:
   - Make all screenshots similar width (e.g., 6-7 inches)
   - Maintain aspect ratio when resizing
   - Align screenshots to left margin

---

**End of Screenshot Placement Guide**

