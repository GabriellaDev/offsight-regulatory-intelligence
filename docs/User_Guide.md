# OffSight™ User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Managing Sources](#managing-sources)
3. [Running the Monitoring Pipeline](#running-the-monitoring-pipeline)
4. [Viewing Detected Changes](#viewing-detected-changes)
5. [Validating Changes](#validating-changes)

---

## Getting Started

### Accessing the Application

1. Open your web browser and navigate to: `http://localhost:8000`
2. You will see the OffSight™ home page with the system logo in the top-left corner.

**📸 SCREENSHOT PLACEMENT: Insert a screenshot of the home page here**

**What to highlight in the screenshot:**
- The OffSight™ logo in the top-left corner
- The navigation menu at the top (Home, Changes, Sources, Run Pipeline)
- The "What this system does" explanation box
- The "End-to-end workflow" section showing the 4-step process

### Understanding the System

OffSight™ monitors regulatory sources (websites containing regulations), stores different versions of those documents, detects when content changes, and uses AI to summarize what changed. Your job as a reviewer is to validate or correct the AI's suggestions.

**The workflow consists of 4 main steps:**
1. **Sources are scraped** - The system retrieves content from configured regulatory websites
2. **Change detection** - The system compares new versions with old ones to find differences
3. **AI analysis** - An AI model generates summaries and categorizes changes
4. **Human validation** - You review and approve, correct, or reject the AI suggestions

---

## Managing Sources

### What are Sources?

Sources are regulatory websites that OffSight™ monitors for changes. You can add new sources, view existing ones, and enable or disable monitoring for each source.

### Adding a New Source

1. Click **"Sources"** in the top navigation menu
2. You will see the "Manage Sources" page with a form at the top

**📸 SCREENSHOT PLACEMENT: Insert a screenshot of the Sources page with the "Add New Source" form visible**

**What to highlight in the screenshot:**
- The "Add New Source" heading
- The form fields: Name, URL, Description
- The "Enabled" checkbox (with the help text below it explaining what it does)
- The "Add Source" button

3. Fill in the form:
   - **Name**: Enter a descriptive name (e.g., "HSE Offshore Safety Regulations")
   - **URL**: Enter the full website address (must start with `http://` or `https://`)
   - **Description**: (Optional) Add a brief description of what this source contains
   - **Enabled checkbox**: 
     - ✓ **Checked** = The system will monitor this source for changes
     - ✗ **Unchecked** = The source will be saved but not monitored

4. Click **"Add Source"**

5. You will see a success message and the new source will appear in the table below

**📸 SCREENSHOT PLACEMENT: Insert a screenshot showing a successfully added source in the table**

**What to highlight in the screenshot:**
- The success message banner (green)
- The new source row in the table showing:
  - Source ID
  - Name
  - URL (as a clickable link)
  - Status badge (Enabled/Disabled)
  - Created date
  - Enable/Disable button

### Enabling or Disabling a Source

1. In the "Configured Sources" table, find the source you want to change
2. Click the **"Enable"** or **"Disable"** button in the Actions column
3. The status will update immediately and you'll see a confirmation message

**📸 SCREENSHOT PLACEMENT: Insert a screenshot showing the Enable/Disable button being clicked**

**What to highlight in the screenshot:**
- The Enable/Disable button for a specific source
- The status badge showing "Enabled" or "Disabled"

**Note**: Only enabled sources will be monitored when you run the pipeline. Disabled sources are saved but ignored during monitoring.

---

## Running the Monitoring Pipeline

### What is the Pipeline?

The monitoring pipeline is a series of automated steps that:
- Retrieves content from enabled sources
- Detects changes between document versions
- Uses AI to analyze and summarize changes

### Running the Pipeline

1. Click **"Run Pipeline"** in the top navigation menu
2. You will see the "Run Monitoring Pipeline" page with checkboxes for different steps

**📸 SCREENSHOT PLACEMENT: Insert a screenshot of the Run Pipeline page showing all the checkboxes**

**What to highlight in the screenshot:**
- The main pipeline options (all checked by default):
  - ☑ Seed demo sources
  - ☑ Scrape enabled sources
  - ☑ Detect changes
  - ☑ Run AI analysis
  - ☑ Test Ollama connectivity
- The "AI limit" field (default: 5)
- The "Run Monitoring Pipeline" button
- The "Advanced Options" section (collapsed by default)

3. **For first-time use or normal operation:**
   - Leave all checkboxes checked (default settings)
   - The "AI limit" field controls how many changes the AI will analyze (default: 5)
   - Click **"Run Monitoring Pipeline"**

4. **Wait for execution** - The page will show a loading state, then redirect to show results

**📸 SCREENSHOT PLACEMENT: Insert a screenshot of the pipeline results page**

**What to highlight in the screenshot:**
- The success banner at the top (if changes were detected)
  - Shows number of new changes detected
  - Shows number of changes analyzed by AI
  - The "View Changes →" button
- The Summary section showing:
  - Sources Seeded
  - Sources Scraped
  - New Documents
  - **New Changes** (highlighted in a different color)
  - **AI Processed** (highlighted in a different color)
- The "Step-by-Step Execution" section showing:
  - ✅ Success indicators for completed steps
  - ⚠️ Warning indicators (if any)
  - ❌ Error indicators (if any)
  - Step messages and counts

### Understanding Pipeline Results

**Success Banner**: If new changes were detected, you'll see a green success banner with a "View Changes →" button. Click it to see the detected changes.

**Summary Section**: Shows totals for:
- **Sources Seeded**: How many sources were added/updated
- **Sources Scraped**: How many enabled sources were checked
- **New Documents**: How many new document versions were stored
- **New Changes**: How many changes were detected (this is the important number!)
- **AI Processed**: How many changes were analyzed by AI

**Step-by-Step Execution**: Shows detailed results for each pipeline step:
- ✅ Green checkmark = Step completed successfully
- ⚠️ Yellow warning = Step completed with warnings (e.g., no sources found)
- ❌ Red X = Step failed (pipeline may have stopped)

**Warnings Section**: If any warnings occurred (e.g., a source failed to scrape), they will be listed here. The pipeline continues even if some sources fail.

### Advanced Options

**📸 SCREENSHOT PLACEMENT: Insert a screenshot showing the expanded Advanced Options section**

**What to highlight in the screenshot:**
- The "Advanced Options" section when expanded
- The "Init DB (create tables)" checkbox (usually unchecked)
- The "Reset demo DB (DANGEROUS)" checkbox (usually unchecked)
- The confirmation text field (only appears when reset is checked)
- The warning text explaining these are dangerous operations

**Warning**: The advanced options are for system maintenance only:
- **Init DB**: Creates database tables (only needed on first setup)
- **Reset demo DB**: Deletes all data (requires typing "CONFIRM" in the text field)

**Do not use these options unless you understand the consequences.**

---

## Viewing Detected Changes

### The Changes List Page

1. Click **"Changes"** in the top navigation menu
2. You will see a list of all detected regulatory changes

**📸 SCREENSHOT PLACEMENT: Insert a screenshot of the Changes list page**

**What to highlight in the screenshot:**
- The explanation box at the top explaining what the page shows
- The Filters section with:
  - Status dropdown (showing "All Statuses" or a selected status)
  - Source ID input field
  - "Apply Filters" button
- The table showing changes with columns:
  - ID
  - Detected At (date and time)
  - Source (bold source name)
  - Status (colored badge: Pending, AI Suggested, Validated, etc.)
  - Requirement class (category name)
  - Summary (2-line preview with ellipsis)
  - Action (View button)

### Filtering Changes

You can filter changes by:

1. **Status**: Select from the dropdown:
   - **All Statuses**: Shows everything
   - **Pending**: Changes not yet analyzed by AI
   - **AI Suggested**: Changes analyzed by AI, awaiting validation
   - **Validated**: Changes approved by a reviewer
   - **Corrected**: Changes where the reviewer provided corrections
   - **Rejected**: Changes rejected by the reviewer

2. **Source ID**: Enter a specific source ID number to see only changes from that source

3. Click **"Apply Filters"** to update the list

**📸 SCREENSHOT PLACEMENT: Insert a screenshot showing filtered results**

**What to highlight in the screenshot:**
- The Status dropdown with a status selected (e.g., "AI Suggested")
- The filtered table showing only changes matching the selected status
- The status badges in the table matching the filter

### Understanding the Changes Table

Each row represents one detected change:

- **ID**: Unique change identifier (e.g., #1, #2)
- **Detected At**: When the change was first detected
- **Source**: Which regulatory source the change came from
- **Status**: Current status of the change (see status meanings above)
- **Requirement class**: AI-assigned category (e.g., "Spatial constraints", "Evidence and reporting requirements")
- **Summary**: AI-generated summary (truncated to 2 lines)
- **Action**: Click "View" to see full details

**📸 SCREENSHOT PLACEMENT: Insert a screenshot showing a specific change row with all columns visible**

**What to highlight in the screenshot:**
- One complete row showing all columns
- The status badge (colored: blue for AI Suggested, green for Validated, etc.)
- The summary text (showing truncation with ellipsis if long)
- The "View" button

### Viewing Change Details

1. Click the **"View"** button for any change
2. You will see the detailed change view

**📸 SCREENSHOT PLACEMENT: Insert a screenshot of the Change Detail page**

**What to highlight in the screenshot:**
- The explanation banner at the top (blue box)
- The Metadata section showing:
  - Source (as clickable link)
  - Detected At timestamp
  - Status badge
  - Previous Version number
  - New Version number
- The AI-Generated Suggestion section (if available):
  - Requirement class badge
  - Summary text
- The Change Diff section:
  - The diff content box (with monospace font)
  - Lines with `-` (red) showing removed text
  - Lines with `+` (green) showing added text

---

## Validating Changes

### What is Validation?

Validation is your review of the AI's suggestions. You can:
- **Approve**: Accept the AI's summary and category as correct
- **Correct**: Provide your own summary and/or category
- **Reject**: Reject the AI's suggestion entirely

### How to Validate a Change

1. Navigate to a change detail page (click "View" on any change)
2. Scroll down to the **"Human Validation (Required)"** section

**📸 SCREENSHOT PLACEMENT: Insert a screenshot of the Validation form**

**What to highlight in the screenshot:**
- The "Human Validation (Required)" heading
- The explanation text above the form
- The radio buttons:
  - ○ Approved (accept AI suggestion)
  - ○ Corrected (provide corrections)
  - ○ Rejected (reject AI suggestion)
- The "Final Summary" textarea (appears when "Corrected" or "Rejected" is selected)
- The "Final Requirement class" dropdown (appears when "Corrected" or "Rejected" is selected)
- The "Notes" textarea (optional)
- The "Submit Validation" button

3. **Choose your validation decision:**

   **Option A: Approve**
   - Select **"Approved"** radio button
   - The AI's summary and category will be accepted as-is
   - Click **"Submit Validation"**

   **Option B: Correct**
   - Select **"Corrected"** radio button
   - Enter your **"Final Summary"** in the textarea
   - Select a **"Final Requirement class"** from the dropdown
   - (Optional) Add **"Notes"** explaining your corrections
   - Click **"Submit Validation"**

   **Option C: Reject**
   - Select **"Rejected"** radio button
   - (Optional) Enter a reason in **"Final Summary"**
   - (Optional) Select a different **"Final Requirement class"**
   - (Optional) Add **"Notes"** explaining why it was rejected
   - Click **"Submit Validation"**

**📸 SCREENSHOT PLACEMENT: Insert a screenshot showing the form with "Corrected" selected and fields filled in**

**What to highlight in the screenshot:**
- The "Corrected" radio button selected
- The "Final Summary" textarea with text entered
- The "Final Requirement class" dropdown with a selection
- The "Notes" field (optional)
- The "Submit Validation" button

4. After submitting, you will see a success message and the change status will update

**📸 SCREENSHOT PLACEMENT: Insert a screenshot showing the success message after validation**

**What to highlight in the screenshot:**
- The green success message banner
- The updated status badge (now showing "Validated", "Corrected", or "Rejected")
- The validation record information (if displayed)

### Understanding Validation Statuses

After validation, the change status will change:

- **Validated**: You approved the AI suggestion
- **Corrected**: You provided corrections to the AI suggestion
- **Rejected**: You rejected the AI suggestion

The system stores a complete audit trail of all validations, including who validated it, when, and what decision was made.

---

## Quick Reference

### Status Meanings

- **Pending**: Change detected but not yet analyzed by AI
- **AI Suggested**: AI has analyzed the change and provided a summary/category
- **Validated**: Reviewer approved the AI suggestion
- **Corrected**: Reviewer provided corrections to the AI suggestion
- **Rejected**: Reviewer rejected the AI suggestion

### Navigation Menu

- **Home**: Overview of the system and workflow
- **Changes**: List of all detected changes (with filtering)
- **Sources**: Manage regulatory sources to monitor
- **Run Pipeline**: Execute the monitoring pipeline

### Common Workflow

1. **Setup**: Add sources and ensure they are enabled
2. **Monitor**: Run the pipeline to check for changes
3. **Review**: View detected changes in the Changes list
4. **Validate**: Review each change and approve, correct, or reject

### Tips

- **Enable only sources you want to monitor** - Disabled sources are ignored during pipeline runs
- **Check pipeline results** - Look for the "New Changes" count to see if anything was detected
- **Use filters** - Filter by status to focus on changes that need your attention (e.g., "AI Suggested")
- **Read the diff** - The change diff shows exactly what text was added or removed
- **Add notes** - When validating, add notes to explain your decision for future reference

---

## Troubleshooting

### No Changes Detected

- **Check source status**: Ensure sources are enabled (green "Enabled" badge)
- **Check pipeline results**: Look at the "Sources Scraped" count - if it's 0, no enabled sources exist
- **Check for warnings**: Review the warnings section in pipeline results

### AI Analysis Not Working

- **Check Ollama**: The "Test Ollama connectivity" step should show success
- **Check AI limit**: If you set a low AI limit (e.g., 1), only that many changes will be analyzed
- **Check status**: Changes must be "Pending" to be analyzed by AI

### Can't See Changes

- **Check filters**: Make sure filters aren't hiding the changes you're looking for
- **Run pipeline**: If you just added a source, run the pipeline to detect changes
- **Check source**: Ensure the source is enabled and was successfully scraped

---

**End of User Guide**

