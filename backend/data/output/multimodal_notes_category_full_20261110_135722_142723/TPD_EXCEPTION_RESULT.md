# TPD-only exception: live extraction result

The requested run bypassed local TPD only. RPM, RPD and TPM, exact-source authorization, identity checks, accounting and evidence validation remained active. No prior reservations were cleared.

Made 103 new API calls. Status counts: {'200': 89, '400': 13, '429': 1}. Reported input/output: 304032/67634; 14 attempts have unknown usage, so total actual usage is unknown.

The provider returned HTTP 429 on TPD: limit 200000, used 196670, requested 3733, retry-after about 174 seconds. The run stopped without retrying or switching organizations to bypass the response.

The combined partial notes contain 420 accepted items (419 facts and one definition), 48 more than the previous preview. Facts and definitions have all primary requests attempted; explanations stopped after four calls. Concepts, examples, procedures, relationships and formulas have not started. Many HTTP 200 responses failed strict evidence validation, so this is not a completed or high-coverage extraction.

34 focused tests passed. The source Stage 4 SHA remains unchanged. Exact request/receipt data and the remaining source gaps remain in the category artifacts. No OCR, retranscription, images, Task 11/12A changes, or historical authorization changes were made by this exception.

See `tpd_exception_result.json` for the scoped audit and `partial_notes.md` for the current combined preview. The original 429 request remains failed and cannot be silently dispatched again by normal resume. Retry-after does not guarantee sufficient capacity for the full remaining document.
