# Reviewed student notes — version 8

Source-backed review subset. This is an incomplete preview, not a fully verified course.

Only fields with affirmative source-comparison review are shown. Original items, withheld fields, and evidence remain in the companion audit.

## Source T0002

### DEF_0003

a reserved keyword in Java indicating that a function does not return a value

Source: T0002 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

## Project setup and packages

### FCT_5001

In this recorded IntelliJ demonstration, the project uses JDK version 12. This identifies the tutorial setup, not a present-day version requirement.

Source: T0004 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

### FCT_5002

The tutorial creates a Java project in IntelliJ, checks the selected project SDK, and chooses a project template for a command-line application.

Source: T0004 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

### FCT_5003

A command-line application runs from the command line and has no graphical user interface in this explanation.

Source: T0004 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

### FCT_5004

A package groups related classes, helping organize an application as its number of classes grows.

Source: T0004 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

### FCT_5005

The source describes a convention of reversing the company domain name for a base package. It explicitly says an actual registered Internet domain is not required; the purpose is a namespace for classes.

Source: T0004 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

## Source T0005

### DEF_0038

a public static method with return type void that may take a parameter for passing values to the program

Source: T0005 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

## Assignment, variables and literals

### FCT_0015

int (integer) variables can only store whole numbers without decimal points.

Source: T0010 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

### FCT_0016

The equal sign (=) is called the assignment operator in Java.

Source: T0010 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

### EXM_0002

Declare an integer viewsCount for a video's view count. Use underscores to group digits in a large integer literal for readability.

Source: T0011 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

### FCT_0219

boolean stores true or false values.

Source: T0011 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

### FCT_0224

The source allows an uppercase or lowercase F suffix to represent a floating-point number as a float.

Source: T0012 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

## Object creation

### FCT_0017

In the demonstrated Date example, the source creates an object using the new operator followed by the class name and parentheses.

Source: T0013 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

## String operations

### DEF_0060

**term:** immutable string

Source: T0017 · Field: `/term` · Exact quotations: companion `field_review_queue.json`.

### EXM_0143

replace('!', '*') changes all exclamation marks in the original string to asterisks, producing a new string while leaving the original unchanged

Source: T0017 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

### EXM_0144

The trim method removes extra whitespace at the beginning or end of a string.

Source: T0017 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

## Arithmetic and precedence

### FRM_0014

```text
10 + 3 * 2 = 16
```

Source: T0023 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

**variables / 10:** first operand

Source: T0023 · Field: `/variables/10` · Exact quotations: companion `field_review_queue.json`.

**variables / 2:** third operand

Source: T0023 · Field: `/variables/2` · Exact quotations: companion `field_review_queue.json`.

**variables / 3:** second operand

Source: T0023 · Field: `/variables/3` · Exact quotations: companion `field_review_queue.json`.

### FRM_0015

```text
(10 + 3) * 2 = 26
```

Source: T0023 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

**variables / 2:** multiplier after parentheses

Source: T0023 · Field: `/variables/2` · Exact quotations: companion `field_review_queue.json`.

## Number conversions

### EXM_0155

declare a short variable X set to 1 and an integer Y set to X plus 2; printing Y yields 3

Source: T0024 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

### EXM_0156

assigning a double literal 1.1 to an int variable causes a compilation error; changing the variable type to double allows the assignment and results in 3.1 when adding 2

Source: T0024 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

### CON_0004

**concept_name:** parseInt method

Source: T0025 · Field: `/concept_name` · Exact quotations: companion `field_review_queue.json`.

### EXM_0157

(int) X converts X to an integer, yielding 1 when X is 1.1; adding 2 results in Y = 3

Source: T0025 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

### EXM_0158

Integer.parseInt("1") returns the int 1, which can then be added to other numbers

Source: T0025 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

## Source T0031

### FRM_0007

**Incomplete formula / visual-context warning.** Only individually reviewed components are shown; no complete equation is approved.

**variables / P:** principal or the amount of the loan

Source: T0031 · Field: `/variables/P` · Exact quotations: companion `field_review_queue.json`.

**variables / R:** monthly interest rate

Source: T0031 · Field: `/variables/R` · Exact quotations: companion `field_review_queue.json`.

## Assignment and comparison

### FCT_0326

Equivalent statement: see **FCT_0016**. Sources: T0034.

## Conditional statements

### EXM_0171

If temperature > 30, print "it's a hot day" and "drink plenty of water"; else if temperature is between 20 and 30, print "it's a nice day"; otherwise print "it's a cold day".

Source: T0036 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

### EXP_0115

**topic:** If statements in Java

Source: T0036 · Field: `/topic` · Exact quotations: companion `field_review_queue.json`.

### FCT_0339

In the demonstrated if statement, declaring the local variable directly as the unbraced body produces an error; the source adds braces to create a code block.

Source: T0038 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

## Conditional ordering and alternative approaches

### EXM_0174

Instructional role: **deliberately incorrect demonstration**.

Input 5 → fizz; Input 10 → fizz; Input 3 → buzz; Input 15 → fizz (incorrect; should be fizzbuzz)

Source: T0041 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

### EXP_0127

Instructional role: **explanation of mistake**.

When the first condition checks only divisibility by 5 and is placed before the combined check for 5 and 3, a number like 15 satisfies the first condition, so 'fizz' is printed and the later else‑if branches are skipped.

Source: T0041 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

**topic:** Incorrect ordering of conditional statements causes numbers divisible by both 5 and 3 to output only 'fizz'

Source: T0041 · Field: `/topic` · Exact quotations: companion `field_review_queue.json`.

### PRC_0397

Instructional role: **corrected approach**.

**Step 1:** Import java.util.Scanner and instantiate a Scanner object to read from System.in.

Source: T0029 · Field: `/steps/0` · Exact quotations: companion `field_review_queue.json`.

**Step 2:** Print a prompt asking the user to enter a number.

Source: T0041, T0042 · Field: `/steps/1` · Exact quotations: companion `field_review_queue.json`.

**Step 3:** Read the integer using scanner.nextInt() and store it in a variable (e.g., number).

Source: T0041, T0042 · Field: `/steps/2` · Exact quotations: companion `field_review_queue.json`.

**Step 4:** Check if number % 5 == 0 and number % 3 == 0; if true, print "fizzbuzz".

Source: T0041, T0042 · Field: `/steps/3` · Exact quotations: companion `field_review_queue.json`.

**Step 5:** Else if number % 5 == 0, print "fizz".

Source: T0041, T0042 · Field: `/steps/4` · Exact quotations: companion `field_review_queue.json`.

**Step 6:** Else if number % 3 == 0, print "buzz".

Source: T0041, T0042 · Field: `/steps/5` · Exact quotations: companion `field_review_queue.json`.

**Step 7:** Else, print the number itself.

Source: T0041, T0042 · Field: `/steps/6` · Exact quotations: companion `field_review_queue.json`.

### EXM_0175

Instructional role: **corrected approach**.

If the number is divisible by 5 and 3, print fizzbuzz; otherwise if divisible by 5, print fizz; else if divisible by 3, print buzz; else print the number.

Source: T0042 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

### DEF_0075

DRY means don't repeat yourself. The source discusses duplication as a trade-off, rather than a universal ban on every repeated expression.

Source: T0042 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

### EXM_0176

If the number is divisible by 5, check whether it is also divisible by 3 and print fizzbuzz or fizz accordingly. Otherwise, check divisibility by 3 and print buzz; if neither applies, print the number.

Source: T0042 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

### FCT_0352

Nested if-else statements can make code harder to read; the source prefers a flatter solution in this example despite some repetition.

Source: T0042 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

## Counting loops and input-driven loops

### EXP_0133

In the input-loop explanation, comparing string references does not test their textual values; the source distinguishes the strings' memory locations from their values.

Source: T0044 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

### FCT_0361

The source first demonstrates a counter-based while loop, then an input-driven while loop with no counter variable. The input loop checks whether the user has entered quit.

Source: T0044 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

### FCT_0362

In the counter-based while-loop rewrite, the source decrements the counter at the end of each iteration. The later input-driven example uses no counter variable.

Source: T0044 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

## Input loops and termination

### FCT_5006

The input-loop example uses the equals method of string objects to compare values and repeats while the input does not equal quit.

Source: T0045 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

### FCT_5007

In this example, create the scanner outside the while loop and reuse it, avoiding a new scanner object on each iteration.

Source: T0045 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

### FCT_5008

The example converts input to lowercase after reading it so uppercase or mixed-case versions of quit satisfy the intended termination check.

Source: T0045 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

### FCT_5009

The demonstration echoes entered values back to the terminal and terminates when the user types quit.

Source: T0045 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

### FCT_5010

The source presents while loops as useful when the required number of repetitions is not known ahead of time.

Source: T0045 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

## Loop condition timing

### FCT_5011

A while loop checks its condition first and may execute zero times if the condition is initially false. A do-while loop checks last and executes its body at least once.

Source: T0045 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

### PRC_5001

Instructional role: **continuation**.

The source constructs a do-while loop with its condition after the body.

Source: T0045 · Field: `/content` · Exact quotations: companion `field_review_queue.json`.

**procedure_name:** Constructing a do-while loop

Source: T0045 · Field: `/procedure_name` · Exact quotations: companion `field_review_queue.json`.

**Step 1:** Begin with do and define a code block.

Source: T0045 · Field: `/steps/0` · Exact quotations: companion `field_review_queue.json`.

**Step 2:** Place the repeated actions inside the block.

Source: T0045 · Field: `/steps/1` · Exact quotations: companion `field_review_queue.json`.

**Step 3:** After the block, write while followed by the loop condition.

Source: T0045 · Field: `/steps/2` · Exact quotations: companion `field_review_queue.json`.

**Step 4:** Terminate the do-while statement with a semicolon.

Source: T0045 · Field: `/steps/3` · Exact quotations: companion `field_review_queue.json`.

## Source T0046

### PRC_0400

**Step 1:** Read user input.

Source: T0046 · Field: `/steps/0` · Exact quotations: companion `field_review_queue.json`.
