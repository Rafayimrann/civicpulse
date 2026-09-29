import { describe, expect, it } from "vitest";

import { validateComplaintDraft } from "../src/validation";

describe("validateComplaintDraft", () => {
  it("flags text shorter than 10 characters", () => {
    const errors = validateComplaintDraft("short", "Valid location");
    expect(errors.text).toBeDefined();
  });

  it("flags location shorter than 3 characters", () => {
    const errors = validateComplaintDraft("A perfectly valid complaint description here", "ab");
    expect(errors.location).toBeDefined();
  });

  it("passes when both fields are within bounds", () => {
    const errors = validateComplaintDraft("A perfectly valid complaint description here", "Street 12");
    expect(errors).toEqual({});
  });
});
