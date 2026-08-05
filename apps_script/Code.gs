/**
 * AuditAgent Bench — review sheet writeback.
 *
 * The reviewer works on a browser-only machine, so the Google Sheet is the
 * labeling UI and this script is the only path that stamps label provenance.
 *
 * The single rule this file exists to enforce: `label_source` is written here,
 * on a row a human ticked, and nowhere else. Notebook code never writes
 * `llm_draft_human_verified` — doing so would assert a review that never
 * happened.
 *
 * Setup: Extensions > Apps Script, paste this file, set the script properties
 * listed in requireConfig_(), then run authorizeOnce() to grant scopes.
 */

var SHEET_NAME = 'review';

// Columns the reviewer fills in. A row is exportable only when every required
// column for its task is non-empty.
var REQUIRED_BY_TASK = {
  A: ['severity', 'coso_component'],
  B: ['designed_effectively', 'gap_type'],
  C: ['is_deficient'],
  D: ['citation', 'coso_component']
};

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('AuditAgent')
    .addItem('Validate reviewed rows', 'validateReviewed')
    .addItem('Export reviewed rows to GCS', 'exportReviewed')
    .addToUi();
}

/** Run once from the editor to grant the OAuth scopes this script needs. */
function authorizeOnce() {
  requireConfig_();
  ScriptApp.getOAuthToken();
  Logger.log('Authorized. Config OK.');
}

function requireConfig_() {
  var props = PropertiesService.getScriptProperties();
  var bucket = props.getProperty('GCS_BUCKET');
  var prefix = props.getProperty('GCS_LABEL_PREFIX') || 'processed/labels';
  if (!bucket) {
    throw new Error('Set the GCS_BUCKET script property (Project Settings > Script Properties).');
  }
  return { bucket: bucket, prefix: prefix };
}

function sheet_() {
  var sheet = SpreadsheetApp.getActive().getSheetByName(SHEET_NAME);
  if (!sheet) throw new Error('No worksheet named "' + SHEET_NAME + '".');
  return sheet;
}

/** Read the sheet into objects keyed by header name. */
function readRows_() {
  var values = sheet_().getDataRange().getValues();
  var headers = values.shift();
  return values.map(function (row, i) {
    var obj = { _rowNumber: i + 2 };
    headers.forEach(function (h, j) { obj[h] = row[j]; });
    return obj;
  });
}

function isReviewed_(row) {
  return String(row.reviewed).toUpperCase() === 'TRUE';
}

/**
 * A row is complete when every column its task requires is filled.
 * Task B only requires gap_type when the control is NOT designed effectively.
 */
function incompleteReason_(row) {
  var task = String(row.item_id || '').charAt(0);
  var required = REQUIRED_BY_TASK[task];
  if (!required) return 'unknown task for item_id "' + row.item_id + '"';

  for (var i = 0; i < required.length; i++) {
    var col = required[i];
    if (task === 'B' && col === 'gap_type' &&
        String(row.designed_effectively).toUpperCase() === 'TRUE') {
      continue;
    }
    if (row[col] === '' || row[col] === null || row[col] === undefined) {
      return 'missing ' + col;
    }
  }
  return null;
}

/** Report what would export and what is blocking, without writing anything. */
function validateReviewed() {
  var rows = readRows_();
  var reviewed = rows.filter(isReviewed_);
  var problems = [];

  reviewed.forEach(function (row) {
    var reason = incompleteReason_(row);
    if (reason) problems.push('Row ' + row._rowNumber + ' (' + row.item_id + '): ' + reason);
  });

  var message = reviewed.length + ' of ' + rows.length + ' rows ticked as reviewed.\n' +
    (problems.length
      ? problems.length + ' incomplete:\n\n' + problems.slice(0, 20).join('\n')
      : 'All reviewed rows are complete and ready to export.');

  SpreadsheetApp.getUi().alert('Validation', message, SpreadsheetApp.getUi().ButtonSet.OK);
}

/**
 * Export reviewed, complete rows to GCS with provenance stamped.
 *
 * Incomplete rows are skipped rather than exported with blanks — a partially
 * filled label is not a reviewed label.
 */
function exportReviewed() {
  var config = requireConfig_();
  var rows = readRows_();
  var now = new Date().toISOString();

  var exportable = [];
  var skipped = 0;

  rows.forEach(function (row) {
    if (!isReviewed_(row)) return;
    if (incompleteReason_(row)) { skipped++; return; }

    delete row._rowNumber;

    // Provenance is stamped here, on a human-ticked row, and only here.
    // 'disclosure' where the filer's own characterization supplied the label;
    // otherwise the reviewer authored or accepted it.
    row.label_source = row.label_source || 'human';
    row.reviewed_at = now;
    exportable.push(row);
  });

  if (!exportable.length) {
    SpreadsheetApp.getUi().alert('Nothing to export',
      'No reviewed row is complete. Run Validate for details.',
      SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }

  var ndjson = exportable.map(function (r) { return JSON.stringify(r); }).join('\n') + '\n';
  var objectName = config.prefix + '/reviewed.jsonl';

  uploadToGcs_(config.bucket, objectName, ndjson);

  SpreadsheetApp.getUi().alert('Exported',
    'Wrote ' + exportable.length + ' rows to gs://' + config.bucket + '/' + objectName +
    (skipped ? '\n\nSkipped ' + skipped + ' incomplete reviewed rows.' : ''),
    SpreadsheetApp.getUi().ButtonSet.OK);
}

/**
 * Upload a string to GCS via the JSON API.
 *
 * Uses the script's OAuth token, so the account running the script needs
 * objectCreator on the bucket. The name is URL-encoded because the path
 * contains slashes.
 */
function uploadToGcs_(bucket, objectName, body) {
  var url = 'https://storage.googleapis.com/upload/storage/v1/b/' + encodeURIComponent(bucket) +
    '/o?uploadType=media&name=' + encodeURIComponent(objectName);

  var response = UrlFetchApp.fetch(url, {
    method: 'post',
    contentType: 'application/x-ndjson',
    payload: body,
    headers: { Authorization: 'Bearer ' + ScriptApp.getOAuthToken() },
    muteHttpExceptions: true
  });

  var code = response.getResponseCode();
  if (code < 200 || code >= 300) {
    throw new Error('GCS upload failed (' + code + '): ' + response.getContentText());
  }
}
