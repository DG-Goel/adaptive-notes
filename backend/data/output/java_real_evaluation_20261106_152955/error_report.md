# Actual execution errors

1. Original chunk 1: HTTP 400, json_validate_failed. Groq reported “max completion tokens reached before generating a valid document.” Reserved input 3,678 and output 3,122 totaled 6,800. Actual token usage was not supplied. The entire reservation remains charged for its rolling windows. No identical retry occurred.
2. Source-boundary recovery: the production splitter created 36 chunks from the same 50 source units without omission or reordering. Revised chunk 1 returned HTTP 200, valid JSON and finish_reason stop. Reported tokens: 2,042 input, 2,940 output, 4,982 total. Output includes 2,227 reasoning tokens; these are already included in completion usage.
3. Revised chunk 1 failed strict source evidence validation. Offline replay reproduced the error. Three of ten quotes differ from the supplied source. This is a model evidence failure, not a credential, quota, browser or JSON syntax failure. It was not automatically corrected. The response and audit are preserved.

No rate-limit response, SQLite contention, timeout or network interruption was observed in these two calls. Those outcomes are not guarantees for future requests. No complete notes were generated.
