# Thirty-bundle independent semantic-review pilot

**AWAITING HUMAN REVIEW.** Existing dispositions below are historical assistant source comparisons. No independent pilot decisions have been completed.

Source version: `a5308662926ea1174c36c0f3a10ccdc8b0e80d6b6c172cd2eb6865b3fccce447`

The 30 bundles cover 47 field leaves, not an established number of atomic claims. Review every assertion and qualification in each bundle.

## 1. PRC_0012:/steps/1

Packet: `PKT_2ffd6e655228b706ca684b68bdc9fc6b2cd9265c306c19274ecccbc635c2e0f7`

Selected because: Precommitted hash-ranked draw from unreviewed procedure bundles.

Current historical statuses: PRC_0012:/steps/1 = NOT_REVIEWED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
Call the trim() method on the string
```

Primary sources: T0017. Context sources: none.

### Canonical quote — T0017

```text
we also have another useful method to lowercase let's take a look so to lowercase converts all characters to lowercase and once again you can see that the original string is not affected because this method returns a new string okay we also have two uppercase and another useful method is trim trim and with this we can get rid of extra white spaces that can be at the beginning or the end of a string sometimes our users type unnecessary spaces in form fields so using the trim method we can get rid
```

### Neighbor context — not newly authorized evidence

T0016 · canonical characters 1765–2665 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
ods or functions do find in the string class for example we have this method here ends with and with this we can check to see if our string ends with a character or sequence of characters for example here we can pass their string to see if our message ends with two exclamation marks now instead of printing the message let's print this expression here so let's run the program we get true so this method that we have called here returns a boolean value which can be true or false we also have another method starts with let's take a look now in this case we get false because our message doesn't start with two exclamation marks another useful method is length so we can call that to get the length of a string which is the number of characters so message dot length take a look so in this string we have 13 characters and this is useful in situations where you want to check the length of the input
```

T0018 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
get removed take a look so here's the original string you can see two white spaces at the beginning and here's our string after trimming so these are some useful methods in the string class but this glass has more methods than we don't have time to cover in this lecture but as we go through the course you're gonna learn more about the string class and other useful classes in Java third times will include special characters in our strings like a tab or a new line or a backslash or double quotes so in this tutorial I'm gonna show you how to include these special characters in your strings so here we have the string hello Marsh let's say we want to surround Marsh with double quotes now here's the problem if we add a double quote here Java compiler thinks this is the termination of our string so it doesn't stand what we have after that's why we have a compilation error the fixes problem we n
```

Relationships: []

Mechanical results: [{"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 2. FCT_0333:/content, FCT_0333:/fact_text

Packet: `PKT_910d181e18bb11d28f766f201a26be2bc80d304b3dbda803e65e25d12e5aa0e9`

Selected because: Precommitted hash-ranked draw from unreviewed fact bundles.

Current historical statuses: FCT_0333:/content = NOT_REVIEWED, FCT_0333:/fact_text = NOT_REVIEWED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
When both the first condition (high income or good credit) and the second condition (no criminal record) are true, the person is eligible for a loan.
```

Primary sources: T0036. Context sources: none.

### Canonical quote — T0036

```text
true and the second condition is true then that person is eligible for a new loan so as you can see these logical operators are very useful in implementing real word rules next we're going to talk about if statements in this tutorial we're going to look at if statements in Java if statements are extremely important because they allow us to build programs that can make decisions based on certain conditions here's an example in this file we have a bunch of conditions if temperature is greater than
```

### Neighbor context — not newly authorized evidence

T0035 · canonical characters 1769–2669 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
ery meaningful and descriptive so here's the rule an applicant is eligible if they have high income or good credit if one of these conditions is true they are eligible so we write has high income or so these two vertical bars represent the or operator so if they have high income or good credit then they are eligible so with the or operator if at least one condition is true the result will be true in this example when Java evaluates this expression it starts from the left side this boolean variable is true so it doesn't matter what we have after Java will not evaluate the rest of this expression it simply returns true however if this variable was false Java would continue evaluating this expression hoping that the next boolean value or the next boolean expression is true so this is the or operator and finally we have the not operator that we use to reverse a value let me show you how that
```

T0037 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
and inside these parentheses we type a boolean expression if 10 is greater than 20 and it's less than or equal to 30 you want to print a different message like beautiful day now here I haven't added the braces because we have a single statement so braces are only required if we have multiple statements now this is a little bit controversial some people believe we should always add braces whether we have a single statement or not other people like myself believe this creates unnecessary noise in the code in this tutorial I'm gonna add the braces first and then remove them so you can see the difference so let's add a pair of curly braces here and finally our last condition so if none of these two conditions are true let me print a different message so here we simply type LS we don't have any more conditions so let's add a code block and print cold day now let me define a few terms here we 
```

Relationships: []

Mechanical results: [{"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}, {"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 3. PRC_0399:/steps/3

Packet: `PKT_c97d5931398437f8361c96e3751b6fcc88d33bc792e194dc2e9d0bb9f9dea665`

Selected because: Hash-ranked unreviewed fill; no semantic judgment used for selection.

Current historical statuses: PRC_0399:/steps/3 = NOT_REVIEWED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
The loop will repeat until the user types "quit"
```

Primary sources: T0044. Context sources: none.

### Canonical quote — T0044

```text
times you want to repeat something for example let's say we're going to write a program and ask the user to continuously enter something until they type quit the moment they type quit we're gonna terminate the program in that situation we don't know how many times the user is going to enter something so let's write that program using a while loop I'm gonna delete everything from here all right we're gonna start with our while loop now what is our loop condition here we don't have a counter
```

### Neighbor context — not newly authorized evidence

T0043 · canonical characters 1644–2544 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
ted now at the end of this iteration or at the end of this loop the control moves here so I is incremented by one now we are at the beginning of the second iteration once again this condition is evaluated is one less than five obviously it is so once again the body of this loop gets executed now fast forward at the end of the fifth iteration I will become five five is not less than five so the loop condition will be false and control moves outside of this for loop now here's one thing you need to remember if you want to execute something five times you can initialize your loop counter or loop variable to zero and use the less than operator here another way is to initialize this to one and then use the less than or equal to operator here now to make this more interesting let's print I over here so here we add a space and then concatenate this string with I take a look so we get hello ward
```

T0045 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
to compare their value instead we need to use the equals method of string objects so we want to check to see if the input equals quit now here we need to apply the not operator so as long as the input does not equal quit we're gonna continuously ask the user to enter something so here we can print a label like input and then we can use a scanner object to read something from the terminal so let's create a scanner object and instantiate it using system dot in I didn't call scanner that next this will return a string so we can store it in this input variable now with this implementation in every iteration we're going to create a new scanner object so if the user enters 10 numbers we're gonna create 10 scanner objects in memory this is unnecessary and it's actually a bad practice because it's going to pollute our memory so it's better to create the scanner object outside of a while loop and
```

Relationships: []

Mechanical results: [{"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 4. PRC_0400:/content

Packet: `PKT_ee88585f270b816fc45905fb143b7f510155a4815c76da0a94c363d0a640f4bc`

Selected because: Hash-ranked unreviewed fill; no semantic judgment used for selection.

Current historical statuses: PRC_0400:/content = NOT_REVIEWED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
This procedure ensures that the word "quit" ends the program without being echoed, "pass" causes the loop to restart without echoing, and all other inputs are echoed back.
```

Primary sources: T0046. Context sources: none.

### Canonical quote — T0046

```text
cases for that so just be aware of them but most of the time prefer to use wire loops we're gonna continue with the example from the last tutorial this program we have written has a tiny problem let me show you so I'm gonna run this enter a couple numbers these numbers get echo back beautiful if we type quit the program terminates but the word quit also gets echoed back this is a bit weird so let's look at a couple ideas for solving this problem back to our code one way to solve this problem is
```

### Canonical quote — T0046

```text
to check the input before printing it so here we can type an if statement if the input does not equal quit then we're print it so not equal input dot equals quit if this condition is true then we're going to print the input let's take a look so one to quit beautiful we solved the problem there is another way to solve this problem as well let me show you we can reverse this condition so if the user types quit you can immediately jump out of the loop using the break statement so I'm gonna remove
```

### Canonical quote — T0046

```text
the nut operator if the user types quit we're gonna break out of the loop otherwise we're gonna continue execution and print this input on a terminal so when Java sees the break statement it will ignore everything else after and it will terminate the loop let's run the program once again we enter a couple numbers followed by quit beautiful so this is the break statement we also have the continuous statement that moves control to the beginning of a loop let me show you so let's imagine if the
```

### Canonical quote — T0046

```text
user types pass we don't want to echo that but also we don't want to terminate the loop you want to ask the user to try one more time so after we read the input we can check to see if input equals pass this is where we use the continuous statement when Java sees this it would move control to the beginning of the loop so all these other statements are gonna get ignored and what the user types is not gonna get printed on the terminal let's run the program and see this in action so we type 1 2 pass
```

### Neighbor context — not newly authorized evidence

T0045 · canonical characters 1730–2630 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
 loop called a do-while loop it's very similar to a while loop but it gets executed at least once let me show you what I mean so I'm gonna rewrite the same code using a do-while loop we start with a do keyword then we create a code block at the end of this code block we type while followed by our loop condition so not input dot equals quit and then we terminate this using a semicolon now inside the body of this loop we'll simply copy all these lines we have here now compared these two types of loops with while loops we check the condition first so if the condition is false the first time this loop will never get executed in contrast with do-while loops we check the condition last so do-while loops always get executed at least once even if the condition is false that is the only difference the reality most of the time we use while loops do-while loops are rarely used but there are certain
```

T0047 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
amongst professional programmers just remember if you're using this technique make sure to have a break statement otherwise you will end up with an infinite loop that executes forever it never terminates and that can be very dangerous in terms of memory consumption so if you're using while true make sure you have a break statement in your loop the last type of loop we want to look at is the for each loop in Java we use for each loops to iterate over arrays or collections let me show you so I'm going to start by declaring a string array called fruit and we initialize this with three items let's say Apple mango and orange now let's say we want to iterate over this array and print each item on a terminal we can use any of the loops you learn about earlier like a for loop or a while loop but we can also use the for each loop which is a bit easier let me show you first I'm going to use the fo
```

Relationships: []

Mechanical results: [{"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 5. FCT_0284:/content, FCT_0284:/fact_text

Packet: `PKT_c59fed6c5b902ec7907c6b02950d42252c2aa90a6ab9c9a53f1fc582fe2ff533`

Selected because: Hash-ranked unreviewed fill; no semantic judgment used for selection.

Current historical statuses: FCT_0284:/content = NOT_REVIEWED, FCT_0284:/fact_text = NOT_REVIEWED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
Math.ceil returns the smallest integer greater than or equal to the argument; it returns a double
```

Primary sources: T0026. Context sources: none.

### Canonical quote — T0026

```text
int and a second implementation it takes a double and returns a log so let's pass 1.1 as a float to this method and store the result in an integer like this now we print the result and we get one beautiful another useful method is seal or sealing which returns the smallest integer that is greater than or equal to this number so the ceiling of 1.1 is 2 now here we have a compilation error because this method returns a double but we're storing the result in an integer so here we need to explicitly
```

### Neighbor context — not newly authorized evidence

T0025 · canonical characters 1610–2510 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
 different so here we have parse float so back to this example let's say we get X as a string and we want to convert it to an integer this is how we do it integer dot parse int we pass X here and then add it to take a look so we get 3 you might be curious why this matters why should we parse or convert a string to a number to add it to something else well pretty much in most frameworks for building user interfaces whether you're building a desktop or a mobile application or web application we always receive input from the user as a string so if you have a form with a bunch of text boxes or drop-down lists almost always we get values as a strings so that's why we need to convert these strings to their numeric representation ok now what if X is a floating-point number here what will happen when we try to parse this as an integer let's take a look once again we get an exception which is how
```

T0027 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
different number between 0 to 100 now if we don't want these digits after the decimal point we can either round this number or cast it to an integer let me show you so we can call math that round and pass the result of this expression so I'm gonna cut this add parenthesis to call the round method and then paste that expression now let's run this code so every time we get a double we still have the fraction here so we can change the type to an INT now we have a compilation error because the round method returns a long but here we have declared an integer this is one of those cases where implicit casting cannot happen because we have a value that is represented in 8 bytes of memory and you want to store that in a variable that has only 4 bytes of memory so implicit casting doesn't work but we can use explicit casting because we know the result of this expression is a number between 0 to 10
```

Relationships: [{"target_id": "FCT_0285", "relation": "RELATED_BUT_DISTINCT", "rationale": "Different subjects, operations, values, or instructional roles: Math.ceil returns the smallest integer greater than or equal to the argument; it returns a double | Math.floor returns the largest integer less than or equal to the argument; it returns a double Retain both; similarity is not equivalence.", "claim": "Math.floor returns the largest integer less than or equal to the argument; it returns a double"}, {"target_id": "FCT_0285", "relation": "RELATED_BUT_DISTINCT", "rationale": "Different subjects, operations, values, or instructional roles: Math.ceil returns the smallest integer greater than or equal to the argument; it returns a double | Math.floor returns the largest integer less than or equal to the argument; it returns a double Retain both; similarity is not equivalence.", "claim": "Math.floor returns the largest integer less than or equal to the argument; it returns a double"}]

Mechanical results: [{"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}, {"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 6. PRC_0017:/procedure_name

Packet: `PKT_f1273bda63584d49531b89df338383e4247a66d9a5fdda19d0ee1439af1f9494`

Selected because: Hash-ranked unreviewed fill; no semantic judgment used for selection.

Current historical statuses: PRC_0017:/procedure_name = NOT_REVIEWED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
initialize and use a variable
```

Primary sources: T0010. Context sources: none.

### Canonical quote — T0010

```text
reading them so with this line we're storing number 30 somewhere in computer's memory and we're assigning this label to that memory location now on line 7 instead of printing hello world we can print the value of the age variable take a look so I'm gonna run this program using ctrl + R there you go now we see 30 on the terminal beautiful we can also change the value of our variable so after we initialize it per house we can change it to 35 now when we run this program again we see it 35
```

### Neighbor context — not newly authorized evidence

T0009 · canonical characters 1955–2855 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
ing interfaces you'll learn about many of the useful classes in the standard Java library and finally in the last part we'll be looking at the advanced features in Java such as streams threads database programming and so on so I hope you're gonna join me on this journey and master Java the most popular programming language behind millions of apps and websites you intersection we're gonna look at the fundamentals of programming in Java you're gonna learn about variables and constants primitive and reference types you're gonna learn about casting or type conversion you will learn how to work with numbers strings and arrays and how to read input from the user once you learn all this I'm gonna give you a project you're gonna build a mortgage calculator on your own so make sure to pay great attention to all the materials you're gonna learn because you're gonna use most of them in this project
```

T0011 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
word my it's all in lowercase but the second word starts with a capital letter so this is all about declaring and initializing variables in the next tutorial we're going to talk about various types in Java in this tutorial we're going to talk about various types in Java basically we have two categories of types we have primitive types for storing simple values and non primitive types or reference types for storing complex objects so in the category of primitive types we have white which takes one byte of memory and in one bite we can store values from 128 to 127 now the more bytes we have the larger numbers we can store so next we have short which takes two bytes and with this we can store values up to 32,000 next we have integer which we have seen before integers take four bytes of memory and allow us to store values up to two billion then we have long which takes eight bytes and with t
```

Relationships: []

Mechanical results: [{"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 7. EXM_0173:/exemplifies

Packet: `PKT_129a1471505ca15c5c353701200bca830585e7a42fa82c653d97e7fbfbddc67c`

Selected because: Precommitted hash-ranked draw from unreviewed example bundles.

Current historical statuses: EXM_0173:/exemplifies = NOT_REVIEWED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
Checking user role with if statement
```

Primary sources: T0039. Context sources: none.

### Canonical quote — T0039

```text
statements to execute different parts of code depending on the value of an expression kind of similar to if statements let me show you so let's say we're gonna write a program and check the role of the current user and then we're gonna print different messages or give them different features depending on their row so let's declare a string variable called role and here we set this to admin now to check the role of the user we can write an if statement like this if role equals admin then perhaps
```

### Neighbor context — not newly authorized evidence

T0038 · canonical characters 1827–2727 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
ng false here we type our expression income is greater than $100,000 so here we have a boolean expression if this boolean expression evaluates to true this boolean variable is going to be true otherwise it's going to be false so this is the simplest the most elegant and the most professional way to implement this scenario now one more improvement before we finish this tutorial I personally prefer to wrap this expression in parentheses even though technically we don't need parentheses here but these parentheses make our code more clear more readable let me show you so I'm gonna wrap this inside these parentheses now it's very clear we're obviously on the right side of this assignment operator we have a boolean expression in this tutorial we're gonna look at the ternary operator in Java so we're gonna continue with the example from the last tutorial we had this income variable imagine this
```

T0040 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
to admin but this is just for demonstration in a real program we are not gonna hard code this admin here so we're gonna read the role of the current user from somewhere else we don't know what it is at the time of writing code okay so here we have one condition let's write another condition else if role equals moderator perhaps we want to display a different message so you are a moderator and finally if the role is none of these values you want to print you are a guest so this is one way to implement this scenario using an if statement we can also implement this using a switch statement and sometimes that looks a little bit cleaner let me show you so we start with a switch statement then we add parentheses and inside this parenthesis we add our variable in this case row next we define a block of code and in this block we add one or more case clauses so we have a case for an admin we add 
```

Relationships: []

Mechanical results: [{"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 8. EXP_0137:/topic

Packet: `PKT_f22abe1d458e92ba678319cf0a2186d53d1f46e644a7d056ab748c0c332c6c7d`

Selected because: Precommitted hash-ranked draw from unreviewed explanation bundles.

Current historical statuses: EXP_0137:/topic = NOT_REVIEWED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
control flow statements
```

Primary sources: T0050. Context sources: none.

### Canonical quote — T0050

```text
easier to read and easier to understand chunks and that's what I'm gonna show you next so in this section you'll learn how to control the flow of execution of your programs we started off by talking about the comparison operators for comparing primitive values then we talked about the logical operators like and or and not I showed you how we can use these operators for implementing real word rules and then we talked about three types of control flow statements you learn about conditional
```

### Neighbor context — not newly authorized evidence

T0049 · canonical characters 1704–2604 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
int an error message enter a value between 1 and 30 okay now if you look to the right side again we have two compilation errors monthly interest is not resolved because we have declared it inside of this block so let's move the declaration to the top here we remove the float keyword and declare monthly interest over here that's better and finally for the last question one more time we're to wrap it in this infinite loop this is where we read the number of years and right after this line we need to do our data validation so if yours is greater than or equal to one and it's less than or equal to 30 here we add a code block this is where we calculate the number of payments and then we break actually I forgot to type an S here otherwise if the user enters an invalid value will simply print an error message enter a value between 1 and 30 now here once again we have a compilation error because
```

Relationships: []

Mechanical results: [{"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 9. EXP_0009:/topic

Packet: `PKT_3fd875b57ca31e1d66c92d7f26d7705e8cacc19d0656a4b1a46ba09709f87619`

Selected because: Hash-ranked unreviewed fill; no semantic judgment used for selection.

Current historical statuses: EXP_0009:/topic = NOT_REVIEWED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
naming convention
```

Primary sources: T0010. Context sources: none.

### Canonical quote — T0010

```text
variable into another here is an example let me delete these variables and declare a new variable called my age we set it to 30 and then we declare another variable like her age and we set it to my age so now when we print her age we're gonna see 30 take a look so on line seven recapping the value of this variable into this other variable now one thing I want you to pay attention to here is the convention I have used for naming our variables as I told you before this is called the camelcase
```

### Neighbor context — not newly authorized evidence

T0009 · canonical characters 1955–2855 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
ing interfaces you'll learn about many of the useful classes in the standard Java library and finally in the last part we'll be looking at the advanced features in Java such as streams threads database programming and so on so I hope you're gonna join me on this journey and master Java the most popular programming language behind millions of apps and websites you intersection we're gonna look at the fundamentals of programming in Java you're gonna learn about variables and constants primitive and reference types you're gonna learn about casting or type conversion you will learn how to work with numbers strings and arrays and how to read input from the user once you learn all this I'm gonna give you a project you're gonna build a mortgage calculator on your own so make sure to pay great attention to all the materials you're gonna learn because you're gonna use most of them in this project
```

T0011 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
word my it's all in lowercase but the second word starts with a capital letter so this is all about declaring and initializing variables in the next tutorial we're going to talk about various types in Java in this tutorial we're going to talk about various types in Java basically we have two categories of types we have primitive types for storing simple values and non primitive types or reference types for storing complex objects so in the category of primitive types we have white which takes one byte of memory and in one bite we can store values from 128 to 127 now the more bytes we have the larger numbers we can store so next we have short which takes two bytes and with this we can store values up to 32,000 next we have integer which we have seen before integers take four bytes of memory and allow us to store values up to two billion then we have long which takes eight bytes and with t
```

Relationships: []

Mechanical results: [{"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 10. PRC_0382:/content

Packet: `PKT_bc98e09201e8dc4c8f897058907e033f9d8d02238068eaa5c61b164c51c20212`

Selected because: Hash-ranked unreviewed fill; no semantic judgment used for selection.

Current historical statuses: PRC_0382:/content = NOT_REVIEWED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
The array elements are rearranged into ascending order.
```

Primary sources: T0020. Context sources: none.

### Canonical quote — T0020

```text
it's implemented with different parameter types so we call this method and pass our numbers array now when we run this program we can see our array is sorted beautiful so yeah I've learned that we use arrays to store a list of objects in Java we can also create multi-dimensional arrays for example we can create a two-dimensional array to store a matrix or we can create a three-dimensional array to store data for cube these are useful in scientific computations let me show you so here we have a
```

### Neighbor context — not newly authorized evidence

T0019 · canonical characters 1645–2545 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
fault when we print an array Java returns the string which is calculated based on the address of this object in memory so if you have another array and we print that we're gonna see something different because each object is gonna be in a different memory space okay now how can we see the actual items in this array well we have a class in Java called arrays let me show you arrays so this class is defined in Java that util package let's press ENTER now this is important on the top beautiful so we can use the dot operator to access the members of this class here we have a method called two string now as you see it this method is implemented multiple times so in the first implementation this method gets a float array in the second implementation it takes an integer array and so on so for all primitive types as well as reference types this method is implemented multiple times this is what we
```

T0021 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
this to a two-dimensional array we need to add another pair of square brackets now we have a compilation error because we need to repeat these brackets on the other side so let's say we want to create a 2 by 3 matrix so 2 rows and 3 columns we add in other brackets here and change these lengths to 2 and 3 so now we have 2 rows and 3 columns now to access individual items in this array we need to supply two indexes first the index of the row so we can go to the first row and then the first column and initialize that to 1 now let us print this so and so you t-tap once again we use our arrays class dot to string and pass this object take a look once again we get this weird string because here we're dealing with a multi-dimensional array to solve this problem we need to use another method in this class called deep to string use this for printing multi-dimensional arrays take a look now we ha
```

Relationships: []

Mechanical results: [{"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 11. CON_0028:/content

Packet: `PKT_6a7030d3540e247adebf08f748748e4c03375d88bab5d7da9528afad5982d1d8`

Selected because: Precommitted hash-ranked draw from unreviewed concept bundles.

Current historical statuses: CON_0028:/content = NOT_REVIEWED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
A factory method is a static method that creates and returns an instance of a class, allowing object creation without using the new operator directly.
```

Primary sources: T0028. Context sources: none.

### Canonical quote — T0028

```text
abstract so there is another way let me show you this class has a bunch of methods that start with get so we have get currency instance and when we call this method this will create an instance of the number format class and return it so instead of using the new operator we're gonna use this method here this is what we call a factory method because it's like a factory it creates new are jects now look at the return type of this method it's a number format object okay so we call this method now
```

### Neighbor context — not newly authorized evidence

T0027 · canonical characters 1626–2526 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
nthesis so we add parentheses around this and now let me run this we get an integer between 0 and 100 quite often when we worked with numbers we need to format them as currency values for example we might have a number like this imagine this is the price of a product to display this to the user you want to add a dollar sign here and separate every three digits with a comma or if you might have a number like 0.1 and we want to represent this as a percentage value so instead of 0.1 you want to display 10% so in this tutorial I'm gonna show you how to format numbers in Java we have this class number format that is defined in Java the text package in this package we have a lot of classes for handling text dates numbers and so on so let's press ENTER here it's important on the top beautiful now I want to declare a variable so let's give this variable a name currency now we need to instantiate
```

T0029 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
can see this refactor menu and here we have rename now look at this shortcut on the right side unfortunately it's not visible in my recording window but on Mac is Shift + F I always use shortcuts because they're faster so let's press shift and f6 now we get this red box and below this we can see a few suggestions for a better name we can choose one of these or pick our own name I'm gonna change this to percent and note that as I'm typing this the other reference gets updated automatically so this is very helpful now let's press Enter okay we're done with renaming now let's pass a different value here so let's say we have a number like 0.1 we want to format this as a percent let's run the program there you go you get 10% beautiful now let me show you a cool technique in this program we don't really need this percent object because we have used it in a single place it would make sense to h
```

Relationships: []

Mechanical results: [{"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 12. DEF_0069:/term

Packet: `PKT_3983ad296ea9ea288030d8c521153e073c567b2166fa030573ac3f474fa81e2b`

Selected because: Precommitted hash-ranked draw from unreviewed definition bundles.

Current historical statuses: DEF_0069:/term = NOT_REVIEWED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
abstract class
```

Primary sources: T0028. Context sources: none.

### Canonical quote — T0028

```text
this new number format however we get a compilation error here let's take a look number format is abstract it cannot be instantiated so in Java we have this concept of abstract classes so some classes are abstract and they're basically like a half-baked cake we cannot use the new operator to create an instance of them we're going to talk about abstract classes and why they exist later in the course for now remember that we cannot create an instance of the number format class because it's
```

### Neighbor context — not newly authorized evidence

T0027 · canonical characters 1626–2526 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
nthesis so we add parentheses around this and now let me run this we get an integer between 0 and 100 quite often when we worked with numbers we need to format them as currency values for example we might have a number like this imagine this is the price of a product to display this to the user you want to add a dollar sign here and separate every three digits with a comma or if you might have a number like 0.1 and we want to represent this as a percentage value so instead of 0.1 you want to display 10% so in this tutorial I'm gonna show you how to format numbers in Java we have this class number format that is defined in Java the text package in this package we have a lot of classes for handling text dates numbers and so on so let's press ENTER here it's important on the top beautiful now I want to declare a variable so let's give this variable a name currency now we need to instantiate
```

T0029 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
can see this refactor menu and here we have rename now look at this shortcut on the right side unfortunately it's not visible in my recording window but on Mac is Shift + F I always use shortcuts because they're faster so let's press shift and f6 now we get this red box and below this we can see a few suggestions for a better name we can choose one of these or pick our own name I'm gonna change this to percent and note that as I'm typing this the other reference gets updated automatically so this is very helpful now let's press Enter okay we're done with renaming now let's pass a different value here so let's say we have a number like 0.1 we want to format this as a percent let's run the program there you go you get 10% beautiful now let me show you a cool technique in this program we don't really need this percent object because we have used it in a single place it would make sense to h
```

Relationships: []

Mechanical results: [{"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 13. FCT_0213:/content, FCT_0213:/fact_text

Packet: `PKT_b998a1bcaa5fdd2ee3f77a1ce1081632731ead83dfd61de6e210fb9238acc29b`

Selected because: Unreviewed numeric/range assertion; requires careful source and technical assessment.

Current historical statuses: FCT_0213:/content = NOT_REVIEWED, FCT_0213:/fact_text = NOT_REVIEWED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
short takes two bytes of memory and can store values up to 32,000.
```

Primary sources: T0011. Context sources: none.

### Canonical quote — T0011

```text
one byte of memory and in one bite we can store values from 128 to 127 now the more bytes we have the larger numbers we can store so next we have short which takes two bytes and with this we can store values up to 32,000 next we have integer which we have seen before integers take four bytes of memory and allow us to store values up to two billion then we have long which takes eight bytes and with this we can store even larger numbers now all these types are for storing whole numbers that don't
```

### Neighbor context — not newly authorized evidence

T0010 · canonical characters 1695–2595 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
riable like temperature and set it to 20 so using a comma we can declare multiple variables on the same line now even though this is technically possible it's not something that I recommend so it's always better to declare one variable on each line like this we can also copy the value of one variable into another here is an example let me delete these variables and declare a new variable called my age we set it to 30 and then we declare another variable like her age and we set it to my age so now when we print her age we're gonna see 30 take a look so on line seven recapping the value of this variable into this other variable now one thing I want you to pay attention to here is the convention I have used for naming our variables as I told you before this is called the camelcase notation so we should capitalize the first letter of every word except the first word so in this case the first
```

T0012 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
store values up to two billion but let's say the number of times this video has been watched is three billion so I had a three here now we have a red on the line that indicates an error let me hover our mouse over it we see this tooltip integer number too large so we need to change the type of this variable to long however the error is still there what's going on here the reason we're getting this error is that by default Java sees these numbers as integers so even though we have defined the type of this variable as long Java compiler sees this value as an integer and he thinks this value is too large for an integer to solve this problem we need to add an L as a suffix or this number we can use an uppercase or a lowercase L but as you can see a lowercase L kind of looks like a 1 so it's better to use a capital L so these are examples of whole numbers now let's declare a variable for stor
```

Relationships: [{"target_id": "FCT_0212", "relation": "RELATED_BUT_DISTINCT", "rationale": "Different subjects, operations, values, or instructional roles: byte takes one byte of memory and can store values from -128 to 127. | short takes two bytes of memory and can store values up to 32,000. Retain both; similarity is not equivalence.", "claim": "byte takes one byte of memory and can store values from -128 to 127."}, {"target_id": "FCT_0214", "relation": "RELATED_BUT_DISTINCT", "rationale": "Different subjects, operations, values, or instructional roles: short takes two bytes of memory and can store values up to 32,000. | int (integer) takes four bytes of memory and can store values up to two billion. Retain both; similarity is not equivalence.", "claim": "int (integer) takes four bytes of memory and can store values up to two billion."}, {"target_id": "FCT_0215", "relation": "RELATED_BUT_DISTINCT", "rationale": "Different subjects, operations, values, or instructional roles: short takes two bytes of memory and can store values up to 32,000. | long takes eight bytes of memory and can store even larger numbers. Retain both; similarity is not equivalence.", "claim": "long takes eight bytes of memory and can store even larger numbers."}, {"target_id": "FCT_0212", "relation": "RELATED_BUT_DISTINCT", "rationale": "Different subjects, operations, values, or instructional roles: byte takes one byte of memory and can store values from -128 to 127. | short takes two bytes of memory and can store values up to 32,000. Retain both; similarity is not equivalence.", "claim": "byte takes one byte of memory and can store values from -128 to 127."}, {"target_id": "FCT_0214", "relation": "RELATED_BUT_DISTINCT", "rationale": "Different subjects, operations, values, or instructional roles: short takes two bytes of memory and can store values up to 32,000. | int (integer) takes four bytes of memory and can store values up to two billion. Retain both; similarity is not equivalence.", "claim": "int (integer) takes four bytes of memory and can store values up to two billion."}, {"target_id": "FCT_0215", "relation": "RELATED_BUT_DISTINCT", "rationale": "Different subjects, operations, values, or instructional roles: short takes two bytes of memory and can store values up to 32,000. | long takes eight bytes of memory and can store even larger numbers. Retain both; similarity is not equivalence.", "claim": "long takes eight bytes of memory and can store even larger numbers."}]

Mechanical results: [{"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}, {"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 14. REL_0023:/subject

Packet: `PKT_173b54c3a7f244db116e4bd466448fcc8709596342b8b95fbc5f6503fa62a405`

Selected because: Precommitted hash-ranked draw from unreviewed relationship bundles.

Current historical statuses: REL_0023:/subject = NOT_REVIEWED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
class Date
```

Primary sources: T0013. Context sources: none.

### Canonical quote — T0013

```text
followed by a semicolon in this example this variable we have defined here is an instance of the date class so this class is defined template or blueprints for creating new objects new instances as another example we can have a class called human and we can have objects like John Bob Mary and so on so an object is an instance of a class now this object or this class have members that we can access using the dot operator so we can type now dot and these are all the members defined in this class
```

### Neighbor context — not newly authorized evidence

T0012 · canonical characters 1699–2599 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
 we set it to a note that we should always surround single characters with single quotes and multiple characters or strings with double quotes okay so char represents only one character string represents a series of characters and finally let's see an example of a boolean so we define a boolean variable called is eligible is this person eligible for loan or not we said this to true or false these are the boolean values now note that all these words coded in orange are reserved keywords in Java just like public static void class package these are all reserved keywords so we cannot use these reserved keywords the name our variables classes and methods in the last tutorial you learned that we use primitive types to store simple values like numbers boolean values or single characters in contrast use reference types to store complex objects like data objects or mail messages these are complex
```

T0014 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
have members so if you type age dot we don't see anything these items you see here are not members of age their code snippets which allow us to quickly generate code for example we can select for I and this automatically generates this block of code for us we'll talk about this in the future so this age variable is a primitive type it's not an object it doesn't have any members and that's why when we use the dot operator we don't see anything here now let's delete this line and instead print the value of this data object so once again we can type system this is a class so we can use the dot operator to access its members here we have out which is a field and the type of this field is print string which is another class in Java so once again we can use a dot operator and call the print line function now let me show you a very cool shortcut instead of typing all this we can use one of thes
```

Relationships: []

Mechanical results: [{"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 15. FCT_0352:/content, FCT_0352:/fact_text

Packet: `PKT_886db8f4f52082cb3cd83b4c9106b3c23a0dd07e6eb7604e6942a8095bf14eb0`

Selected because: Nested-conditional advice must retain its scoped trade-off.

Current historical statuses: FCT_0352:/content = SUPPORTED, FCT_0352:/fact_text = SUPPORTED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
Nested if-else statements can make code harder to read; the source prefers a flatter solution in this example despite some repetition.
```

Primary sources: T0042. Context sources: none.

### Canonical quote — T0042

```text
why this line will not be executed so in situations like this you should have the most specific conditions on the top and the most generic ones on the bottom in this case we want to move this condition to the top so if the number is divisible by 5 & 3 we're gonna print fizzbuzz so this is very specific otherwise if the number is only divisible by 5 we print fizz else if it's divisible by 3 we print buzz and finally if none of his conditions is true then we print the same number now let's run the program one more time so we enter 15 and we get fizzbuzz beautiful so here's one way to solve this problem now I've seen some people argue that we have repeated this expression twice number is divisible by 5 we have that here on line 12 as well as line 14 in programming we have this concept called dry which is short for don't repeat yourself so some people argue that here we have repeated this expression and this is not a good solution here is another way let me show you so we're gonna get rid of this second condition here instead we're gonna add a code block over here so if the number is divisible by 5 first we check to see if the number is also divisible by 3 if that's the case we print fizzbuzz otherwise we print just fizz like this okay now we no longer need these two lines because we already implemented this concept here so first we check to see if the number is divisible by five if not we check to see if it's divisible by three and otherwise so here is another way to solve this problem but in my opinion this approach is kind of amateurish and ugly because these nested if-else statements are considered a bad practice now this is not terribly bad but the more you nest these L statements the more confusing your code is going to be to other people so I personally prefer the previous solution even though we had a bit of repetition in the code the more you program the more you build software the more you realize that there is no way to build ideal software programming and problem solving is all about trade-offs every solution has certain strengths and certain weaknesses this solution doesn't have any repetition or duplication in the code but it has a nested structure and these nested structures make our code hard to read and understand the previous solution had a bit of repetition but it had a flat structure there is no nesting here and this code is cleaner and easier to read there are times that we want to repeat one or more statements for example let's say we have this hello world message here let's say we want to print this five times on the terminal we don't want to repeat this
```

### Neighbor context — not newly authorized evidence

T0041 · canonical characters 1553–2453 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
ble by 3 we print buzz we need another condition if this number is divisible by 5 and 3 so here we use the and operator number divisible by 3 equals 0 in this case we want to print fizz buzz otherwise you want to print the same number like this now this is not the right solution as I will show you in a second this program has a book but it's a very common solution that I see amongst my students so let's run this program and see what is wrong here all right here we enter five we get fizz utiful what if you enter ten ten is also divisible by 5 so we get fits so far so good what about a number that is divisible by 3 we get buzz good what if we enter a number that is divisible by both 5 & 3 like 15 we get physican why is that here's the reason with this implementation if we enter 15 this first condition will evaluate to true so we get fizz these other else clauses will be ignored and that is
```

T0043 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
code like this this looks very ugly that's where we use loops in Java we have a few different types of loops the first one that I'm going to talk about in this tutorial is for loops so let's see how we can use a for loop here I'm going to delete all this code you start by typing the for keyword followed by parentheses and inside these parentheses we need to do three things first we need to declare a loop or counter variable so let's declare a variable called I and initialize it to 0 quit often use variable names like I J and K for loop counters next we add a semicolon to terminate the first statement then we write a boolean expression that determines how many times this loop is gonna get executed so I than five as long as I is less than five this loop will be executed once again we add a semicolon and finally we increment I by one like this so this is the basic structure for a for loop n
```

Relationships: []

Mechanical results: [{"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}, {"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 16. EXP_0004:/content, EXP_0004:/explanation_text

Packet: `PKT_1352c8831b40fcb17d5cea21912946cd92dea2ea21442fe570d9909c3d478440`

Selected because: Literal code also occurs inside procedure prose; verify fragment withholding and retained instructions.

Current historical statuses: EXP_0004:/content = NOT_REVIEWED, EXP_0004:/explanation_text = NOT_REVIEWED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
````text
Changing a field (e.g., `point1.x = 2;`) updates the single underlying object. Since `point2` references the same object, reading `point2.x` will reflect the updated value.
````

Primary sources: T0015. Context sources: none.

### Canonical quote — T0015

```text
and point two are referencing the exact same point object in memory we only have one point object so these two variables are not independent of each other they're referencing the same object and that means if I update this point object through either of these variables the changes will be visible to the other variable I'm gonna show you so using the first variable point one we're going to update the value of x so we use the dot operator and here we can see the members of this object X on Y are
```

### Canonical quote — T0015

```text
both fields which are variables that exist inside of a class so we said X just like a regular variable to a different value let's say two now because point one and point two are referencing the exact same object if we print point two we're going to see the change that we just made take a look so S or ut tab let's print point to run the program there you go so the change was visible so remember this reference types are copied by the references whereas primitive types are copied by their value and
```

### Neighbor context — not newly authorized evidence

T0014 · canonical characters 1624–2524 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
hese two categories of types in terms of memory management and that's what we're going to talk about in this tutorial so I'm going to declare a primitive variable X and set it to 1 and then I'm going to declare another variable like Y and set it to X so in this example we have two different variables x and y and these two variables are at different memory locations so they're completely independent of each other in other words if I change the value of X Y is not going to get affected let me show you so I'm gonna update X to 2 and then print Y so syu t tab y let's take a look so run as you can see Y is not affected because x and y are completely independent of each other however when we use a reference time this behavior is different let's take a look so I'm gonna delete all the code here in Java we have a point class that is defined in this package Java that awt so we press ENTER and now
```

T0016 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
printed the hello world message on a terminal this hello word that we have here is a string or more accurately it's a string literal that means a string value now let's extract this from here and store it in a string variable so cut just before this line we type string now look this string class is defined in Java that Lang package what is interesting is that we don't have an import statement to import this package or import this class because this package is automatically imported so we can use any classes that are defined in this package now let's declare a variable called message and because this is a reference type we should instantiate this variable using the new operator so Neal string and here in parenthesis we type our message hello world however here we have this little warning take a look new string is redundant because in Java there is a shorter way to initialize string variab
```

Relationships: []

Mechanical results: [{"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}, {"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 17. FCT_5011:/content, FCT_5011:/fact_text

Packet: `PKT_5a243a5153e7d2756e751e1d1b948db718634258f766fdc40ea18b24a1ec2984`

Selected because: Recovered zero-execution versus at-least-once condition timing.

Current historical statuses: FCT_5011:/content = SUPPORTED, FCT_5011:/fact_text = SUPPORTED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
A while loop checks its condition first and may execute zero times if the condition is initially false. A do-while loop checks last and executes its body at least once.
```

Primary sources: T0045. Context sources: none.

### Canonical quote — T0045

```text
with while loops we check the condition first so if the condition is false the first time this loop will never get executed in contrast with do-while loops we check the condition last so do-while loops always get executed at least once even if the condition is false
```

### Neighbor context — not newly authorized evidence

T0044 · canonical characters 1720–2620 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
that situation we don't know how many times the user is going to enter something so let's write that program using a while loop I'm gonna delete everything from here all right we're gonna start with our while loop now what is our loop condition here we don't have a counter variable in this example instead we want to check to see if the user entered quit or not so here we can declare a string called input and initialize it to an empty string then we can write a while loop like this while input does not equal to quit now this code is not gonna work because input is a string which is a reference type and we cannot use comparison operators between reference types because these operators will compare the address or a string objects not their value so if you have two strings quit and quit but stored in different memory locations to have different addresses so we can use the inequality operator
```

T0046 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
cases for that so just be aware of them but most of the time prefer to use wire loops we're gonna continue with the example from the last tutorial this program we have written has a tiny problem let me show you so I'm gonna run this enter a couple numbers these numbers get echo back beautiful if we type quit the program terminates but the word quit also gets echoed back this is a bit weird so let's look at a couple ideas for solving this problem back to our code one way to solve this problem is to check the input before printing it so here we can type an if statement if the input does not equal quit then we're print it so not equal input dot equals quit if this condition is true then we're going to print the input let's take a look so one to quit beautiful we solved the problem there is another way to solve this problem as well let me show you we can reverse this condition so if the user
```

Relationships: []

Mechanical results: [{"original_item_result": null, "original_validation_scope": "not recorded", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}, {"original_item_result": null, "original_validation_scope": "not recorded", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 18. FRM_0007:/content, FRM_0007:/formula_text

Packet: `PKT_18a12f956bb0f781d13cb374de41c08a21ff13388de2830fb59e507d17680e29`

Selected because: Unresolved mortgage equation and repaired multi-source context; keep visual limitation.

Current historical statuses: FRM_0007:/content = PARTIALLY_SUPPORTED, FRM_0007:/formula_text = PARTIALLY_SUPPORTED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
mortgage = P * R
```

Primary sources: T0031. Context sources: T0033.

**Warning: incomplete / visual-dependent formula. Do not approve a complete equation from its components.**

### Canonical quote — T0031

```text
to combine this suit together this is not ideal so that's when we use the next line method with this method we get the in turn line that the user enters no matter how many spaces or tabs are there take a look so Marsh comma Donny and we get the full name now what if I type a few spaces before my name let's see what happens so those spaces also appear here and this looks a little bit odd this is where we use the trim method remember we trim we can get rid of all these white spaces before or after a string so this next line method returns a string that we are storing in this variable right now just before storing the result in this variable here we can use the dot operator to access the members of this string object so we call the trim method and then store the result in this variable once again we're chaining multiple methods here let's run the program so a few spaces Maharani and you get this beautiful output right now it's time for a project I want you to use what you have learned in a section and build a mortgage calculator like this so when you run this program we get a few questions the first question is the principal or the amount of loan we want to get let's say $100,000 the second question is the annual interest rate let's say three point nine two percent and the third question is period in years let's say you want to get a loan for thirty years so this program calculates our monthly payments and displays it as a currency this is a great exercise for you to practice all the materials you learn in this section now before you get started I want to give you a few hints here is a formula for calculating the mortgage or the monthly payments I found this page on wikiHow comm is called calculate mortgage payments so let's see how this works mortgage equals P or principal or the amount we're gonna loan multiplied by R which is our monthly interest rate this is very important so this number that we get here is our annual interest rate we need to divide this by 12 also take into account that this number is represented as a percent to calculate the actual interest rate you need to divide this number by 100 so in this example the interest rate is zero point zero three nine two so whatever the user enters divided by 100 and then divided by twelve to get to the monthly interest rate now we have this monthly interest rate we need to multiply this by this expression here we need to add 1 to this interest rate and raise it to the power of n where n is the number of payments so we need to multiply this number by 12 or 12 months to
```

### Canonical quote — T0033

```text
because the maximum number we want to support is 30 so one byte is sufficient to store the number 30 or anything smaller now based on the number of years we calculate the number of payments note the camel notation here I've capitalized the first letter of every word except the first word so we get the Earth's and x months in here again the code is very self-explanatory once we collect all this data then we calculate the mortgage so we get a principal multiplied by this expression and then divide it by this other expression let's have a quick look here now this looks a little bit complicated so if you're not download my source code look below this video I'm attached it for you to download and finally after we calculate the mortgage we use the number format class to format this value as a currency so we get a result store it in this string mortgage format it and print it over here now here we can also avoid declaring this variable and simply add this expression over here but it decided to do this to increase the readability of this code otherwise this line would be so long but that's just my personal preference you don't have to follow this alright so this was my implementation of the mortgage calculator however this program has a number of problems the first problem is input validation so if we run this and enter a non numeric value like XYZ our program crashes or as another example if we enter a negative value here our program is not gonna behave properly so that's where conditional statements come to the rescue in the next section we're going to talk about conditional statements you will learn how to use these statements to validate the values entered by the user so that brings us to the end of this section I hope you learn a lot and thank you for watching so in this section you'll learn all about variables and constants you learn about primitive and reference types you learn that primitive types store simple values but reference types hold references to complex objects that's why we call them reference types you also learn about casting and type conversion you learn about two types of casting implicit and explicit you learn how to work with numbers strings and arrays and finally you learned how to read input from the terminal I hope you learned a lot I've been enjoying the course so far in the next section we're going to look at conditional statements for controlling the flow of our programs so I'll see you in the next section hey Marcia I just want to make a quick announcement this course you've been watching is actually the beginning of my complete Java series in this course we only talk about the basics but in my complete series we go way beyond that so if you're serious about Java if you're
```

### Neighbor context — not newly authorized evidence

T0030 · canonical characters 1651–2551 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
 look at the differences so first I'm going to call the next method here we have a compilation issue because this method returns a string I'm gonna change this to a string let me collapse this that's better we should also rename this variable so what was the shortcut Shift + f6 now let's train just a name enter beautiful and one last time we should also update the label name run the program so I'm gonna type my name here Marsh it says your Amash pretty under for one more time this time I'm gonna type my full-name maha Madani but we don't get the last name here's the reason these wars that we have here these are called tokens every time we call the next method it reads one token so here we have a space we have two tokens and we need to call the next method two times to get the full name the first time we call it it returns Marsh the second time we call it it returns Hamid ani then we need
```

T0032 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
calculate the number of payments now to raise this number to the power of n you need to use the power method of the math class so this math class has this power or power method that takes two arguments or two values a and B so go ahead and spend ten to fifteen minutes on this exercise when you're done come back see my solution all right let's see what I've done here and by the way don't worry if your coat is different from mine we all think and coat differently so it's perfectly fine if your code is different just look at my coat see what I've done here and see if there are ways you can improve your coat that's what matters okay so here in our main method first I've declared two final variables or constants the first one is months in year which I've set to 12 and the second one is percent which I've set to 100 the reason I declared this constant is that I didn't want to have magic number
```

T0032 · canonical characters 1713–2613 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
ple and we read the answer as an integer I thought integer is a good datatype for storing the principle because short is not enough with short we can store a maximum of $32,000 that's not enough what if someone wants to find us $1,000,000 so int is good and it allows us to store a value up to two billion next we ask the second question annual interest rate we read this as a float here I could use double but the interest rate is a small number so float is sufficient for that we don't really need double so we get the annual interest and then based on that we calculate the monthly interest also see how I have named my variables all variables have a proper meaningful names there are no magic words here like MI as it short for monthly interest or m1 or m2 do not use magic names for your variables always use meaningful and descriptive names alright next we get the period we read this as a byte
```

T0034 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
looking for a job as a Java developer I highly encourage you to enroll in my complete Java series it's exactly the same structure the same quality but it has way more content plus you will get a certificate of completion that you can add to your resume so if you're interested I put the link down below you can get the course with a discount and if you're not happy for any reasons you can ask for a refund within the first 30 days so I hope to see you in the course in this section we're going to look at control flow or controlling the flow of execution of our programs you're gonna start off by talking about comparison operators for comparing values then I'm gonna talk about logical operators like the logical and logical or and logical not we use these operators for implementing real world rules and then we're gonna talk about three different types of control flow statements we're going to t
```

Relationships: []

Mechanical results: [{"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}, {"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 19. EXP_0133:/content, EXP_0133:/explanation_text

Packet: `PKT_6a6417d0f596fb868619f0d59191e57ebae4a53987dddc06112f95e102a4545b`

Selected because: Distinguish reference comparison from comparison of textual values.

Current historical statuses: EXP_0133:/content = SUPPORTED, EXP_0133:/explanation_text = SUPPORTED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
In the input-loop explanation, comparing string references does not test their textual values; the source distinguishes the strings' memory locations from their values.
```

Primary sources: T0044. Context sources: none.

### Canonical quote — T0044

```text
one two three four five in contrast if we initialize I to zero and use the less than operator we will get hello word zero one two three four we can also print these numbers in reverse order so we initialize I to five and execute this loop as long as I is greater than zero but here instead of incrementing I we decrement it now we get hello world five four three two one so this is all about for loops next we're gonna look at while loops in this tutorial we're gonna talk about while loops in Java while loops are very similar to for loops in terms of their functionality but they're different in terms of syntax let me show you so we're gonna continue with the example from the last tutorial I'm gonna rewrite this code using a while loop so first we declare a loop variable and I initialize it to zero next we type while and here in parentheses we type our loop condition while I is greater than zero then we're gonna execute the code inside this block so I'm gonna copy this from here paste it in this block and finally we need to decrement I like this so at the end of each iteration we decrement I just like our for loops so as you can see we can achieve the same thing using a for loop or a while loop however the implementation using the for loop is a little bit lighter and cleaner so in situations where you know ahead of time how many times you want to execute one or more statements it's better to use a for loop while loops are better in situations where we don't know exactly how many times you want to repeat something for example let's say we're going to write a program and ask the user to continuously enter something until they type quit the moment they type quit we're gonna terminate the program in that situation we don't know how many times the user is going to enter something so let's write that program using a while loop I'm gonna delete everything from here all right we're gonna start with our while loop now what is our loop condition here we don't have a counter variable in this example instead we want to check to see if the user entered quit or not so here we can declare a string called input and initialize it to an empty string then we can write a while loop like this while input does not equal to quit now this code is not gonna work because input is a string which is a reference type and we cannot use comparison operators between reference types because these operators will compare the address or a string objects not their value so if you have two strings quit and quit but stored in different memory locations to have different addresses so we can use the inequality operator
```

### Neighbor context — not newly authorized evidence

T0043 · canonical characters 1644–2544 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
ted now at the end of this iteration or at the end of this loop the control moves here so I is incremented by one now we are at the beginning of the second iteration once again this condition is evaluated is one less than five obviously it is so once again the body of this loop gets executed now fast forward at the end of the fifth iteration I will become five five is not less than five so the loop condition will be false and control moves outside of this for loop now here's one thing you need to remember if you want to execute something five times you can initialize your loop counter or loop variable to zero and use the less than operator here another way is to initialize this to one and then use the less than or equal to operator here now to make this more interesting let's print I over here so here we add a space and then concatenate this string with I take a look so we get hello ward
```

T0045 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
to compare their value instead we need to use the equals method of string objects so we want to check to see if the input equals quit now here we need to apply the not operator so as long as the input does not equal quit we're gonna continuously ask the user to enter something so here we can print a label like input and then we can use a scanner object to read something from the terminal so let's create a scanner object and instantiate it using system dot in I didn't call scanner that next this will return a string so we can store it in this input variable now with this implementation in every iteration we're going to create a new scanner object so if the user enters 10 numbers we're gonna create 10 scanner objects in memory this is unnecessary and it's actually a bad practice because it's going to pollute our memory so it's better to create the scanner object outside of a while loop and
```

Relationships: []

Mechanical results: [{"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}, {"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 20. EXM_0174:/content, EXM_0174:/example_text

Packet: `PKT_17f8fe1af9b38f9633c22f26950310dae6a12ecb4cefed6b61ed51aa61541584`

Selected because: Check that the intentionally incorrect output is not taught as the correct rule.

Current historical statuses: EXM_0174:/content = SUPPORTED, EXM_0174:/example_text = SUPPORTED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
Input 5 → fizz; Input 10 → fizz; Input 3 → buzz; Input 15 → fizz (incorrect; should be fizzbuzz)
```

Primary sources: T0041. Context sources: none.

Instructional role: deliberately_incorrect_demonstration.

### Canonical quote — T0041

```text
one so as you can see with sweet statements we can execute different code depending on the value of an expression all right now it's time for an exercise this exercise I'm gonna give you is a popular interview question so I want you to write a program that behaves like this here we should enter a number if this number is divisible by five we get this so if you run the program again and enter ten once again we get fit now if this number is divisible by 3 we get buzz if this number is divisible by both five and three like fifteen or thirty or whatever we get fizzbuzz and if this number is not divisible by five or three like two we get the same number printed on the terminal so go ahead and spend five to ten minutes on this exercise you'll see my solution next all right to read the number first we need to use the scanner object so scanner we import this and instantiate it and as you know here we need to pass system that in to read data from the terminal now we print a message so we're gonna use the print method instead of print line here we add a label like number and then we call scanner the next int to read a number we store it in this variable number okay so the first part is done now we need to check to see if this number is divisible by five or not so we can write an if statement like this if number here we use the modulus operator which returns the remainder of a division so we divide this by five and if the remainder equals zero that means this number is divisible by 5 so we print fizz now otherwise if this number is divisible by 3 we print buzz we need another condition if this number is divisible by 5 and 3 so here we use the and operator number divisible by 3 equals 0 in this case we want to print fizz buzz otherwise you want to print the same number like this now this is not the right solution as I will show you in a second this program has a book but it's a very common solution that I see amongst my students so let's run this program and see what is wrong here all right here we enter five we get fizz utiful what if you enter ten ten is also divisible by 5 so we get fits so far so good what about a number that is divisible by 3 we get buzz good what if we enter a number that is divisible by both 5 & 3 like 15 we get physican why is that here's the reason with this implementation if we enter 15 this first condition will evaluate to true so we get fizz these other else clauses will be ignored and that is
```

### Neighbor context — not newly authorized evidence

T0040 · canonical characters 1619–2519 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
matically jump out of this block in contrast if we didn't use this break statement here Java will continue executing these other lines here so if the role is admin first it will execute this line and then it will jump to this case block it will execute this other line and then after it executes this break statement it will jump out of this switch block okay so this is how we use a switch statement now compare this with wave statement some people prefer to use if statements others prefer to use a switch statement now one more thing before we finish this tutorial here we're comparing the value of role with strings but we could also use integers other than the long type so if roll was a byte short or an integer our cases would look like this case one case two and so on now here we have a compilation error because roll is a string let's change this to an integer and we can initialize this to
```

T0042 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
why this line will not be executed so in situations like this you should have the most specific conditions on the top and the most generic ones on the bottom in this case we want to move this condition to the top so if the number is divisible by 5 & 3 we're gonna print fizzbuzz so this is very specific otherwise if the number is only divisible by 5 we print fizz else if it's divisible by 3 we print buzz and finally if none of his conditions is true then we print the same number now let's run the program one more time so we enter 15 and we get fizzbuzz beautiful so here's one way to solve this problem now I've seen some people argue that we have repeated this expression twice number is divisible by 5 we have that here on line 12 as well as line 14 in programming we have this concept called dry which is short for don't repeat yourself so some people argue that here we have repeated this ex
```

Relationships: [{"target_id": "EXP_0127", "relation": "explained_by", "claim": "When the first condition checks only divisibility by 5 and is placed before the combined check for 5 and 3, a number like 15 satisfies the first condition, so 'fizz' is printed and the later else‑if branches are skipped."}, {"target_id": "EXM_0175", "relation": "corrected_by", "claim": "If the number is divisible by 5 and 3, print fizzbuzz; otherwise if divisible by 5, print fizz; else if divisible by 3, print buzz; else print the number."}, {"target_id": "PRC_0397", "relation": "corrected_by", "claim": "A simple console program that reads an integer and prints fizz, buzz, fizzbuzz, or the number based on divisibility rules."}, {"target_id": "EXP_0127", "relation": "explained_by", "claim": "When the first condition checks only divisibility by 5 and is placed before the combined check for 5 and 3, a number like 15 satisfies the first condition, so 'fizz' is printed and the later else‑if branches are skipped."}, {"target_id": "EXM_0175", "relation": "corrected_by", "claim": "If the number is divisible by 5 and 3, print fizzbuzz; otherwise if divisible by 5, print fizz; else if divisible by 3, print buzz; else print the number."}, {"target_id": "PRC_0397", "relation": "corrected_by", "claim": "A simple console program that reads an integer and prints fizz, buzz, fizzbuzz, or the number based on divisibility rules."}]

Mechanical results: [{"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}, {"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 21. FRM_0014:/content, FRM_0014:/formula_text

Packet: `PKT_113b0c5939c1bcf0cd7b41e3fb2f6e40549f3b50d87173bcb8bced946f76de0c`

Selected because: Source expression and multiplication precedence.

Current historical statuses: FRM_0014:/content = SUPPORTED, FRM_0014:/formula_text = SUPPORTED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
10 + 3 * 2 = 16
```

Primary sources: T0023. Context sources: none.

### Canonical quote — T0023

```text
the same result take a look too however if we use this on the right side of an assignment operator we get different results let me show you so I'm gonna declare another variable Y we set it to X plus plus in this case because we have applied the increment operator as a postfix first the value of x will get copied to Y so Y would be 1 and then X will be incremented by 1 so if you print x and y x is gonna be 2 and Y is gonna be 1 take a look so X is 2 and Y is 1 beautiful however if you apply this as a prefix first X will be incremented by 1 so it will be 2 and then it will be copied to Y so in this case both X&Y will be to take a look so we get two and two now what if you want to increment X by more than one let's say by two well there are two ways to do this let's remove Y we don't really need it anymore we can write x equals x plus 2 so first we add 2 to X the result will be three and then three will be copied into X the other way is to use the Augmented or compound assignment operator so we can write X plus equals two what we have on line eight is exactly identical to what we have on line seven well as you can see it's shorter so this is a better way to write the same code now this is one of the Augmented assignment operators we have the Augmented assignment operator for other arithmetic operators so we can type X minus equals 2 and this would reduce the value of x by 2 we also have multiply and divide so these are the Augmented or compound assignment operators right now I've got a question for you here we have declared this variable X it goes to 10 plus 3 times 2 what do you think is the result of this expression the result is 16 let's run this program and find out so run there you go we got 16 but why well this is a very basic math concept that unfortunately a lot of people don't know in math the multiplication and division operators have a higher priority so they get applied first in this example this expression 3 times 2 is evaluated first the result is 6 and then 6 is added to 10 that's why we get 16 now if you want to change the order of these operators you can always use parentheses for example if you want this expression to be evaluated first we wrap it in parentheses so like this now Java compiler will first evaluate this expression the result will be 13 and then 13 is multiplied by 2 so we get 26 take a look there you go so
```

### Neighbor context — not newly authorized evidence

T0022 · canonical characters 1666–2566 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
are casting or converting this number to a double similarly we should do that here and now we have a compilation error because on the left side we declared an integer but here the result of this expression is a double and by the way an expression is a piece of code that produces a value so what we have here is an expression because it produces a value so to fix this problem we need to change this to double now when we run this program we get this floating point number beautiful so these are the arithmetic operators and these numbers that we have here are called operands we also have increment and decrement operators let me show you so I'm gonna declare a new variable int X we set it to 1 now if you want to increase the value of x by 1 we use the increment operator now let's print this on a terminal so we get 2 there you go we can apply this operator as a postfix or as a prefix and we get
```

T0024 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
be aware of the order of these operations parentheses always have the highest priority then we have multiplication and division and finally we have addition and subtraction in this tutorial we're going to talk about casting and type conversion so I'm gonna declare a short variable call X and set it to 1 and then I'm gonna declare an integer called Y and set it to X plus 2 in this example we're adding a short to an integer what do you think the result is gonna be well let's take a look so sou t let's print Y we get 3 that is what you were expecting but let me explain what happens under the hood for this expression to get executed because we're dealing with two different types of values one is a short the other is an integer one of these values should be converted to the other type so they are equal now I got a question for you how many bytes do we have in a short variable we have 2 bytes 
```

Relationships: [{"target_id": "FRM_0015", "relation": "RELATED_BUT_DISTINCT", "rationale": "Different subjects, operations, values, or instructional roles: 10 + 3 * 2 = 16 | (10 + 3) * 2 = 26 Retain both; similarity is not equivalence.", "claim": "(10 + 3) * 2 = 26"}, {"target_id": "FRM_0015", "relation": "RELATED_BUT_DISTINCT", "rationale": "Different subjects, operations, values, or instructional roles: 10 + 3 * 2 = 16 | (10 + 3) * 2 = 26 Retain both; similarity is not equivalence.", "claim": "(10 + 3) * 2 = 26"}]

Mechanical results: [{"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}, {"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 22. EXP_0127:/content, EXP_0127:/explanation_text

Packet: `PKT_0b82d3d358a03acceb50a46d323978c6aea0ad0853ae8cc6fc337dbb01ddaa39`

Selected because: Check the explanation of the earlier conditional branch error.

Current historical statuses: EXP_0127:/content = SUPPORTED, EXP_0127:/explanation_text = SUPPORTED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
When the first condition checks only divisibility by 5 and is placed before the combined check for 5 and 3, a number like 15 satisfies the first condition, so 'fizz' is printed and the later else‑if branches are skipped.
```

Primary sources: T0041. Context sources: none.

Instructional role: explanation_of_mistake.

### Canonical quote — T0041

```text
here all right here we enter five we get fizz utiful what if you enter ten ten is also divisible by 5 so we get fits so far so good what about a number that is divisible by 3 we get buzz good what if we enter a number that is divisible by both 5 & 3 like 15 we get physican why is that here's the reason with this implementation if we enter 15 this first condition will evaluate to true so we get fizz these other else clauses will be ignored and that is
```

### Canonical quote — T0041

```text
one so as you can see with sweet statements we can execute different code depending on the value of an expression all right now it's time for an exercise this exercise I'm gonna give you is a popular interview question so I want you to write a program that behaves like this here we should enter a number if this number is divisible by five we get this so if you run the program again and enter ten once again we get fit now if this number is divisible by 3 we get buzz if this number is divisible by both five and three like fifteen or thirty or whatever we get fizzbuzz and if this number is not divisible by five or three like two we get the same number printed on the terminal so go ahead and spend five to ten minutes on this exercise you'll see my solution next all right to read the number first we need to use the scanner object so scanner we import this and instantiate it and as you know here we need to pass system that in to read data from the terminal now we print a message so we're gonna use the print method instead of print line here we add a label like number and then we call scanner the next int to read a number we store it in this variable number okay so the first part is done now we need to check to see if this number is divisible by five or not so we can write an if statement like this if number here we use the modulus operator which returns the remainder of a division so we divide this by five and if the remainder equals zero that means this number is divisible by 5 so we print fizz now otherwise if this number is divisible by 3 we print buzz we need another condition if this number is divisible by 5 and 3 so here we use the and operator number divisible by 3 equals 0 in this case we want to print fizz buzz otherwise you want to print the same number like this now this is not the right solution as I will show you in a second this program has a book but it's a very common solution that I see amongst my students so let's run this program and see what is wrong here all right here we enter five we get fizz utiful what if you enter ten ten is also divisible by 5 so we get fits so far so good what about a number that is divisible by 3 we get buzz good what if we enter a number that is divisible by both 5 & 3 like 15 we get physican why is that here's the reason with this implementation if we enter 15 this first condition will evaluate to true so we get fizz these other else clauses will be ignored and that is
```

### Neighbor context — not newly authorized evidence

T0040 · canonical characters 1619–2519 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
matically jump out of this block in contrast if we didn't use this break statement here Java will continue executing these other lines here so if the role is admin first it will execute this line and then it will jump to this case block it will execute this other line and then after it executes this break statement it will jump out of this switch block okay so this is how we use a switch statement now compare this with wave statement some people prefer to use if statements others prefer to use a switch statement now one more thing before we finish this tutorial here we're comparing the value of role with strings but we could also use integers other than the long type so if roll was a byte short or an integer our cases would look like this case one case two and so on now here we have a compilation error because roll is a string let's change this to an integer and we can initialize this to
```

T0042 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
why this line will not be executed so in situations like this you should have the most specific conditions on the top and the most generic ones on the bottom in this case we want to move this condition to the top so if the number is divisible by 5 & 3 we're gonna print fizzbuzz so this is very specific otherwise if the number is only divisible by 5 we print fizz else if it's divisible by 3 we print buzz and finally if none of his conditions is true then we print the same number now let's run the program one more time so we enter 15 and we get fizzbuzz beautiful so here's one way to solve this problem now I've seen some people argue that we have repeated this expression twice number is divisible by 5 we have that here on line 12 as well as line 14 in programming we have this concept called dry which is short for don't repeat yourself so some people argue that here we have repeated this ex
```

Relationships: []

Mechanical results: [{"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}, {"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 23. FRM_0015:/content, FRM_0015:/formula_text

Packet: `PKT_80a31a201671644db29c0367e4a33e4a5925679d6699c2a2d76b3b36b3bf0389`

Selected because: Contrasting parenthesized arithmetic; do not conflate results.

Current historical statuses: FRM_0015:/content = SUPPORTED, FRM_0015:/formula_text = SUPPORTED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
(10 + 3) * 2 = 26
```

Primary sources: T0023. Context sources: none.

### Canonical quote — T0023

```text
the same result take a look too however if we use this on the right side of an assignment operator we get different results let me show you so I'm gonna declare another variable Y we set it to X plus plus in this case because we have applied the increment operator as a postfix first the value of x will get copied to Y so Y would be 1 and then X will be incremented by 1 so if you print x and y x is gonna be 2 and Y is gonna be 1 take a look so X is 2 and Y is 1 beautiful however if you apply this as a prefix first X will be incremented by 1 so it will be 2 and then it will be copied to Y so in this case both X&Y will be to take a look so we get two and two now what if you want to increment X by more than one let's say by two well there are two ways to do this let's remove Y we don't really need it anymore we can write x equals x plus 2 so first we add 2 to X the result will be three and then three will be copied into X the other way is to use the Augmented or compound assignment operator so we can write X plus equals two what we have on line eight is exactly identical to what we have on line seven well as you can see it's shorter so this is a better way to write the same code now this is one of the Augmented assignment operators we have the Augmented assignment operator for other arithmetic operators so we can type X minus equals 2 and this would reduce the value of x by 2 we also have multiply and divide so these are the Augmented or compound assignment operators right now I've got a question for you here we have declared this variable X it goes to 10 plus 3 times 2 what do you think is the result of this expression the result is 16 let's run this program and find out so run there you go we got 16 but why well this is a very basic math concept that unfortunately a lot of people don't know in math the multiplication and division operators have a higher priority so they get applied first in this example this expression 3 times 2 is evaluated first the result is 6 and then 6 is added to 10 that's why we get 16 now if you want to change the order of these operators you can always use parentheses for example if you want this expression to be evaluated first we wrap it in parentheses so like this now Java compiler will first evaluate this expression the result will be 13 and then 13 is multiplied by 2 so we get 26 take a look there you go so
```

### Neighbor context — not newly authorized evidence

T0022 · canonical characters 1666–2566 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
are casting or converting this number to a double similarly we should do that here and now we have a compilation error because on the left side we declared an integer but here the result of this expression is a double and by the way an expression is a piece of code that produces a value so what we have here is an expression because it produces a value so to fix this problem we need to change this to double now when we run this program we get this floating point number beautiful so these are the arithmetic operators and these numbers that we have here are called operands we also have increment and decrement operators let me show you so I'm gonna declare a new variable int X we set it to 1 now if you want to increase the value of x by 1 we use the increment operator now let's print this on a terminal so we get 2 there you go we can apply this operator as a postfix or as a prefix and we get
```

T0024 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
be aware of the order of these operations parentheses always have the highest priority then we have multiplication and division and finally we have addition and subtraction in this tutorial we're going to talk about casting and type conversion so I'm gonna declare a short variable call X and set it to 1 and then I'm gonna declare an integer called Y and set it to X plus 2 in this example we're adding a short to an integer what do you think the result is gonna be well let's take a look so sou t let's print Y we get 3 that is what you were expecting but let me explain what happens under the hood for this expression to get executed because we're dealing with two different types of values one is a short the other is an integer one of these values should be converted to the other type so they are equal now I got a question for you how many bytes do we have in a short variable we have 2 bytes 
```

Relationships: [{"target_id": "FRM_0014", "relation": "RELATED_BUT_DISTINCT", "rationale": "Different subjects, operations, values, or instructional roles: 10 + 3 * 2 = 16 | (10 + 3) * 2 = 26 Retain both; similarity is not equivalence.", "claim": "10 + 3 * 2 = 16"}, {"target_id": "FRM_0014", "relation": "RELATED_BUT_DISTINCT", "rationale": "Different subjects, operations, values, or instructional roles: 10 + 3 * 2 = 16 | (10 + 3) * 2 = 26 Retain both; similarity is not equivalence.", "claim": "10 + 3 * 2 = 16"}]

Mechanical results: [{"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}, {"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 24. FCT_5005:/content, FCT_5005:/fact_text

Packet: `PKT_538531e50c9cffd3c23f78e1e94bc9611d10b69de95748a3e7306a46a0101812`

Selected because: Recovered package convention with no-registration qualification.

Current historical statuses: FCT_5005:/content = SUPPORTED, FCT_5005:/fact_text = SUPPORTED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
The source describes a convention of reversing the company domain name for a base package. It explicitly says an actual registered Internet domain is not required; the purpose is a namespace for classes.
```

Primary sources: T0004. Context sources: none.

### Canonical quote — T0004

```text
now by convention the base package for a Java project is the domain name of your company in Reverse so my website is code with mass comm that is why I'm gonna set the base package for this project to come that code with Marsh now it doesn't mean that you should have an actual domain registered on an Internet this is just a way to create a namespace for our classes
```

### Neighbor context — not newly authorized evidence

T0003 · canonical characters 1737–2637 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
uld have an access modifier an access modifier is a special keyword that determines if other classes and methods in this program can access these classes and methods we have various access modifiers like public private and so on now most of the time we use the public access modifier so we put that in front of our class and Method declarations so this is the basic structure of a Java program at a minimum we have a main class and inside this main class we have the main method now you might be curious why we have a capital m in the name of this class because in Java we use different conventions for naming our classes and our methods to name our classes we use the Pascal naming convention and that basically means the first letter of every word should be uppercase in contrast to name our methods we use the camel naming convention and that means the first letter of every word should be operate
```

T0005 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
become that your name or whatever it doesn't really matter all right now let's go forward alright here's our first Java project now this code editor might look a little bit intimidating at first but trust me it's really easy and you're gonna learn about it throughout this course on the left side we have the project panel where we can see all the folders and files in a project for example on the top we have the hello word project inside this project we have the source folder where we have the source code of a project now in this folder we have another folder that is calm that code with Marsh that is the name of our base package and in this package we have this class main so you can see this main file opened on the right side here now look at the name of this file its main the Java so all Java files should have the Java extension okay now let's collapse the project panel by clicking on thi
```

Relationships: []

Mechanical results: [{"original_item_result": null, "original_validation_scope": "not recorded", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}, {"original_item_result": null, "original_validation_scope": "not recorded", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 25. EXM_0003:/content, EXM_0003:/example_text

Packet: `PKT_eb8968db9f232001cafe00a086856b04f2b8eae2664e67c471c220ee6bc2d110`

Selected because: Known reconstructed code with preserved adverse disposition.

Current historical statuses: EXM_0003:/content = UNSUPPORTED, EXM_0003:/example_text = UNSUPPORTED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
String path = "C:\\Windows\\"; // prints C:\Windows\
```

Primary sources: T0018. Context sources: none.

**Warning: existing adverse disposition. Preserve the distinction between source fidelity and technical correctness.**

### Canonical quote — T0018

```text
get removed take a look so here's the original string you can see two white spaces at the beginning and here's our string after trimming so these are some useful methods in the string class but this glass has more methods than we don't have time to cover in this lecture but as we go through the course you're gonna learn more about the string class and other useful classes in Java third times will include special characters in our strings like a tab or a new line or a backslash or double quotes so in this tutorial I'm gonna show you how to include these special characters in your strings so here we have the string hello Marsh let's say we want to surround Marsh with double quotes now here's the problem if we add a double quote here Java compiler thinks this is the termination of our string so it doesn't stand what we have after that's why we have a compilation error the fixes problem we need to prefix this double code with a backslash so using this backslash we have escaped the double quote now one more time let's add backslash double code here now let's run the program and see what we get so we get hello Marsh in double quote beautiful so double quote is one of those special characters that you need to be aware of another special character is backslash let's say we want to store the pass to a directory on a Windows machine so that will look like this C Drive backslash windows backslash whatever now if you want to store this in a string we need to escape each backslash let me show you so C Drive backslash now we have a problem Java compiler thinks we're escaping the double code here so it thinks our string is not terminated with another double code but that's not what we want you want to add a backslash here so we need to prefix our backslash with another backslash now we type windows one more time something let's run the program so even though we have two backslashes in our code we actually see one backslash in a terminal window in other escape sequences backslash N and we use that to add a new line to our strings so let's change this to backslash N and run the program to see what happens now our string is broken down onto multiple lines by the first line we have C Drive then we have Windows so wherever we had a backslash n Java will insert a new line we can also add a tab in our strings so if you add backslash T here there will be a tab which means C Drive and windows let's take a look so C Drive here we have a tab and then windows now in Java we have a few more escape sequences but quite honestly they're hardly used so remember these four escape sequences
```

### Neighbor context — not newly authorized evidence

T0017 · canonical characters 1755–2655 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
l string right after SRU T tab message you can see the original string is not changed because in Java strings are immutable we cannot mutate them we cannot change them so any methods that modify a string will always return a new string object okay we also have another useful method to lowercase let's take a look so to lowercase converts all characters to lowercase and once again you can see that the original string is not affected because this method returns a new string okay we also have two uppercase and another useful method is trim trim and with this we can get rid of extra white spaces that can be at the beginning or the end of a string sometimes our users type unnecessary spaces in form fields so using the trim method we can get rid of these white spaces let me show you so I'm gonna add a couple of spaces before and after our message now when we trim it these white spaces are gonna
```

T0019 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
that we cover in this tutorial in this tutorial we're going to talk about arrays in Java we use arrays to store a list of items like a list of numbers or a list of people or a list of messages let me show you so here we have an integer variable you want to convert this to an integer array so right after int we add square brackets now we have a compilation error because we're storing a single number in this array so to fix this we need to remove one because arrays are reference types we need to use the new operator here then we repeat the type one more time enter a and here in square brackets we specify the size or the length of this array how many items do we want to include in this array let's say five also we should change the name of this variable from number two numbers because we're dealing with a list of items so always pay attention to the name of your variables now you can access
```

Relationships: [{"target_id": "EXM_0145", "relation": "RELATED_BUT_DISTINCT", "rationale": "Different subjects, operations, values, or instructional roles: String s = \"\\\"Hello Marsh\\\"\"; // prints \"Hello Marsh\" | String path = \"C:\\\\Windows\\\\\"; // prints C:\\Windows\\ Retain both; similarity is not equivalence.", "claim": "String s = \"\\\"Hello Marsh\\\"\"; // prints \"Hello Marsh\""}, {"target_id": "EXM_0004", "relation": "RELATED_BUT_DISTINCT", "rationale": "Different subjects, operations, values, or instructional roles: String path = \"C:\\\\Windows\\\\\"; // prints C:\\Windows\\ | String multiLine = \"C Drive\\nWindows\"; // prints C Drive on first line, Windows on second line Retain both; similarity is not equivalence.", "claim": "String multiLine = \"C Drive\\nWindows\"; // prints C Drive on first line, Windows on second line"}, {"target_id": "EXM_0146", "relation": "RELATED_BUT_DISTINCT", "rationale": "Different subjects, operations, values, or instructional roles: String path = \"C:\\\\Windows\\\\\"; // prints C:\\Windows\\ | String tabbed = \"C Drive\\tWindows\"; // prints C Drive    Windows (with a tab space) Retain both; similarity is not equivalence.", "claim": "String tabbed = \"C Drive\\tWindows\"; // prints C Drive    Windows (with a tab space)"}, {"target_id": "EXM_0145", "relation": "RELATED_BUT_DISTINCT", "rationale": "Different subjects, operations, values, or instructional roles: String s = \"\\\"Hello Marsh\\\"\"; // prints \"Hello Marsh\" | String path = \"C:\\\\Windows\\\\\"; // prints C:\\Windows\\ Retain both; similarity is not equivalence.", "claim": "String s = \"\\\"Hello Marsh\\\"\"; // prints \"Hello Marsh\""}, {"target_id": "EXM_0004", "relation": "RELATED_BUT_DISTINCT", "rationale": "Different subjects, operations, values, or instructional roles: String path = \"C:\\\\Windows\\\\\"; // prints C:\\Windows\\ | String multiLine = \"C Drive\\nWindows\"; // prints C Drive on first line, Windows on second line Retain both; similarity is not equivalence.", "claim": "String multiLine = \"C Drive\\nWindows\"; // prints C Drive on first line, Windows on second line"}, {"target_id": "EXM_0146", "relation": "RELATED_BUT_DISTINCT", "rationale": "Different subjects, operations, values, or instructional roles: String path = \"C:\\\\Windows\\\\\"; // prints C:\\Windows\\ | String tabbed = \"C Drive\\tWindows\"; // prints C Drive    Windows (with a tab space) Retain both; similarity is not equivalence.", "claim": "String tabbed = \"C Drive\\tWindows\"; // prints C Drive    Windows (with a tab space)"}]

Mechanical results: [{"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}, {"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 26. FCT_0252:/content, FCT_0252:/fact_text

Packet: `PKT_09211f6a0d96cf6ff2af528dfd1c4b1a62a4894211d70c62ed38c5a8393f2795`

Selected because: Transcript factual assertion still inconclusive; quote matching is insufficient.

Current historical statuses: FCT_0252:/content = INCONCLUSIVE, FCT_0252:/fact_text = INCONCLUSIVE.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
In a String array, elements default to an empty string.
```

Primary sources: T0020. Context sources: none.

### Canonical quote — T0020

```text
if you have a string array all items get initialized to an empty string
```

### Neighbor context — not newly authorized evidence

T0019 · canonical characters 1645–2545 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
fault when we print an array Java returns the string which is calculated based on the address of this object in memory so if you have another array and we print that we're gonna see something different because each object is gonna be in a different memory space okay now how can we see the actual items in this array well we have a class in Java called arrays let me show you arrays so this class is defined in Java that util package let's press ENTER now this is important on the top beautiful so we can use the dot operator to access the members of this class here we have a method called two string now as you see it this method is implemented multiple times so in the first implementation this method gets a float array in the second implementation it takes an integer array and so on so for all primitive types as well as reference types this method is implemented multiple times this is what we
```

T0021 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
this to a two-dimensional array we need to add another pair of square brackets now we have a compilation error because we need to repeat these brackets on the other side so let's say we want to create a 2 by 3 matrix so 2 rows and 3 columns we add in other brackets here and change these lengths to 2 and 3 so now we have 2 rows and 3 columns now to access individual items in this array we need to supply two indexes first the index of the row so we can go to the first row and then the first column and initialize that to 1 now let us print this so and so you t-tap once again we use our arrays class dot to string and pass this object take a look once again we get this weird string because here we're dealing with a multi-dimensional array to solve this problem we need to use another method in this class called deep to string use this for printing multi-dimensional arrays take a look now we ha
```

Relationships: [{"target_id": "FCT_0251", "relation": "RELATED_BUT_DISTINCT", "rationale": "Different subjects, operations, values, or instructional roles: In a boolean array, elements default to false. | In a String array, elements default to an empty string. Retain both; similarity is not equivalence.", "claim": "In a boolean array, elements default to false."}, {"target_id": "FCT_0251", "relation": "RELATED_BUT_DISTINCT", "rationale": "Different subjects, operations, values, or instructional roles: In a boolean array, elements default to false. | In a String array, elements default to an empty string. Retain both; similarity is not equivalence.", "claim": "In a boolean array, elements default to false."}]

Mechanical results: [{"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}, {"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 27. FCT_0361:/content, FCT_0361:/fact_text

Packet: `PKT_4969ed47d60171811199dd22034fd8879032c6e9fc8fb87cebd71ee5288c7c13`

Selected because: Counting example must not become a universal counter requirement.

Current historical statuses: FCT_0361:/content = SUPPORTED, FCT_0361:/fact_text = SUPPORTED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
The source first demonstrates a counter-based while loop, then an input-driven while loop with no counter variable. The input loop checks whether the user has entered quit.
```

Primary sources: T0044. Context sources: none.

### Canonical quote — T0044

```text
one two three four five in contrast if we initialize I to zero and use the less than operator we will get hello word zero one two three four we can also print these numbers in reverse order so we initialize I to five and execute this loop as long as I is greater than zero but here instead of incrementing I we decrement it now we get hello world five four three two one so this is all about for loops next we're gonna look at while loops in this tutorial we're gonna talk about while loops in Java while loops are very similar to for loops in terms of their functionality but they're different in terms of syntax let me show you so we're gonna continue with the example from the last tutorial I'm gonna rewrite this code using a while loop so first we declare a loop variable and I initialize it to zero next we type while and here in parentheses we type our loop condition while I is greater than zero then we're gonna execute the code inside this block so I'm gonna copy this from here paste it in this block and finally we need to decrement I like this so at the end of each iteration we decrement I just like our for loops so as you can see we can achieve the same thing using a for loop or a while loop however the implementation using the for loop is a little bit lighter and cleaner so in situations where you know ahead of time how many times you want to execute one or more statements it's better to use a for loop while loops are better in situations where we don't know exactly how many times you want to repeat something for example let's say we're going to write a program and ask the user to continuously enter something until they type quit the moment they type quit we're gonna terminate the program in that situation we don't know how many times the user is going to enter something so let's write that program using a while loop I'm gonna delete everything from here all right we're gonna start with our while loop now what is our loop condition here we don't have a counter variable in this example instead we want to check to see if the user entered quit or not so here we can declare a string called input and initialize it to an empty string then we can write a while loop like this while input does not equal to quit now this code is not gonna work because input is a string which is a reference type and we cannot use comparison operators between reference types because these operators will compare the address or a string objects not their value so if you have two strings quit and quit but stored in different memory locations to have different addresses so we can use the inequality operator
```

### Neighbor context — not newly authorized evidence

T0043 · canonical characters 1644–2544 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
ted now at the end of this iteration or at the end of this loop the control moves here so I is incremented by one now we are at the beginning of the second iteration once again this condition is evaluated is one less than five obviously it is so once again the body of this loop gets executed now fast forward at the end of the fifth iteration I will become five five is not less than five so the loop condition will be false and control moves outside of this for loop now here's one thing you need to remember if you want to execute something five times you can initialize your loop counter or loop variable to zero and use the less than operator here another way is to initialize this to one and then use the less than or equal to operator here now to make this more interesting let's print I over here so here we add a space and then concatenate this string with I take a look so we get hello ward
```

T0045 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
to compare their value instead we need to use the equals method of string objects so we want to check to see if the input equals quit now here we need to apply the not operator so as long as the input does not equal quit we're gonna continuously ask the user to enter something so here we can print a label like input and then we can use a scanner object to read something from the terminal so let's create a scanner object and instantiate it using system dot in I didn't call scanner that next this will return a string so we can store it in this input variable now with this implementation in every iteration we're going to create a new scanner object so if the user enters 10 numbers we're gonna create 10 scanner objects in memory this is unnecessary and it's actually a bad practice because it's going to pollute our memory so it's better to create the scanner object outside of a while loop and
```

Relationships: []

Mechanical results: [{"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}, {"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 28. DEF_0060:/content, DEF_0060:/definition_text

Packet: `PKT_1387f7e3790020c3951be91ef67ed68d2cdc8750e924f0b78233a68cac4d7a01`

Selected because: Universal new-object claim remains only partially supported.

Current historical statuses: DEF_0060:/content = PARTIALLY_SUPPORTED, DEF_0060:/definition_text = PARTIALLY_SUPPORTED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
a string that cannot be changed after it is created; any method that appears to modify a string actually returns a new string object
```

Primary sources: T0017. Context sources: none.

### Canonical quote — T0017

```text
asterisk are arguments now let's run this program and see what happens so our explanation marks are replaced with stars now what is important here is that this method does not modify our original string it returns a new string so if we print our original string right after SRU T tab message you can see the original string is not changed because in Java strings are immutable we cannot mutate them we cannot change them so any methods that modify a string will always return a new string object okay
```

### Neighbor context — not newly authorized evidence

T0016 · canonical characters 1765–2665 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
ods or functions do find in the string class for example we have this method here ends with and with this we can check to see if our string ends with a character or sequence of characters for example here we can pass their string to see if our message ends with two exclamation marks now instead of printing the message let's print this expression here so let's run the program we get true so this method that we have called here returns a boolean value which can be true or false we also have another method starts with let's take a look now in this case we get false because our message doesn't start with two exclamation marks another useful method is length so we can call that to get the length of a string which is the number of characters so message dot length take a look so in this string we have 13 characters and this is useful in situations where you want to check the length of the input
```

T0018 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
get removed take a look so here's the original string you can see two white spaces at the beginning and here's our string after trimming so these are some useful methods in the string class but this glass has more methods than we don't have time to cover in this lecture but as we go through the course you're gonna learn more about the string class and other useful classes in Java third times will include special characters in our strings like a tab or a new line or a backslash or double quotes so in this tutorial I'm gonna show you how to include these special characters in your strings so here we have the string hello Marsh let's say we want to surround Marsh with double quotes now here's the problem if we add a double quote here Java compiler thinks this is the termination of our string so it doesn't stand what we have after that's why we have a compilation error the fixes problem we n
```

Relationships: []

Mechanical results: [{"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}, {"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 29. PRC_5001:/steps/3

Packet: `PKT_c2180c9aa06ed6bd19cdfbc50286239e2f2ca70fda16abc1a89d3b8245748530`

Selected because: Additional Task 8 source-backed construction sequence.

Current historical statuses: PRC_5001:/steps/3 = SUPPORTED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
Terminate the do-while statement with a semicolon.
```

Primary sources: T0045. Context sources: none.

Instructional role: continuation.

### Canonical quote — T0045

```text
we start with a do keyword then we create a code block at the end of this code block we type while followed by our loop condition so not input dot equals quit and then we terminate this using a semicolon now inside the body of this loop we'll simply copy all these lines we have here
```

### Neighbor context — not newly authorized evidence

T0044 · canonical characters 1720–2620 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
that situation we don't know how many times the user is going to enter something so let's write that program using a while loop I'm gonna delete everything from here all right we're gonna start with our while loop now what is our loop condition here we don't have a counter variable in this example instead we want to check to see if the user entered quit or not so here we can declare a string called input and initialize it to an empty string then we can write a while loop like this while input does not equal to quit now this code is not gonna work because input is a string which is a reference type and we cannot use comparison operators between reference types because these operators will compare the address or a string objects not their value so if you have two strings quit and quit but stored in different memory locations to have different addresses so we can use the inequality operator
```

T0046 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
cases for that so just be aware of them but most of the time prefer to use wire loops we're gonna continue with the example from the last tutorial this program we have written has a tiny problem let me show you so I'm gonna run this enter a couple numbers these numbers get echo back beautiful if we type quit the program terminates but the word quit also gets echoed back this is a bit weird so let's look at a couple ideas for solving this problem back to our code one way to solve this problem is to check the input before printing it so here we can type an if statement if the input does not equal quit then we're print it so not equal input dot equals quit if this condition is true then we're going to print the input let's take a look so one to quit beautiful we solved the problem there is another way to solve this problem as well let me show you we can reverse this condition so if the user
```

Relationships: []

Mechanical results: [{"original_item_result": null, "original_validation_scope": "not recorded", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.

## 30. PRC_0397:/steps/3

Packet: `PKT_f907559cba8eb3b8da22f3b8b81b84a36837a7a2f48e8f0821ae436cfca75e70`

Selected because: Check the combined-condition correction and explicit T0042 support.

Current historical statuses: PRC_0397:/steps/3 = SUPPORTED.

Independent pilot judgment: **PENDING**.

Exact generated claim / unsplit field bundle:
```text
Check if number % 5 == 0 and number % 3 == 0; if true, print "fizzbuzz".
```

Primary sources: T0041. Context sources: T0029, T0042.

Instructional role: corrected_approach.

### Canonical quote — T0041

```text
one so as you can see with sweet statements we can execute different code depending on the value of an expression all right now it's time for an exercise this exercise I'm gonna give you is a popular interview question so I want you to write a program that behaves like this here we should enter a number if this number is divisible by five we get this so if you run the program again and enter ten once again we get fit now if this number is divisible by 3 we get buzz if this number is divisible by both five and three like fifteen or thirty or whatever we get fizzbuzz and if this number is not divisible by five or three like two we get the same number printed on the terminal so go ahead and spend five to ten minutes on this exercise you'll see my solution next all right to read the number first we need to use the scanner object so scanner we import this and instantiate it and as you know here we need to pass system that in to read data from the terminal now we print a message so we're gonna use the print method instead of print line here we add a label like number and then we call scanner the next int to read a number we store it in this variable number okay so the first part is done now we need to check to see if this number is divisible by five or not so we can write an if statement like this if number here we use the modulus operator which returns the remainder of a division so we divide this by five and if the remainder equals zero that means this number is divisible by 5 so we print fizz now otherwise if this number is divisible by 3 we print buzz we need another condition if this number is divisible by 5 and 3 so here we use the and operator number divisible by 3 equals 0 in this case we want to print fizz buzz otherwise you want to print the same number like this now this is not the right solution as I will show you in a second this program has a book but it's a very common solution that I see amongst my students so let's run this program and see what is wrong here all right here we enter five we get fizz utiful what if you enter ten ten is also divisible by 5 so we get fits so far so good what about a number that is divisible by 3 we get buzz good what if we enter a number that is divisible by both 5 & 3 like 15 we get physican why is that here's the reason with this implementation if we enter 15 this first condition will evaluate to true so we get fizz these other else clauses will be ignored and that is
```

### Canonical quote — T0042

```text
why this line will not be executed so in situations like this you should have the most specific conditions on the top and the most generic ones on the bottom in this case we want to move this condition to the top so if the number is divisible by 5 & 3 we're gonna print fizzbuzz so this is very specific otherwise if the number is only divisible by 5 we print fizz else if it's divisible by 3 we print buzz and finally if none of his conditions is true then we print the same number now let's run the program one more time so we enter 15 and we get fizzbuzz beautiful so here's one way to solve this problem now I've seen some people argue that we have repeated this expression twice number is divisible by 5 we have that here on line 12 as well as line 14 in programming we have this concept called dry which is short for don't repeat yourself so some people argue that here we have repeated this expression and this is not a good solution here is another way let me show you so we're gonna get rid of this second condition here instead we're gonna add a code block over here so if the number is divisible by 5 first we check to see if the number is also divisible by 3 if that's the case we print fizzbuzz otherwise we print just fizz like this okay now we no longer need these two lines because we already implemented this concept here so first we check to see if the number is divisible by five if not we check to see if it's divisible by three and otherwise so here is another way to solve this problem but in my opinion this approach is kind of amateurish and ugly because these nested if-else statements are considered a bad practice now this is not terribly bad but the more you nest these L statements the more confusing your code is going to be to other people so I personally prefer the previous solution even though we had a bit of repetition in the code the more you program the more you build software the more you realize that there is no way to build ideal software programming and problem solving is all about trade-offs every solution has certain strengths and certain weaknesses this solution doesn't have any repetition or duplication in the code but it has a nested structure and these nested structures make our code hard to read and understand the previous solution had a bit of repetition but it had a flat structure there is no nesting here and this code is cleaner and easier to read there are times that we want to repeat one or more statements for example let's say we have this hello world message here let's say we want to print this five times on the terminal we don't want to repeat this
```

### Neighbor context — not newly authorized evidence

T0040 · canonical characters 1619–2519 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
matically jump out of this block in contrast if we didn't use this break statement here Java will continue executing these other lines here so if the role is admin first it will execute this line and then it will jump to this case block it will execute this other line and then after it executes this break statement it will jump out of this switch block okay so this is how we use a switch statement now compare this with wave statement some people prefer to use if statements others prefer to use a switch statement now one more thing before we finish this tutorial here we're comparing the value of role with strings but we could also use integers other than the long type so if roll was a byte short or an integer our cases would look like this case one case two and so on now here we have a compilation error because roll is a string let's change this to an integer and we can initialize this to
```

T0042 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
why this line will not be executed so in situations like this you should have the most specific conditions on the top and the most generic ones on the bottom in this case we want to move this condition to the top so if the number is divisible by 5 & 3 we're gonna print fizzbuzz so this is very specific otherwise if the number is only divisible by 5 we print fizz else if it's divisible by 3 we print buzz and finally if none of his conditions is true then we print the same number now let's run the program one more time so we enter 15 and we get fizzbuzz beautiful so here's one way to solve this problem now I've seen some people argue that we have repeated this expression twice number is divisible by 5 we have that here on line 12 as well as line 14 in programming we have this concept called dry which is short for don't repeat yourself so some people argue that here we have repeated this ex
```

T0041 · canonical characters 1553–2453 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
ble by 3 we print buzz we need another condition if this number is divisible by 5 and 3 so here we use the and operator number divisible by 3 equals 0 in this case we want to print fizz buzz otherwise you want to print the same number like this now this is not the right solution as I will show you in a second this program has a book but it's a very common solution that I see amongst my students so let's run this program and see what is wrong here all right here we enter five we get fizz utiful what if you enter ten ten is also divisible by 5 so we get fits so far so good what about a number that is divisible by 3 we get buzz good what if we enter a number that is divisible by both 5 & 3 like 15 we get physican why is that here's the reason with this implementation if we enter 15 this first condition will evaluate to true so we get fizz these other else clauses will be ignored and that is
```

T0043 · canonical characters 0–900 · NOT_AUTHORIZED_BY_THIS_PACKET
```text
code like this this looks very ugly that's where we use loops in Java we have a few different types of loops the first one that I'm going to talk about in this tutorial is for loops so let's see how we can use a for loop here I'm going to delete all this code you start by typing the for keyword followed by parentheses and inside these parentheses we need to do three things first we need to declare a loop or counter variable so let's declare a variable called I and initialize it to 0 quit often use variable names like I J and K for loop counters next we add a semicolon to terminate the first statement then we write a boolean expression that determines how many times this loop is gonna get executed so I than five as long as I is less than five this loop will be executed once again we add a semicolon and finally we increment I by one like this so this is the basic structure for a for loop n
```

Relationships: []

Mechanical results: [{"original_item_result": true, "original_validation_scope": "exact quotation, chunk membership and field coverage only", "original_field_evidence_valid": true, "active_field_evidence_valid": true, "semantic_entailment_proven": false}]

Review controls: SUPPORTED / PARTIALLY_SUPPORTED / UNSUPPORTED / CONTRADICTED / INCONCLUSIVE. Record identity, rationale, evidence scope and this exact version.
