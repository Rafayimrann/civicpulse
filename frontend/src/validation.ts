// Mirrors the server's field-level bounds (text 10-2000 chars, location
// 3-200 chars) so a citizen gets instant feedback instead of a round trip.
// This is NOT a second source of truth for business rules - it duplicates
// only the string-length constraints already enforced in
// backend/app/schemas.py and at the DB layer; category, priority and status
// transitions are never decided here.

export interface ValidationErrors {
  text?: string;
  location?: string;
}

export function validateComplaintDraft(text: string, location: string): ValidationErrors {
  const errors: ValidationErrors = {};

  if (text.trim().length < 10) {
    errors.text = "Please describe the complaint in at least 10 characters.";
  } else if (text.length > 2000) {
    errors.text = "Complaint text must be 2000 characters or fewer.";
  }

  if (location.trim().length < 3) {
    errors.location = "Please provide a location (at least 3 characters).";
  } else if (location.length > 200) {
    errors.location = "Location must be 200 characters or fewer.";
  }

  return errors;
}
